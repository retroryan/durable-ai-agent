import asyncio
import concurrent.futures
import logging
import os
from datetime import datetime

import dspy
from dotenv import load_dotenv
from temporalio.worker import Worker

from activities.react_agent_activity import ReactAgent
from agentic_loop.demo_react_agent import create_tool_set_registry
from agentic_loop.react_agent import ReactAgent as AgenticReactAgent
from shared.config import TEMPORAL_TASK_QUEUE, get_temporal_client
from shared.llm_utils import LLMConfig, setup_llm
from shared.logging_config import setup_file_logging
from workflows.agentic_ai_workflow import AgenticAIWorkflow


async def main():
    # Load environment variables from worker.env
    load_dotenv("worker.env", override=True)

    # Initialize logging
    log_file = setup_file_logging("worker", log_level=logging.INFO)
    logging.info(f"Worker starting up. Log file: {log_file}")

    # Setup LLM
    llm_config = LLMConfig.from_env()
    setup_llm(llm_config)

    # Create tool registry
    tool_set_name = os.getenv("TOOL_SET", "agriculture")
    registry = create_tool_set_registry(tool_set_name)
    logging.info(f"Tool registry created for tool set: {tool_set_name}")

    # Initialize the Agentic React Agent here
    tool_set_signature = registry.get_react_signature()

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

    # Initialize AgenticReactAgent from agentic_loop
    agentic_react_agent = AgenticReactAgent(
        signature=ReactSignature, tool_registry=registry
    )
    logging.info(f"AgenticReactAgent initialized with tool set: {tool_set_name}")

    # Create activity with the initialized agent
    react_agent_activity = ReactAgent(agentic_react_agent)
    logging.info(f"ReactAgent activity created with pre-initialized agent")

    # Create the client
    try:
        client = await get_temporal_client()
        logging.info("Temporal client initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize Temporal client: {e}", exc_info=True)
        raise

    print("Worker ready to process tasks!")

    # Run the worker with proper cleanup
    try:
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=100
        ) as activity_executor:
            worker = Worker(
                client,
                task_queue=TEMPORAL_TASK_QUEUE,
                workflows=[AgenticAIWorkflow],
                activities=[
                    react_agent_activity.run_react_agent,
                ],
                activity_executor=activity_executor,
            )

            logging.info(
                f"Starting worker, connecting to task queue: {TEMPORAL_TASK_QUEUE}"
            )
            print(f"Starting worker, connecting to task queue: {TEMPORAL_TASK_QUEUE}")
            await worker.run()
    except Exception as e:
        logging.error(f"Worker failed: {e}", exc_info=True)
        raise
    finally:
        # Cleanup resources
        logging.info("Cleaning up MCP connections")


if __name__ == "__main__":
    asyncio.run(main())
