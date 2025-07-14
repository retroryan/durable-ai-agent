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
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import dspy

# Add the project root to Python path so imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared" / "tool_utils"))

# Import shared utilities
from shared import ConsoleFormatter, setup_llm
from shared.llm_utils import get_full_history, save_dspy_history

# Import tool sets
from shared.tool_utils import EcommerceToolSet, EventsToolSet
from shared.tool_utils.agriculture_tool_set import AgricultureToolSet
from shared.tool_utils.registry import ToolRegistry

# Tool set class mapping using NAME constants
TOOL_SET_MAP = {
    EcommerceToolSet.NAME: EcommerceToolSet,
    AgricultureToolSet.NAME: AgricultureToolSet,
    EventsToolSet.NAME: EventsToolSet,
}

# Initialize module-level logger
logger = logging.getLogger(__name__)


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


def create_tool_set_registry(tool_set_name: str) -> ToolRegistry:
    """Create tool registry for a specific tool set."""
    tool_set_class = TOOL_SET_MAP[tool_set_name]
    tool_set = tool_set_class()

    # Create registry and load tools
    registry = ToolRegistry()
    registry.register_tool_set(tool_set)

    return registry


def run_react_loop(
    react_agent,
    tool_registry,
    user_query: str,
    tool_set_name: str,
    max_iterations: int = 5,
) -> Tuple[Dict[str, Any], float]:
    """
    Run the React agent loop until completion or max iterations.

    Args:
        react_agent: The initialized ReactAgent
        tool_registry: The tool registry for executing tools
        user_query: The user's question
        tool_set_name: Name of the tool set being used
        max_iterations: Maximum number of iterations

    Returns:
        Tuple of (trajectory dictionary, execution time)
    """
    trajectory = {}
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
        trajectory, tool_name, tool_args = react_agent(
            trajectory=trajectory,
            current_iteration=current_iteration,
            user_query=user_query,
        )

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

        logger.debug(f"Tool selected: {tool_name}")
        logger.debug(f"Tool args: {tool_args}")

        # Check if we're done
        if tool_name == "finish":
            logger.debug("Agent selected 'finish' - task complete")
            # Add final observation for finish
            trajectory[f"observation_{current_iteration-1}"] = "Completed."
            break

        # Execute the tool if it's not finish
        if tool_name in tool_registry.get_all_tools():
            try:
                tool = tool_registry.get_tool(tool_name)
                logger.debug(f"Executing tool: {tool_name}")
                result = tool.execute(**tool_args)
                logger.debug(f"Tool result: {result}")

                # Add tool result to trajectory
                idx = current_iteration - 1
                trajectory[f"observation_{idx}"] = result

            except Exception as e:
                logger.error(f"Tool execution error: {e}", exc_info=True)
                trajectory[f"observation_{current_iteration-1}"] = f"Error: {e}"
        else:
            logger.warning(f"Unknown tool: {tool_name}")
            trajectory[
                f"observation_{current_iteration-1}"
            ] = f"Error: Unknown tool {tool_name}"

        current_iteration += 1

    if current_iteration > max_iterations:
        logger.warning(f"Reached maximum iterations ({max_iterations})")

    execution_time = time.time() - start_time
    return trajectory, execution_time


