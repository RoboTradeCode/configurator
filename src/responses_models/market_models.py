"""
\file market_models.py
\author github:khanbekov, telegram:qoddrysdaim
\brief В файле находится классы для хранения информации о маркетах и ассетах (их возвращает API)
\data 2022.03.12
"""
from typing import Optional

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
# min_amount: float - минимальный объем ордера
# max_amount: float - максимальный объем ордера
# base_asset: str - базовый актив
# quote_asset: str - котируемый актив
class Market(BaseModel):
    class Precision(BaseModel):
        price: Optional[float]
        amount: Optional[float]
        cost: Optional[float]

    class Limits(BaseModel):
        class MinMax(BaseModel):
            min: Optional[float]
            max: Optional[float]
        amount: MinMax
        price: MinMax
        cost: MinMax
        leverage: MinMax

    exchange_symbol: str
    common_symbol: str
    precision: Precision
    limits: Limits
    base_asset: str
    quote_asset: str
