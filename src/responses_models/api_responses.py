"""
\file api_responses.py
\author github:khanbekov, telegram:qoddrysdaim
\brief В файле находятся классы и части классов (композиция), которые возвращает API при нормальной работе,
т.е. без исключений. Для исключений используются классы из файла api_errors.py
\data 2022.03.12
\version 1.0.1
"""
from pydantic import BaseModel

from src.responses_models.market_models import AssetLabel, Market


# Класс для описания одного шага Торгового маршрута
# source_asset: str - Ассет, который нужен для выполнения операции
# common_symbol: str - Название торговой пары (маркета)
# operation: str - Указание, нужно произвести покупку или продажу с торговой парой (маркетом), "buy" или "sell"
class RouteStep(BaseModel):
    source_asset: str
    common_symbol: str
    operation: str


class MarketsResponseData(BaseModel):
    markets: list[Market]
    assets_labels: list[AssetLabel]
    routes: list[list[RouteStep]]
    sections: dict

class MarketsResponse(BaseModel):
    is_new: bool
    data: MarketsResponseData

