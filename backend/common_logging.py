import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(name, debug_to_console=False):
    logger = logging.getLogger(name)
    logger.setLevel(logging.CRITICAL)
    
    # Ensure the logs directory exists
    os.makedirs('backend/logs', exist_ok=True)
    
    # File handler
    file_handler = RotatingFileHandler(f'backend/logs/{name}.log', maxBytes=10000000, backupCount=5)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    if debug_to_console:
        # Console handler for debug mode
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)
    
    return logger
