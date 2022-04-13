"""
\file settings.py
\author github:khanbekov, telegram:qoddrysdaim
\brief Файл загружает настройки Configurator
\data 2022.03.12
"""
import tomli

CONFIG_PATH = 'config.toml'

with open(CONFIG_PATH, "rb") as f:
    toml_dict = tomli.load(f)

PATH_TO_CONFIGS_FOLDER = toml_dict['data']['path_to_configs_folder']

LOGGING_CONFIG = toml_dict['logging']
