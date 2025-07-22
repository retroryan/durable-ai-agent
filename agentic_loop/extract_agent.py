"""
Extract Agent - Isolated ReAct Extract functionality
This module synthesizes the final answer from a trajectory using dspy.ChainOfThought.
"""

import logging
from typing import TYPE_CHECKING, Any, List, Type

import dspy
from dspy.primitives.module import Module
from dspy.signatures.signature import ensure_signature

from models.trajectory import Trajectory

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from dspy.signatures.signature import Signature


class ReactExtract(Module):
    """
    ReAct Extract functionality - synthesizes final answers from trajectories.
    This is the reasoning module that processes the complete trajectory to produce final outputs.
    """

    def __init__(self, signature: Type["Signature"]):
        """
        Initialize the ReactExtract module with signature.

        Args:
            signature: The signature defining input/output fields for final extraction
        """
        super().__init__()
        self.signature = signature = ensure_signature(signature)

        # Create fallback signature that includes trajectory as input
        # This allows ChainOfThought to reason over the complete interaction history
        fallback_signature = dspy.Signature(
            {**signature.input_fields, **signature.output_fields},
            signature.instructions,
        ).append("trajectory", dspy.InputField(), type_=str)

        self.extract = dspy.ChainOfThought(fallback_signature)

    def _format_trajectories(self, trajectories: List[Trajectory]):
        """Format trajectories for display to the LLM."""
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
        
        return "\n".join(formatted_parts)

    def forward(self, trajectories: List[Trajectory], **input_args):
        """
        Extract final answer from trajectories using Chain of Thought reasoning.

        Args:
            trajectories: List of trajectory steps containing the complete interaction history
            **input_args: Original input arguments from the signature

        Returns:
            dspy.Prediction with final extracted answers and reasoning
        """
        # Format trajectories for the LLM
        formatted_trajectory = self._format_trajectories(trajectories)

        # Use ChainOfThought to reason over the trajectory and extract final answer
        extract_result = self.extract(**input_args, trajectory=formatted_trajectory)

        return dspy.Prediction(
            **extract_result,
            trajectories=trajectories,
            formatted_trajectory=formatted_trajectory,
        )
