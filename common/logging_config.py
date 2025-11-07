"""
Logging configuration for AI agent tutorials.
Uses Python's standard logging module with enhanced formatting.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from common.config import LOGS_DIR


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path. If None, logs only to console.
        
    Returns:
        Configured logger instance
    """
    # Get numeric log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter with detailed information
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if log_file specified
    if log_file:
        file_path = LOGS_DIR / log_file
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {log_level}, Log dir: {LOGS_DIR}")
    
    return logger


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Name for the logger (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Default logger instance
logger = get_logger()
