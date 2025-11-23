"""Logging configuration module.

This module provides a unified logging setup for the QA Sentinel project with:
- Console logging to stdout
- Rotating file logging to logs/qa_sentinel.log
- Consistent formatting with timestamps, log levels, and logger names
- Simple get_logger() helper function for easy logger creation
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


# Logs directory
LOGS_DIR = Path("logs")
LOG_FILE = LOGS_DIR / "qa_sentinel.log"

# Log format
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Default log level
DEFAULT_LOG_LEVEL = logging.INFO

# Track if handlers have been configured
_handlers_configured = False


def _setup_handlers():
    """
    Configure logging handlers (console and rotating file).
    
    This function ensures handlers are added only once by checking
    the _handlers_configured flag. It creates the logs directory if needed
    and sets up both console and file handlers.
    """
    global _handlers_configured
    
    if _handlers_configured:
        return
    
    # Create logs directory if it doesn't exist
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(DEFAULT_LOG_LEVEL)
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(DEFAULT_LOG_LEVEL)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Rotating file handler
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1024 * 1024,  # 1 MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(DEFAULT_LOG_LEVEL)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    _handlers_configured = True


def get_logger(name: str = "qa-sentinel") -> logging.Logger:
    """
    Return a configured logger with the given name.
    
    Ensures handlers are added only once. The logger will output to both
    console (stdout) and a rotating file (logs/qa_sentinel.log).
    
    Args:
        name: Logger name (typically module or component name).
              Defaults to "qa-sentinel" for the root logger.
    
    Returns:
        Configured Logger instance with console and file handlers
    
    Example:
        >>> logger = get_logger("orchestrator")
        >>> logger.info("Pipeline started")
        >>> logger.error("Failed to process story")
    """
    # Ensure handlers are configured
    _setup_handlers()
    
    # Get or create logger with the specified name
    logger = logging.getLogger(name)
    logger.setLevel(DEFAULT_LOG_LEVEL)
    
    return logger

