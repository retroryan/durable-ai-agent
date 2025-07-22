import asyncio
import concurrent.futures
import logging
import os

import dspy
from dotenv import load_dotenv
from temporalio.worker import Worker

from activities.tool_execution_activity import ToolExecutionActivity
from activities.react_agent_activity import ReactAgentActivity
from activities.extract_agent_activity import ExtractAgentActivity

from shared.tool_utils.registry import create_tool_set_registry
from agentic_loop.react_agent import ReactAgent
from agentic_loop.extract_agent import ReactExtract
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

    # Create tool registry with mock configuration (default to mock for worker)
    tool_set_name = os.getenv("TOOL_SET", "agriculture")
    # Workers default to mock mode for safety and predictability
    registry = create_tool_set_registry(tool_set_name, mock_results=True)
    logging.info(f"Tool registry created for tool set: {tool_set_name} (mock_results=True)")

    # Initialize the Agentic React Agent here
    tool_set_signature = registry.get_react_signature()

    if tool_set_signature:
        ReactSignature = tool_set_signature
    else:
        # Fallback to generic signature
        class ReactSignature(dspy.Signature):
            """Use tools to answer the user's question."""

            user_query: str = dspy.InputField(desc="The user's question")

    # Initialize ReactAgent from agentic_loop
    agentic_react_agent = ReactAgent(signature=ReactSignature, tool_registry=registry)
    logging.info(f"ReactAgent initialized with tool set: {tool_set_name}")

    # Create activity with the initialized agent
    react_agent_activity = ReactAgentActivity(agentic_react_agent)
    logging.info(f"ReactAgent activity created with pre-initialized agent")

    # Initialize ExtractAgent
    extract_signature = registry.get_extract_signature()
    if not extract_signature:
        # Fallback to generic extract signature
        class ExtractSignature(dspy.Signature):
            """Extract the final answer from the agent's trajectory."""
            
            user_query: str = dspy.InputField(desc="The original user's question")
            answer: str = dspy.OutputField(desc="The final answer to the user's question")
            reasoning: str = dspy.OutputField(desc="The reasoning behind the answer")
        
        extract_signature = ExtractSignature
    
    extract_agent_activity = ExtractAgentActivity()
    logging.info(f"ExtractAgent activity created with AnswerExtractionSignature")

    tool_execution_activity = ToolExecutionActivity(tool_registry=registry)
    logging.info(f"ToolExecutionActivity initialized with tool registry (handles both traditional and MCP tools)")

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
                    extract_agent_activity.run_extract_agent,
                    tool_execution_activity.execute_tool,
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
        if hasattr(tool_execution_activity, 'cleanup'):
            await tool_execution_activity.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
