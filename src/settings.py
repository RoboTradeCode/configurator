"""
\file settings.py
\author github:khanbekov, telegram:qoddrysdaim
\brief Файл загружает настройки Configurator
\data 2022.03.12
"""
import os

import tomli

API_CONFIGURATION_PATH = 'config.toml'


AERON_SERVICE_NAME = 'aeron'
if os.system(f'systemctl is-active --quiet {AERON_SERVICE_NAME}') != 0:
    print('Critical: Aeron service is not launched. Please launch Aeron before launching Configurator.')
    exit(1)

with open(API_CONFIGURATION_PATH, "rb") as f:
    toml_dict = tomli.load(f)

PATH_TO_TRADE_SERVERS_CONFIGS = toml_dict['data']['path_to_trade_servers_configs']

LOGGING_CONFIG = toml_dict['logging']
