#!/usr/bin/env python3
"""
Demo script for ReactAgent with Extract Agent - runs test cases from tool sets.

This script demonstrates the ReactAgent + Extract Agent integration by running
test cases from various tool sets with nice formatting and progress tracking.
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List

import dspy
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from shared.tool_utils import AgricultureToolSet

# Add the project root to Python path so imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared" / "tool_utils"))

# Import shared utilities
from shared import ConsoleFormatter, setup_llm
from shared.llm_utils import LLMConfig, get_full_history, save_dspy_history

from shared.tool_utils.registry import create_tool_set_registry, TOOL_SET_MAP
from models.trajectory import Trajectory, summarize_trajectories
from models.types import ActivityStatus

# Initialize module-level logger
logger = logging.getLogger(__name__)


# Pydantic model for test case results
class TestCaseResult(BaseModel):
    status: str
    trajectories: List[Trajectory] = Field(default_factory=list)
    tools_used: List[str] = []
    execution_time: float = 0.0
    answer: str = ""
    reasoning: str = ""
    expected_tools: List[str] = []
    tools_match: bool = False
    error: Optional[str] = None


# Configure logging
def setup_logging(log_level: str = "INFO"):
    """Configure logging for the demo.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Reduce verbosity of some loggers unless in DEBUG mode
    if log_level.upper() != "DEBUG":
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("anthropic").setLevel(logging.WARNING)
        logging.getLogger("LiteLLM").setLevel(logging.WARNING)


def run_react_loop(
    react_agent,
    tool_registry,
    user_query: str,
    tool_set_name: str,
    max_iterations: int = 5,
) -> Tuple[List[Trajectory], float]:
    """
    Run the React agent loop until completion or max iterations.

    Args:
        react_agent: The initialized ReactAgent
        tool_registry: The tool registry for executing tools
        user_query: The user's question
        tool_set_name: Name of the tool set being used
        max_iterations: Maximum number of iterations

    Returns:
        Tuple of (list of trajectories, execution time)
    """
    trajectories: List[Trajectory] = []
    current_iteration = 1
    start_time = time.time()

    # Check if DSPY debug mode is enabled
    dspy_debug_enabled = os.getenv("DSPY_DEBUG", "false").lower() == "true"

    logger.debug("Starting ReactAgent loop")
    logger.debug(f"Query: {user_query}")

    # Loop until we get "finish" or hit max iterations
    while current_iteration <= max_iterations:
        logger.debug(f"Iteration {current_iteration}/{max_iterations}")

        # Call ReactAgent
        trajectory = react_agent(
            trajectories=trajectories,
            current_iteration=current_iteration,
            user_query=user_query,
        )
        
        # Add the new trajectory to the list
        trajectories.append(trajectory)
        # Save ReactAgent history only if DSPY debug is enabled
        if dspy_debug_enabled:
            try:
                saved_path = save_dspy_history(
                    tool_set_name=tool_set_name,
                    agent_type="react",
                    index=current_iteration,
                )
                if saved_path:
                    logger.debug(f"Saved ReactAgent history to: {saved_path}")
            except Exception as e:
                logger.warning(f"Failed to save ReactAgent history: {e}")

        logger.debug(f"Tool selected: {trajectory.tool_name}")
        logger.debug(f"Tool args: {trajectory.tool_args}")

        # Check if we're done
        if trajectory.check_is_finish():
            logger.debug("Agent selected 'finish' - task complete")
            break

        # Execute the tool if it's not finish
        if trajectory.tool_name in tool_registry.get_all_tools():
            try:
                tool = tool_registry.get_tool(trajectory.tool_name)
                logger.debug(f"Executing tool: {trajectory.tool_name}")
                
                # Ensure numeric fields are properly typed
                # This handles cases where DSPy might return numeric values as strings
                tool_args = trajectory.tool_args.copy()
                if 'latitude' in tool_args and isinstance(tool_args['latitude'], str):
                    try:
                        tool_args['latitude'] = float(tool_args['latitude'])
                    except ValueError:
                        pass  # Keep as string if conversion fails
                if 'longitude' in tool_args and isinstance(tool_args['longitude'], str):
                    try:
                        tool_args['longitude'] = float(tool_args['longitude'])
                    except ValueError:
                        pass  # Keep as string if conversion fails
                
                #save tool execution to the trajectory observation
                trajectory.observation = tool.execute(**tool_args)
                logger.debug(f"Tool result: {trajectory.observation}")
            except Exception as e:
                logger.error(f"Tool execution error: {e}", exc_info=True)
                trajectory.observation = f"Error: {e}"
        else:
            logger.warning(f"Unknown tool: {trajectory.tool_name}")
            trajectory.observation = f"Error: Unknown tool {trajectory.tool_name}"

        current_iteration += 1

    if current_iteration > max_iterations:
        logger.warning(f"Reached maximum iterations ({max_iterations})")

    execution_time = time.time() - start_time
    return trajectories, execution_time


