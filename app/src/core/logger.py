"""
Module for logging.
It is used to import the MainLogger class.

Imports: paths.
"""

import logging
from logging.handlers import RotatingFileHandler

from . import paths

class MainLogger:
    """
    Singleton class for the main logger.

    Useful methods:
    - get: Returns the instance of the MainLogger.
    """
    _instance: logging.Logger|None = None

    @classmethod
    def get(cls) -> logging.Logger:
        """
        Returns the instance of the MainLogger.
        """
        if not cls._instance:
            with paths.LOG_FILE.open('a') as log_file:
                log_file.write("\n\n")
            formatter: logging.Formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler: RotatingFileHandler = RotatingFileHandler(paths.LOG_FILE, maxBytes=1024*1024, backupCount=5)
            file_handler.setFormatter(formatter)
            logger_name: str = 'main_logger'
            cls._instance = logging.getLogger(logger_name)
            cls._instance.setLevel(logging.DEBUG)
            cls._instance.addHandler(file_handler)
        return cls._instance
