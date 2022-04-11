"""
\file settings.py
\author github:khanbekov, telegram:qoddrysdaim
\brief В файле находятся настройки программы
\data 2022.03.12
\version 1.0.1
"""

PATH_TO_CONFIGS_FOLDER = './configs'

ERROR_LOG_FILENAME = ".configurator-errors.log"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s:%(name)s:%(process)d:%(lineno)d " "%(levelname)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "%(message)s",
        },
    },
    "handlers": {
        "logfile": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "WARNING",
            "filename": ERROR_LOG_FILENAME,
            "formatter": "default",
            "backupCount": 2,
        },
        "stdout": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "configurator": {
            "level": "INFO",
            "handlers": [
                "stdout",
            ],
        },
    },
    "root": {"level": "INFO", "handlers": ["logfile", "stdout"]},
}
