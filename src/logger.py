import logging
import sys
from src.config import DEBUG_LOGS_ENABLED


class Logger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        if not self.logger.hasHandlers():
            handler = logging.StreamHandler(sys.stderr)
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(name)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.setLevel(
            logging.DEBUG if DEBUG_LOGS_ENABLED else logging.INFO)

    def log(self, message):
        self.logger.info(message)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)
