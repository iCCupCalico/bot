import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logger(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up and configure the logger.

    Args:
        log_level: The logging level (default: logging.INFO)
        log_file: Path to the log file (default: None, logs to console only)

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("dota_stats_bot")
    logger.setLevel(log_level)

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(detailed_formatter)
    logger.addHandler(console_handler)

    # Create file handler if log_file is specified
    if log_file:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Create rotating file handler (10 MB max size, keep 3 backup files)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=3
        )
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

    return logger
