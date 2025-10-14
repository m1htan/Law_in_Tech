"""
Logging utility for Vietnamese Legal Crawler
"""
import sys
from pathlib import Path
from loguru import logger
from src.config import Config

def setup_logger(name: str = "vietnamese_legal_crawler"):
    """
    Setup logger with file and console output
    
    Args:
        name: Logger name for the log file
    """
    # Remove default logger
    logger.remove()
    
    # Add console handler with color
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Add file handler for all logs
    log_file = Config.LOG_DIR / f"{name}.log"
    logger.add(
        log_file,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )
    
    # Add separate file handler for errors
    error_log_file = Config.LOG_DIR / f"{name}_errors.log"
    logger.add(
        error_log_file,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR"
    )
    
    logger.info(f"Logger initialized: {name}")
    logger.info(f"Log files: {log_file}, {error_log_file}")
    
    return logger

# Initialize default logger
log = setup_logger()
