"""
\file setup.py
\author github:khanbekov, telegram:qoddrysdaim
\brief Точка входа Configurator
\data 2022.03.12
"""
import uvicorn

from configurator.api.api import app
from configurator.settings import LOGGING_CONFIG

if __name__ == '__main__':
    # запуск сервера
    uvicorn.run(app, host='0.0.0.0', port=8000, log_config=LOGGING_CONFIG)
