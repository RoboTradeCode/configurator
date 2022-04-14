"""
\file settings.py
\author github:khanbekov, telegram:qoddrysdaim
\brief Файл загружает настройки Configurator
\data 2022.03.12
"""
import tomli

API_CONFIGURATION_PATH = 'config.toml'

with open(API_CONFIGURATION_PATH, "rb") as f:
    toml_dict = tomli.load(f)

PATH_TO_TRADE_SERVERS_CONFIGS = toml_dict['data']['path_to_trade_servers_configs']

LOGGING_CONFIG = toml_dict['logging']