def extract_final_answer(
    trajectory: Dict[str, Any], user_query: str, tool_set_name: str
) -> Tuple[str, str]:
    """
    Extract the final answer from the trajectory using the Extract Agent.

    Args:
        trajectory: The complete trajectory from the React loop
        user_query: The original user query
        tool_set_name: Name of the tool set being used

    Returns:
        Tuple of (answer, reasoning)
    """
    from agentic_loop.extract_agent import ReactExtract

    # Check if DEMO debug mode is enabled
    demo_debug_enabled = os.getenv("DEMO_DEBUG", "false").lower() == "true"

    logger.debug("Extracting final answer from trajectory")
    logger.debug(f"Trajectory keys: {list(trajectory.keys())}")

    # Create a signature for answer extraction
    class AnswerExtractionSignature(dspy.Signature):
        """Extract a clear, concise answer from the gathered information."""

        user_query: str = dspy.InputField(desc="The user's original question")
        answer: str = dspy.OutputField(
            desc="Clear, direct answer to the user's question"
        )

    # Initialize Extract Agent
    extract_agent = ReactExtract(signature=AnswerExtractionSignature)

    # Extract answer from trajectory
    logger.debug("Calling Extract Agent")
    result = extract_agent(trajectory=trajectory, user_query=user_query)

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
) -> Dict[str, Any]:
    """Run a single test case and return results."""
    from agentic_loop.react_agent import ReactAgent

    # Check if DSPY debug mode is enabled
    dspy_debug_enabled = os.getenv("DSPY_DEBUG", "false").lower() == "true"

    # Get tool set specific signature if available
    tool_set_signature = tool_registry.get_react_signature()

    if tool_set_signature:
        # Format the signature's docstring with current date if needed
        current_date = datetime.now().strftime("%Y-%m-%d")
        if hasattr(tool_set_signature, "__doc__") and tool_set_signature.__doc__:
            tool_set_signature.__doc__ = tool_set_signature.__doc__.format(
                current_date=current_date
            )
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
        trajectory, react_time = run_react_loop(
            react_agent=react_agent,
            tool_registry=tool_registry,
            user_query=test_case.request,
            tool_set_name=tool_set_name,
            max_iterations=5,
        )

        # Extract tools used
        tools_used = []
        for key in sorted(trajectory.keys()):
            if key.startswith("tool_name_") and trajectory[key] != "finish":
                tools_used.append(trajectory[key])

        logger.info(f"✓ React loop completed in {react_time:.2f}s")
        logger.info(
            f"  Iterations: {len([k for k in trajectory.keys() if k.startswith('thought_')])}"
        )
        logger.info(f"  Tools used: {', '.join(tools_used) if tools_used else 'None'}")

        # Extract final answer
        logger.info(
            f"\n{console.section_header('📝 Extract Agent', char='-', width=60)}"
        )
        answer, reasoning = extract_final_answer(
            trajectory, test_case.request, tool_set_name
        )

        logger.info("✓ Answer extracted successfully")

        return {
            "status": "success",
            "trajectory": trajectory,
            "tools_used": tools_used,
            "execution_time": react_time,
            "answer": answer,
            "reasoning": reasoning,
            "expected_tools": test_case.expected_tools,
            "tools_match": set(tools_used) == set(test_case.expected_tools),
        }

    except Exception as e:
        logger.error(f"Test case failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "execution_time": 0,
            "tools_used": [],
            "expected_tools": test_case.expected_tools,
            "tools_match": False,
        }


def run_test_cases(tool_set_name: str, test_case_index: Optional[int] = None):
    """Run test cases for a tool set."""
    console = ConsoleFormatter()

    # Check if DSPY debug mode is enabled
    dspy_debug_enabled = os.getenv("DSPY_DEBUG", "false").lower() == "true"
    demo_debug_enabled = os.getenv("DEMO_DEBUG", "false").lower() == "true"

    logger.info(console.section_header("🚀 ReactAgent + Extract Agent Demo"))
    logger.info(f"Tool Set: {tool_set_name}")
    logger.info("")

    # Setup LLM
    logger.info("Setting up LLM...")
    setup_llm()

    # Create tool registry
    registry = create_tool_set_registry(tool_set_name)

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

        if result["status"] == "success":
            successful_tests += 1
            total_time += result["execution_time"]

            # Check if tools match expected
            if result["tools_match"]:
                logger.info(console.success_message("Tools matched expected"))
            else:
                logger.warning(
                    console.warning_message(
                        f"Tools mismatch - Expected: {', '.join(result['expected_tools'])}, Got: {', '.join(result['tools_used'])}"
                    )
                )

            logger.info(f"Execution time: {result['execution_time']:.2f}s")

            # Final answer
            logger.info(
                f"\n{console.section_header('🎯 Final Answer', char='-', width=60)}"
            )
            logger.info(result["answer"])

            if result["reasoning"] and logger.level == logging.DEBUG:
                logger.debug(
                    f"\n{console.section_header('💭 Reasoning', char='-', width=60)}"
                )
                logger.debug(result["reasoning"])

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
            logger.error(console.error_message(f"Test failed: {result['error']}"))

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
        """,
    )

    # First positional argument: tool set or test case number
    parser.add_argument(
        "tool_set_or_index",
        nargs="?",
        default="agriculture",
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
    tool_set_name = "agriculture"  # default
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
