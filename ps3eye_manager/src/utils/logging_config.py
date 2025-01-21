"""
Centralized logging configuration for PS3 Eye Manager
"""
import os
import sys
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

def setup_logging(log_dir: str = None, debug: bool = False) -> None:
    """
    Configure the logging system for the application
    
    Args:
        log_dir: Directory to save log files. If None, use the default directory
        debug: If True, set the logging level to DEBUG
    """
    if log_dir is None:
        log_dir = Path.home() / "PS3EyeManager" / "logs"
    
    # Create the log directory if it does not exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate the log file name with the date
    log_file = Path(log_dir) / f"ps3eye_manager_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Configure the log format
    log_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    
    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add new handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Specific loggers for components
    loggers = {
        'camera': logging.getLogger('ps3eye.camera'),
        'server': logging.getLogger('ps3eye.server'),
        'ui': logging.getLogger('ps3eye.ui'),
        'driver': logging.getLogger('ps3eye.driver'),
    }
    
    # Configure specific loggers
    for name, logger in loggers.items():
        logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
    logging.info("Logging system successfully configured")
    if debug:
        logging.debug("Debug mode activated")
