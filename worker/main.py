"""Temporal worker for the durable AI agent."""
import asyncio
import logging

# Configure logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from temporalio.client import Client
from temporalio.worker import Worker

from activities import find_events_activity, weather_forecast_activity
from shared.config import get_settings
from workflows import SimpleAgentWorkflow

# Create logs directory if it doesn't exist
os.makedirs("/app/logs", exist_ok=True)

# Generate timestamp for log filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"/app/logs/worker_{timestamp}.log"

# Configure logging with both console and file handlers
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Console output
        RotatingFileHandler(
            log_filename, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
        ),
    ],
)
logger = logging.getLogger(__name__)
logger.info(f"Worker logging to: {log_filename}")


async def main():
    """Start the Temporal worker."""
    settings = get_settings()

    # Configure logging level
    logging.getLogger().setLevel(settings.log_level)

    logger.info(f"Connecting to Temporal at {settings.temporal_host}")

    # Create Temporal client
    client = await Client.connect(
        settings.temporal_host,
        namespace=settings.temporal_namespace,
    )

    # Create worker
    worker = Worker(
        client,
        task_queue=settings.task_queue,
        workflows=[SimpleAgentWorkflow],
        activities=[find_events_activity, weather_forecast_activity],
    )

    logger.info(f"Starting worker on task queue: {settings.task_queue}")
    logger.info("Registered workflows: SimpleAgentWorkflow")
    logger.info(
        "Registered activities: find_events_activity, weather_forecast_activity"
    )

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
