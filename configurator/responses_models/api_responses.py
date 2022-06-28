"""
\file api_responses.py
\author github:khanbekov, telegram:qoddrysdaim
\brief В файле находятся классы и части классов (композиция), которые возвращает API при нормальной работе,
т.е. без исключений. Для исключений используются классы из файла api_errors.py
\data 2022.03.12
"""
import json
from typing import Optional

from pydantic import BaseModel, Field
from pydantic.main import create_model

from configurator.logger.logger import logger
from configurator.responses_models.market_models import AssetLabel, Market
from configurator.api.utils import check_dict_to_missing_fields, check_dict_to_unexpected_fields


# Класс для описания одного шага Торгового маршрута
# source_asset: str - Ассет, который нужен для выполнения операции
# common_symbol: str - Название торговой пары (маркета)
# operation: str - Указание, нужно произвести покупку или продажу с торговой парой (маркетом), "buy" или "sell"
class RouteStep(BaseModel):
    source_asset: str | None
    common_symbol: str
    operation: str


class HeaderReponseFormat(BaseModel):
    exchange: Optional[str]
    node: Optional[str]
    instance: Optional[str]
    algo: Optional[str]


class ResponseFormat(HeaderReponseFormat):
    event: Optional[str]
    action: Optional[str]
    message: Optional[str]
    timestamp: Optional[int]


class ConfigsResponseData(BaseModel):
    markets: list[Market]
    assets_labels: list[AssetLabel]
    routes: list[list[RouteStep]]
    configs: dict


class ConfigsResponse(ResponseFormat):
    event = 'config'
    node = 'configurator'
    algo = 'spread_bot_cpp'
    data: Optional[ConfigsResponseData]

def init_response(path_to_header_file: str, default_header: dict):
    """Функция для получения основных полей response Configurator API и
    обработки недостающих полей в файле header.json

    :param default_header:
    :param path_to_header_file: путь к файлу json с оснонвыми полями для response. Обычно это файл header.json
    :param exchange_id: название биржи. Используется, если в header.json не выставлено значение.
    :param instance: название инстанса. Используется, если в header.json не выставлено значение.
    :return: модель pydantic. Используется потомок ConfigsResponse, с добавление новых полей.
    Если в файле нет новых полей, всё равно будет использоваться потомок, но
    поля будут соответствовать ConfigsResponse.
    """
    with open(f'{path_to_header_file}', 'r') as header_file:
        try:
            header_data: dict = json.load(header_file)
        except json.decoder.JSONDecodeError as e:
            logger.error(f'Error with decoding json {path_to_header_file}. Error: {e}')
            raise e

        response = ConfigsResponse(**header_data)

    if check_dict_to_missing_fields(header_data, ['exchange', 'node', 'instance', 'algo']):
        with open(f'{path_to_header_file}', 'w') as header_file:
            new_header = default_header
            for key, value in header_data.items():
                if key in new_header:
                    new_header[key] = value
            json.dump(HeaderReponseFormat(**new_header).dict(), header_file, indent=4)
    return response


# ЗАМОРОЖЕННЫЙ ФУНКЦИОНАЛ
# Функционал, позволяющий добавлять произвольные поля в header.json.
# Заморожен из-за того, что это нарушает статичность модели response для API.
# Что это значит: API не может быть уверено, какая модель используется в качестве response.
# Это возникает из-за того, что при получении произвольных полей динамически создается
# новая модель, потомок старой модели.
#
# Закомментированный ниже код ЗАМОРОЖЕН.
#
#
# class HeaderReponseFormat(BaseModel):
#     exchange: Optional[str]
#     node: Optional[str]
#     instance: Optional[str]
#     algo: Optional[str]
#
#     # Метод для создания потомка модели с добавлением новых полей
#     @classmethod
#     def with_fields(cls, **field_definitions):
#         return create_model('HeaderWithFields', __base__=cls, **field_definitions)
#
#
# def init_response(path_to_header_file: str, exchange_id: str, instance: str):
#     """Функция для получения основных полей response Configurator API и
#     обработки недостающих полей в файле header.json
#
#     :param path_to_header_file: путь к файлу json с оснонвыми полями для response. Обычно это файл header.json
#     :param exchange_id: название биржи. Используется, если в header.json не выставлено значение.
#     :param instance: название инстанса. Используется, если в header.json не выставлено значение.
#     :return: модель pydantic. Используется потомок ConfigsResponse, с добавление новых полей.
#     Если в файле нет новых полей, всё равно будет использоваться потомок, но
#     поля будут соответствовать ConfigsResponse.
#     """
#     with open(f'{path_to_header_file}', 'r') as header_file:
#         try:
#             header_data: dict = json.load(header_file)
#         except json.decoder.JSONDecodeError as e:
#             logger.error(f'Error with decoding json {path_to_header_file}. Error: {e}')
#             raise e
#
#         _response_model = ConfigsResponse.with_fields(**header_data)
#         response = _response_model(**header_data)
#
#     if check_dict_to_missing_fields(header_data, ['exchange', 'node', 'instance', 'algo']):
#         with open(f'{path_to_header_file}', 'w') as header_file:
#             json.dump(HeaderReponseFormat(**header_data).dict(), header_file, indent=4)
#     return response
