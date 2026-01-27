"""
Logging configuration for Schmekla.

Uses loguru for structured, colorful logging with file rotation.
"""

import sys
from pathlib import Path
from loguru import logger


def setup_logging(log_dir: Path = None, debug: bool = False):
    """
    Configure logging for the application.

    Args:
        log_dir: Directory for log files. Defaults to ~/.schmekla/logs
        debug: Enable debug level logging
    """
    # Remove default handler
    logger.remove()

    # Determine log directory
    if log_dir is None:
        log_dir = Path.home() / ".schmekla" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Console handler with colors
    log_level = "DEBUG" if debug else "INFO"
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # File handler with rotation
    log_file = log_dir / "schmekla.log"
    logger.add(
        log_file,
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )

    logger.debug(f"Logging initialized. Log file: {log_file}")


def get_logger(name: str):
    """
    Get a logger instance for a module.

    Args:
        name: Module name (usually __name__)

    Returns:
        Logger instance
    """
    return logger.bind(name=name)
