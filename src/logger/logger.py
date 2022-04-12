import logging.config
from logging import StreamHandler

from src.settings import LOGGING_CONFIG


# Загрузка настроек логгера и инициализация логгера
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)