def extract_final_answer(
    trajectories: List[Trajectory], user_query: str, tool_set_name: str
) -> Tuple[str, str]:
    """
    Extract the final answer from the trajectories using the Extract Agent.

    Args:
        trajectories: The complete list of trajectories from the React loop
        user_query: The original user query
        tool_set_name: Name of the tool set being used

    Returns:
        Tuple of (answer, reasoning)
    """
    from agentic_loop.extract_agent import ReactExtract

    # Check if DEMO debug mode is enabled
    demo_debug_enabled = os.getenv("DEMO_DEBUG", "false").lower() == "true"

    logger.debug("Extracting final answer from trajectories")
    logger.debug(f"Summary: {summarize_trajectories(trajectories)}")

    # Create a signature for answer extraction
    class AnswerExtractionSignature(dspy.Signature):
        """Extract a clear, concise answer from the gathered information."""

        user_query: str = dspy.InputField(desc="The user's original question")
        answer: str = dspy.OutputField(
            desc="Clear, direct answer to the user's question"
        )

    # Initialize Extract Agent
    extract_agent = ReactExtract(signature=AnswerExtractionSignature)

    # Extract answer from trajectories
    logger.debug("Calling Extract Agent")
    result = extract_agent(trajectories=trajectories, user_query=user_query)

    # Save ExtractAgent history only if DSPY debug is enabled
    if demo_debug_enabled:
        try:
            saved_path = save_dspy_history(
                tool_set_name=tool_set_name,
                agent_type="extract",
                index=1,  # Extract is typically called once at the end
            )
            if saved_path:
                logger.debug(f"Saved ExtractAgent history to: {saved_path}")
        except Exception as e:
            logger.warning(f"Failed to save ExtractAgent history: {e}")

    logger.debug("Successfully extracted final answer")
    return result.answer, getattr(result, "reasoning", "")


