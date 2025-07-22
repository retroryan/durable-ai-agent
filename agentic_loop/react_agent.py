"""
Clean Manual Agent Loop implementation following DSPy ReAct patterns.

This module provides a stateless agent loop that uses trajectory dictionaries
directly, following the exact patterns from dspy/predict/react.py.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Tuple, Type

import dspy
from pydantic import BaseModel, Field

from models.trajectory import Trajectory
from shared.tool_utils import BaseTool
from shared.tool_utils.registry import ToolRegistry

if TYPE_CHECKING:
    from dspy.signatures.signature import Signature

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

    def _format_trajectories(self, trajectories: List[Trajectory]):
        """Format trajectories for display to the LLM."""
        self.logger.debug(
            f"[ReactAgent] Formatting {len(trajectories)} trajectories"
        )

        if not trajectories:
            return "No previous steps."

        formatted_parts = []
        for traj in trajectories:
            step = f"Step {traj.iteration + 1}:\n"
            step += f"  Thought: {traj.thought}\n"
            step += f"  Tool: {traj.tool_name}\n"
            if traj.tool_args:
                step += f"  Args: {traj.tool_args}\n"
            if traj.observation:
                step += f"  Result: {traj.observation}\n"
            if traj.error:
                step += f"  Error: {traj.error}\n"
            formatted_parts.append(step)
        
        formatted = "\n".join(formatted_parts)
        self.logger.debug(
            f"[ReactAgent] Formatted trajectory length: {len(formatted)} chars"
        )

        return formatted

    def forward(
        self, trajectories: List[Trajectory], current_iteration: int, **input_args
    ) -> Trajectory:
        """
        Execute the reactive tool-calling loop.

        Args:
            trajectories: List of previous trajectory steps
            current_iteration: Current iteration number (1-based)
            **input_args: Other signature input fields (e.g., user_query)

        Returns:
            Trajectory: The trajectory for this iteration
        """
        # Calculate the current index (0-based)
        idx = current_iteration - 1

        self.logger.info(
            f"[ReactAgent] Starting forward pass - Iteration: {current_iteration}, "
            f"Query: '{input_args.get('user_query', 'N/A')}'"
        )
        self.logger.debug(f"[ReactAgent] Number of previous trajectories: {len(trajectories)}")

        try:
            self.logger.debug(f"[ReactAgent] Calling react with formatted trajectories")

            pred = self.react(
                **input_args, trajectory=self._format_trajectories(trajectories)
            )

            self.logger.info(
                f"[ReactAgent] LLM response - Thought: '{pred.next_thought}', "
                f"Tool: '{pred.next_tool_name}', Args: {pred.next_tool_args}"
            )

        except ValueError as err:
            self.logger.warning(
                f"[ReactAgent] ValueError: Agent failed to select a valid tool: {err}"
            )
            # Return error trajectory
            return Trajectory(
                iteration=idx,
                thought="Error occurred during tool selection",
                tool_name="error",
                tool_args={},
                error=str(err)
            )

        # Create and return new trajectory
        trajectory = Trajectory(
            iteration=idx,
            thought=pred.next_thought,
            tool_name=pred.next_tool_name,
            tool_args=pred.next_tool_args
        )

        self.logger.info(f"[ReactAgent] Created trajectory for iteration {idx}")
        self.logger.debug(f"[ReactAgent] Trajectory: {trajectory}")

        return trajectory
