"""
\file gate_config.py
\author github:khanbekov, telegram:qoddrysdaim
\brief В файле находится классы конфигурации core
\data 2022.03.12
\version 1.0.1
"""
from typing import Optional

from pydantic import BaseModel


# раздел содержит информацию относительно настроек биржы
class Exchange(BaseModel):
    # имя биржи, записывается в сообщениях, которые отправляет данный шлюз
    name: str
    instance: str


# настройки аккаунта
class Account(BaseModel):
    api_key: str
    secret_key: str
    passphrase: Optional[str]


class AeronChannel(BaseModel):
    channel: str
    stream_id: int


# Настройки относящиеся к отправке данных
class AeronPublishers(BaseModel):
    # настройки канала для publishers рассылающего market data
    orderbook: AeronChannel
    # настройки publishers осуществляющего отправку баланса
    balance: AeronChannel
    # настройки publishers осуществляющего отправку логов
    log: AeronChannel


# Настройки относящиеся к приему данных.
class AeronSubscribers(BaseModel):
    # канал в котором приходят команды от ядра.
    core: AeronChannel


class Aeron(BaseModel):
    publishers: AeronPublishers
    subscribers: AeronSubscribers


class GateConfig(BaseModel):
    # раздел содержит информацию относительно настроек биржы
    exchange: Exchange
    # настройки аккаунта
    account: Account
    # настройки транспортного уровня
    aeron: Aeron
