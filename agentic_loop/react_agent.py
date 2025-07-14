"""
Clean Manual Agent Loop implementation following DSPy ReAct patterns.

This module provides a stateless agent loop that uses trajectory dictionaries
directly, following the exact patterns from dspy/predict/react.py.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Literal, Tuple, Type

import dspy
from pydantic import BaseModel, Field

from shared.tool_utils import BaseTool
from shared.tool_utils.registry import ToolRegistry

if TYPE_CHECKING:
    from dspy.signatures.signature import Signature


class ReactAgentResult(BaseModel):
    """Result from ReactAgent forward pass."""

    trajectory: Dict[str, Any] = Field(description="Agent execution trajectory")
    tool_name: str = Field(description="Name of the tool selected by the agent")
    tool_args: Dict[str, Any] = Field(description="Arguments for the tool call")


class ReactAgent(dspy.Module):
    """
    React with trajectory dictionary management following DSPy ReAct patterns.
    """

    def __init__(self, signature: Type["Signature"], tool_registry: ToolRegistry):
        """
        Initialize the ReactAgent.

        Args:
            signature: The signature defining input/output fields
            tool_registry: Registry containing tool implementations
        """
        super().__init__()
        if not tool_registry:
            raise ValueError("tool_registry is required for ReactAgent")

        # Setup logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self.tool_registry = tool_registry

        self.all_tools: Dict[str, BaseTool] = tool_registry.get_all_tools()

        # Build instruction components
        inputs = ", ".join([f"`{k}`" for k in signature.input_fields.keys()])
        outputs = ", ".join([f"`{k}`" for k in signature.output_fields.keys()])
        instr = [f"{signature.instructions}\n"] if signature.instructions else []

        instr.extend(
            [
                f"You are an Agent. In each episode, you will be given the fields {inputs} as input. And you can see your past trajectory so far.",
                f"Your goal is to use one or more of the supplied tools to collect any necessary information for producing {outputs}.\n",
                "To do this, you will interleave next_thought, next_tool_name, and next_tool_args in each turn, and also when finishing the task.",
                "After each tool call, you receive a resulting observation, which gets appended to your trajectory.\n",
                "When writing next_thought, you may reason about the current situation and plan for future steps.",
                "When selecting the next_tool_name and its next_tool_args, the tool must be one of:\n",
            ]
        )
        # Add finish tool to the tools dictionary before enumeration
        tools_with_finish = self.all_tools.copy()

        # Create a mock finish tool object for consistent formatting
        class FinishTool:
            NAME = "finish"
            description = f"Marks the task as complete. That is, signals that all information for producing the outputs, i.e. {outputs}, are now available to be extracted."

            def get_argument_details(self):
                return {}

        tools_with_finish["finish"] = FinishTool()

        # Add tool descriptions to instructions
        for idx, tool in enumerate(tools_with_finish.values()):
            # Get argument details from the tool
            arg_details = tool.get_argument_details()
            instr.append(
                f"({idx + 1}) Tool(name={tool.NAME}, desc={tool.description}, args={arg_details})"
            )

        instr.append(
            "When providing `next_tool_args`, the value inside the field must be in JSON format"
        )

        self.logger.debug("=" * 25)
        self.logger.debug(f"Using instructions: {instr}")
        self.logger.debug("=" * 25)

        # Create the react signature for tool calling
        react_signature = (
            dspy.Signature({**signature.input_fields}, "\n".join(instr))
            .append("trajectory", dspy.InputField(), type_=str)
            .append("next_thought", dspy.OutputField(), type_=str)
            .append(
                "next_tool_name",
                dspy.OutputField(),
                type_=Literal[tuple(tools_with_finish.keys())],
            )
            .append("next_tool_args", dspy.OutputField(), type_=dict[str, Any])
        )

        self.react = dspy.Predict(react_signature)

    def _format_trajectory(self, trajectory: dict[str, Any]):
        """Format trajectory for display to the LLM."""
        self.logger.debug(
            f"[ReactAgent] Formatting trajectory with keys: {list(trajectory.keys())}"
        )

        adapter = dspy.settings.adapter or dspy.ChatAdapter()
        trajectory_signature = dspy.Signature(f"{', '.join(trajectory.keys())} -> x")
        formatted = adapter.format_user_message_content(
            trajectory_signature, trajectory
        )

        self.logger.debug(
            f"[ReactAgent] Formatted trajectory length: {len(formatted)} chars"
        )

        return formatted

    def forward(
        self, trajectory: dict, current_iteration: int, **input_args
    ) -> ReactAgentResult:
        """
        Execute the reactive tool-calling loop.

        Args:
            trajectory: Dictionary containing the conversation trajectory
            current_iteration: Current iteration number (1-based)
            **input_args: Other signature input fields (e.g., user_query)

        Returns:
            ReactAgentResult: Result containing updated trajectory and tool name
        """
        # Calculate the current index (0-based for trajectory keys)
        idx = current_iteration - 1

        self.logger.info(
            f"[ReactAgent] Starting forward pass - Iteration: {current_iteration}, "
            f"Query: '{input_args.get('user_query', 'N/A')}'"
        )
        self.logger.debug(f"[ReactAgent] Current trajectory state: {trajectory}")

        try:
            self.logger.debug(f"[ReactAgent] Calling react with formatted trajectory")

            pred = self.react(
                **input_args, trajectory=self._format_trajectory(trajectory)
            )

            self.logger.info(
                f"[ReactAgent] LLM response - Thought: '{pred.next_thought}', "
                f"Tool: '{pred.next_tool_name}', Args: {pred.next_tool_args}"
            )

        except ValueError as err:
            self.logger.warning(
                f"[ReactAgent] ValueError: Agent failed to select a valid tool: {err}"
            )
            # Return trajectory with error info
            trajectory[f"error_{idx}"] = str(err)
            self.logger.debug(
                f"[ReactAgent] Returning early with error, trajectory updated with error_{idx}"
            )
            return ReactAgentResult(
                trajectory=trajectory, tool_name="finish", tool_args={}
            )

        # Store the prediction details in trajectory with proper indexing
        trajectory[f"thought_{idx}"] = pred.next_thought
        trajectory[f"tool_name_{idx}"] = pred.next_tool_name
        trajectory[f"tool_args_{idx}"] = pred.next_tool_args

        self.logger.info(f"[ReactAgent] Updated trajectory with iteration {idx} data")
        self.logger.debug(f"[ReactAgent] Final trajectory state: {trajectory}")

        return ReactAgentResult(
            trajectory=trajectory,
            tool_name=pred.next_tool_name,
            tool_args=pred.next_tool_args,
        )
