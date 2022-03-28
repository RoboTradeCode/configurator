"""
\file market_models.py
\author github:khanbekov, telegram:qoddrysdaim
\brief В файле находится классы для хранения информации о маркетах и ассетах (их возвращает API)
\data 2022.03.12
\version 1.0.1
"""
from pydantic import BaseModel


# Класс для хранения данных о названии актива на бирже, и общепринятом названии
# exchange: str - название актива на бирже
# common: str - общепринятое названии
class AssetLabel(BaseModel):
    exchange: str
    common: str


# Класс для хранения данных о торговой паре на бирже
# exchange_symbol: str - как торговая пара называется на бирже (примеры: BTC/USDT, ETH-USDT, fBTCUST)
# common_symbol: str - универсальное название торговой пары (примеры: BTC/USDT, ETH/USDT, SHIB/BTC)
# price_increment: float - шаг цены (примеры: 0.00001, 0.5, 0.025)
# amount_increment: float - шаг объема (примеры: 0.00001, 0.5, 0.025)
# assets: Assets - содержат два поля, base - базовый актив, quote - котируемый актив
class Market(BaseModel):
    exchange_symbol: str
    common_symbol: str
    price_increment: float
    amount_increment: float

    class Assets(BaseModel):
        base: str
        quote: str

    assets: Assets