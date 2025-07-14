import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx


def setup_file_logging(
    service_name: str,
    log_level: int = logging.INFO,
    file_log_level: int = logging.DEBUG,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    log_dir: str = "logs",
) -> Optional[Path]:
    """
    Configure logging to write to both console and file.

    Args:
        service_name: Name of the service (e.g., 'worker', 'api')
        log_level: Console logging level (default: INFO)
        file_log_level: File logging level (default: DEBUG)
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup files to keep
        log_dir: Directory to store log files

    Returns:
        Path to the log file if successful, None otherwise
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
    )

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(min(log_level, file_log_level))

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation - include timestamp for each restart
    log_filename = (
        log_path / f"{service_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_filename, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setLevel(file_log_level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # Log startup message
        logging.info(f"{service_name} logging initialized. Log file: {log_filename}")

        return log_filename
    except Exception as e:
        logging.error(f"Failed to setup file logging: {e}")
        return None


def configure_temporal_logging(level: int = logging.INFO):
    """Configure Temporal-specific loggers."""
    logging.getLogger("temporalio").setLevel(level)
    logging.getLogger("temporal.workflow").setLevel(level)


def test_ollama_connectivity():
    """Test Ollama connectivity and log results."""
    llm_model = os.getenv("LLM_MODEL", "")

    if not llm_model.startswith("ollama"):
        logging.info(
            f"Not using Ollama (model: {llm_model}), skipping connectivity test"
        )
        return True

    ollama_base_url = os.getenv("LLM_BASE_URL", "http://host.docker.internal:11434")

    logging.info(f"Testing Ollama connectivity to {ollama_base_url}")

    try:
        # Test basic connectivity to Ollama
        with httpx.Client(timeout=5.0) as client:
            # Try to get version info
            response = client.get(f"{ollama_base_url}/api/version")
            if response.status_code == 200:
                version_info = response.json()
                logging.info(
                    f"✅ Ollama connected successfully. Version: {version_info.get('version', 'unknown')}"
                )

                # Test if the specific model exists
                model_name = llm_model.replace("ollama/", "")
                try:
                    model_response = client.post(
                        f"{ollama_base_url}/api/show", json={"name": model_name}
                    )
                    if model_response.status_code == 200:
                        logging.info(f"✅ Model {model_name} is available")
                        return True
                    else:
                        logging.warning(
                            f"⚠️ Model {model_name} not found. You may need to run: ollama pull {model_name}"
                        )
                        return False
                except Exception as e:
                    logging.warning(f"⚠️ Could not check model {model_name}: {e}")
                    return True  # Ollama is running, just can't check model

            else:
                logging.error(f"❌ Ollama responded with status {response.status_code}")
                return False

    except httpx.ConnectError:
        logging.error(f"❌ Cannot connect to Ollama at {ollama_base_url}")
        logging.error("   Possible solutions:")
        logging.error("   1. Start Ollama: ollama serve")
        logging.error(
            "   2. Check Docker networking (host.docker.internal should work on Mac/Windows)"
        )
        logging.error("   3. Verify Ollama is running on port 11434")
        return False
    except Exception as e:
        logging.error(f"❌ Unexpected error testing Ollama connectivity: {e}")
        return False