def run_single_test_case(
    test_case, tool_registry, tool_set_name: str, console: ConsoleFormatter
) -> TestCaseResult:
    """Run a single test case and return results."""
    from agentic_loop.react_agent import ReactAgent

    # Check if DSPY debug mode is enabled
    dspy_debug_enabled = os.getenv("DSPY_DEBUG", "false").lower() == "true"

    # Get tool set specific signature if available
    tool_set_signature = tool_registry.get_react_signature()

    if tool_set_signature:
        ReactSignature = tool_set_signature
    else:
        # Fallback to generic signature
        class ReactSignature(dspy.Signature):
            """Use tools to answer the user's question."""

            user_query: str = dspy.InputField(desc="The user's question")

    # Initialize ReactAgent
    react_agent = ReactAgent(signature=ReactSignature, tool_registry=tool_registry)

    # Run React loop
    logger.info(console.section_header("🔄 React Agent Execution", char="-", width=60))

    try:
        trajectories, react_time = run_react_loop(
            react_agent=react_agent,
            tool_registry=tool_registry,
            user_query=test_case.request,
            tool_set_name=tool_set_name,
            max_iterations=5,
        )

        # Extract tools used
        tools_used = []
        for traj in trajectories:
            if not traj.is_finish:
                tools_used.append(traj.tool_name)

        logger.info(f"✓ React loop completed in {react_time:.2f}s")
        logger.info(
            f"  Iterations: {len(trajectories)}"
        )
        logger.info(f"  Tools used: {', '.join(tools_used) if tools_used else 'None'}")

        # Extract final answer
        logger.info(
            f"\n{console.section_header('📝 Extract Agent', char='-', width=60)}"
        )
        answer, reasoning = extract_final_answer(
            trajectories, test_case.request, tool_set_name
        )

        logger.info("✓ Answer extracted successfully")

        return TestCaseResult(
            status=ActivityStatus.SUCCESS,
            trajectories=trajectories,
            tools_used=tools_used,
            execution_time=react_time,
            answer=answer,
            reasoning=reasoning,
            expected_tools=test_case.expected_tools,
            tools_match=set(tools_used) == set(test_case.expected_tools),
        )

    except Exception as e:
        logger.error(f"Test case failed: {e}", exc_info=True)
        return TestCaseResult(
            status=ActivityStatus.ERROR,
            error=str(e),
            execution_time=0,
            tools_used=[],
            expected_tools=test_case.expected_tools,
            tools_match=False,
        )


def run_test_cases(tool_set_name: str, test_case_index: Optional[int] = None):
    """Run test cases for a tool set."""
    console = ConsoleFormatter()
    
    # Load environment variables from agentic_loop/.env
    local_env = Path(__file__).parent / ".env"
    load_dotenv(local_env)

    # Check if DSPY debug mode is enabled
    dspy_debug_enabled = os.getenv("DSPY_DEBUG", "false").lower() == "true"
    demo_debug_enabled = os.getenv("DEMO_DEBUG", "false").lower() == "true"

    logger.info(console.section_header("🚀 ReactAgent + Extract Agent Demo"))
    logger.info(f"Tool Set: {tool_set_name}")
    logger.info("")

    # Setup LLM
    logger.info("Setting up LLM...")
    llm_config = LLMConfig.from_env()
    setup_llm(llm_config)

    # Create tool registry - check TOOLS_MOCK environment variable
    tools_mock = os.getenv("TOOLS_MOCK", "true").lower() == "true"
    logger.info(f"Using {'mock' if tools_mock else 'real'} results (TOOLS_MOCK={os.getenv('TOOLS_MOCK', 'true')})")
    registry = create_tool_set_registry(tool_set_name, mock_results=tools_mock)

    # Get all test cases from the registry
    test_cases = registry.get_all_test_cases()

    # Filter to specific test case if requested
    if test_case_index is not None:
        if 1 <= test_case_index <= len(test_cases):
            test_cases = [test_cases[test_case_index - 1]]
            logger.info(f"Running test case {test_case_index} only")
        else:
            logger.error(
                console.error_message(
                    f"Invalid test case index: {test_case_index} (valid range: 1-{len(test_cases)})"
                )
            )
            return
    else:
        logger.info(f"Found {len(test_cases)} test cases")

    logger.info("")

    # Track overall results
    successful_tests = 0
    total_time = 0

    # Run each test case
    for i, test_case in enumerate(test_cases, 1):
        logger.info(console.section_header(f"🧪 Test Case {i}/{len(test_cases)}"))
        logger.info(f"Description: {test_case.description}")
        logger.info(f"Query: {test_case.request}")
        logger.info(f"Expected tools: {', '.join(test_case.expected_tools)}")
        logger.info("")

        # Run the test case
        result = run_single_test_case(test_case, registry, tool_set_name, console)

        # Display results
        logger.info(f"\n{console.section_header('📊 Results', char='-', width=60)}")

        if result.status == ActivityStatus.SUCCESS:
            successful_tests += 1
            total_time += result.execution_time

            # Check if tools match expected
            if result.tools_match:
                logger.info(console.success_message("Tools matched expected"))
            else:
                logger.warning(
                    console.warning_message(
                        f"Tools mismatch - Expected: {', '.join(result.expected_tools)}, Got: {', '.join(result.tools_used)}"
                    )
                )

            logger.info(f"Execution time: {result.execution_time:.2f}s")

            # Final answer
            logger.info(
                f"\n{console.section_header('🎯 Final Answer', char='-', width=60)}"
            )
            logger.info(result.answer)

            if result.reasoning and logger.level == logging.DEBUG:
                logger.debug(
                    f"\n{console.section_header('💭 Reasoning', char='-', width=60)}"
                )
                logger.debug(result.reasoning)

            # Save history if DSPY debug is enabled
            if dspy_debug_enabled:
                try:
                    history = get_full_history()
                    saved_path = save_dspy_history(
                        tool_set_name=tool_set_name,
                        agent_type="full_session",
                        index=i,
                        history=history,
                    )
                    if saved_path:
                        logger.debug(f"Saved full session history to: {saved_path}")
                except Exception as e:
                    logger.warning(f"Failed to save full session history: {e}")
        else:
            logger.error(console.error_message(f"Test failed: {result.error}"))

        if i < len(test_cases):
            logger.info(f"\n{'='*80}\n")

    # Summary
    if len(test_cases) > 1:
        logger.info(console.section_header("📈 Summary"))
        logger.info(f"Tests passed: {successful_tests}/{len(test_cases)}")
        logger.info(f"Success rate: {successful_tests/len(test_cases)*100:.1f}%")
        if successful_tests > 0:
            logger.info(f"Average execution time: {total_time/successful_tests:.2f}s")


