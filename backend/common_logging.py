import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(name, debug_to_console=False):
    logger = logging.getLogger(name)
    
    if logger.hasHandlers():  # Check if handlers are already set up
        return logger  # If handlers exist, return the logger
    
    logger.setLevel(logging.DEBUG)
    
    # Use an absolute path based on the script's location                                                                    
    log_dir = os.path.join(os.path.dirname(__file__), 'logs') 
    
    # Ensure the logs directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # File handler
    file_handler = RotatingFileHandler(f'logs/{name}.log', maxBytes=10000000, backupCount=5)
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

