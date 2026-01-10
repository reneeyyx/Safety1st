"""Simple utility functions for the backend"""
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Logger:
    """Simple logger wrapper"""

    @staticmethod
    def info(*args):
        """Log info message"""
        message = " ".join(str(arg) for arg in args)
        logging.info(message)

    @staticmethod
    def warn(*args):
        """Log warning message"""
        message = " ".join(str(arg) for arg in args)
        logging.warning(message)

    @staticmethod
    def error(*args):
        """Log error message"""
        message = " ".join(str(arg) for arg in args)
        logging.error(message)

logger = Logger()
