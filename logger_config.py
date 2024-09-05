import logging
import os

# Get log file path from environment variable, or use a default
LOG_FILE = os.environ.get('CONAGUA_LOG_FILE', os.path.join(os.getcwd(), 'conagua_unified.log'))

def setup_logging(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Check if logger already has handlers to avoid duplicate logging
    if not logger.handlers:
        # Ensure the directory for the log file exists
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

        # File handler
        file_handler = logging.FileHandler(LOG_FILE)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(file_formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        console_handler.setFormatter(console_formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger