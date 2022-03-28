"""
\file core_config.py
\author github:khanbekov, telegram:qoddrysdaim
\brief В файле находится классы конфигурации core
\data 2022.03.12
\version 1.0.1
"""
from pydantic import BaseModel


class AeronChannel(BaseModel):
    channel: str
    stream_id: int


class AeronChannelWithDestinations(AeronChannel):
    destinations: list[str]


# Настройки относящиеся к отправке данных
class AeronPublishers(BaseModel):
    # настройки канала для publishers рассылающего market data
    gateway: AeronChannel
    # настройки publishers осуществляющего отправку баланса
    metrics: AeronChannel
    # настройки publishers осуществляющего отправку логов
    log: AeronChannel


# Настройки относящиеся к приему данных.
class AeronSubscribers(BaseModel):
    # канал в котором приходят команды от ядра.
    balance: AeronChannelWithDestinations
    orderbooks: AeronChannelWithDestinations


class Aeron(BaseModel):
    publishers: AeronPublishers
    subscribers: AeronSubscribers


class CoreConfig(BaseModel):
    # настройки транспортного уровня
    aeron: Aeron
