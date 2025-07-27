import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx


class TimestampedRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """RotatingFileHandler that uses timestamps for rotated files instead of numbers."""
    
    def doRollover(self):
        """Override to use timestamp naming for rotated files."""
        if self.stream:
            self.stream.close()
            self.stream = None
        
        # Generate timestamp for the rotated file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Move current log to timestamped backup
        if os.path.exists(self.baseFilename):
            # Get the base name without extension
            base_name = os.path.splitext(self.baseFilename)[0]
            ext = os.path.splitext(self.baseFilename)[1]
            
            # Create new filename with timestamp
            dfn = f"{base_name}_{timestamp}{ext}"
            os.rename(self.baseFilename, dfn)
            
            # Clean up old files if we exceed backupCount
            if self.backupCount > 0:
                # Get all backup files matching our pattern
                dir_name = os.path.dirname(dfn)
                base_name_only = os.path.basename(base_name)
                pattern = f"{base_name_only}_*{ext}"
                
                backup_files = []
                for filename in os.listdir(dir_name or '.'):
                    if filename.startswith(f"{base_name_only}_") and filename.endswith(ext):
                        backup_files.append(os.path.join(dir_name, filename))
                
                # Sort by modification time and delete oldest if needed
                backup_files.sort(key=lambda x: os.path.getmtime(x))
                while len(backup_files) > self.backupCount:
                    os.remove(backup_files[0])
                    backup_files.pop(0)
        
        # Open new file
        self.stream = self._open()


def setup_file_logging(
    service_name: str,
    log_level: int = logging.INFO,
    file_log_level: int = logging.DEBUG,
    max_bytes: int = 5 * 1024 * 1024,  # 5MB - Simple rotation size for demo
    backup_count: int = 10,  # Keep last 10 rotated files for demo
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

    # Use consistent filename (no timestamp) to enable proper rotation
    log_filename = log_path / f"{service_name}.log"
    
    try:
        # Simple rotating file handler - rotates at 5MB, keeps 10 files with timestamp naming
        file_handler = TimestampedRotatingFileHandler(
            log_filename, 
            maxBytes=max_bytes,  # 5MB per file
            backupCount=backup_count  # Keep 10 backup files (50MB total)
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

    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")

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
