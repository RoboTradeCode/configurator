"""
\file logger.py
\author github:khanbekov, telegram:qoddrysdaim
\brief Объявление логгера и загрузка его конфигурации
\data 2022.04.11
"""
import logging.config
from logging import StreamHandler

from src.settings import LOGGING_CONFIG


# Загрузка настроек логгера и инициализация логгера
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)