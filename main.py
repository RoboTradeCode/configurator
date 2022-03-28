"""
\file main.py
\author github:khanbekov, telegram:qoddrysdaim
\brief Точка входа Configurator
\data 2022.03.12
\version 1.0.1
"""
import asyncio

import uvicorn

from src.api.api import app
from src.settings import LOGGING_CONFIG

# запуск сервера
uvicorn.run(app, port=8000, debug=True, log_config=LOGGING_CONFIG)