def main():
    """Main demo function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="ReactAgent + Extract Agent Demo - Run test cases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  poetry run python agentic_loop/demo_react_agent.py              # Run agriculture test cases
  poetry run python agentic_loop/demo_react_agent.py agriculture  # Run all agriculture test cases
  poetry run python agentic_loop/demo_react_agent.py agriculture 2    # Run only agriculture test case 2
  poetry run python agentic_loop/demo_react_agent.py treasure_hunt # Run treasure hunt test cases
  
  # Use TOOLS_MOCK environment variable to control mock/real mode:
  TOOLS_MOCK=false poetry run python agentic_loop/demo_react_agent.py agriculture  # Run with real API calls
        """,
    )

    # First positional argument: tool set or test case number
    parser.add_argument(
        "tool_set_or_index",
        nargs="?",
        default=AgricultureToolSet.NAME,
        help="Tool set name (agriculture, treasure_hunt, etc.) or test case index (1, 2, 3...)",
    )

    # Second positional argument: test case index (only if first arg is tool set)
    parser.add_argument(
        "test_index",
        nargs="?",
        type=int,
        help="Specific test case index to run (optional)",
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set the logging level (default: INFO)",
    )


    args = parser.parse_args()

    # Check if DSPY_DEBUG is enabled and override log level if it is
    dspy_debug_enabled = os.getenv("DSPY_DEBUG", "false").lower() == "true"
    if dspy_debug_enabled:
        setup_logging("DEBUG")
        logger.info("Demo debug mode enabled via DSPY_DEBUG environment variable")
    else:
        setup_logging(args.log_level)

    # Determine if first argument is a tool set or test case index
    tool_set_name = AgricultureToolSet.NAME # default
    test_case_index = None

    # Check if first argument is a number
    try:
        # If it's a number, treat it as test case index for default tool set
        test_case_index = int(args.tool_set_or_index)
    except ValueError:
        # It's a tool set name
        if args.tool_set_or_index in TOOL_SET_MAP:
            tool_set_name = args.tool_set_or_index
            test_case_index = args.test_index
        else:
            logger.error(f"Error: Unknown tool set '{args.tool_set_or_index}'")
            logger.error(f"Available tool sets: {', '.join(TOOL_SET_MAP.keys())}")
            sys.exit(1)

    try:
        run_test_cases(tool_set_name, test_case_index)
    except KeyboardInterrupt:
        logger.info("\n\nDemo interrupted by user.")
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
