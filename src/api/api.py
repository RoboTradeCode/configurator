"""
\file api.py
\author github:khanbekov, telegram:qoddrysdaim
\brief В файле загружается конфигурация API, логгирования, создается инициализируется API и его эндпоинты
\data 2022.03.12
\version 1.1.3.1
"""
import asyncio
import json
import logging
import os.path
import time

import ccxt
import fastapi
import pydantic

from src.market_data_obtaining.markets import get_exchange_by_id, format_markets, format_assets_labels
from src.responses_models.api_errors import ExchangeNotFound, ConfigsNotFound, ConfigDecodeError, CCXTError, UnexpectedError
from src.responses_models.api_responses import MarketsResponseData, MarketsResponse
from src.responses_models.core_config import CoreConfig
from src.responses_models.gate_config import GateConfig
from src.market_data_obtaining.routes import construct_routes
from src.settings import ROUTE_ASSETS, PATH_TO_CONFIGS, LOGGING_CONFIG

# Конфигурация API
route_assets: list[str] = ROUTE_ASSETS
path_to_configs = PATH_TO_CONFIGS

# logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = fastapi.FastAPI()

# словарь для хранения времени последнего обновления конфигурации core и gate
# строится следующим образом:
# str - exchange_id + instance; Пример: binance1
# float - время изменения, os.path.getmtime()
# Значение в словаре обновляется при каждом запросе этих конфигов
configs_update_time_dict: dict[str, float] = {}


# Главный эндпоинт Configurator
# Возвращает данные, включая: список маркетов, ассетов, торговых маршрутов, конфигураций gate и core
# Для доступа к эндпоинту нужно указать название биржи и инстанс. Они соответствуют папкам конфигурации
# Вовзращает данные, только если они ещё не были получены (т.е., если ещё не было запроса на эти "биржа/инстанс") или
# если они обновились с момента последнего запроса.
# Чтобы получить данные вне зависимости от предыдущего условия, нужно указать параметр запроса ?only_update=False
@app.get('/{exchange_id}/{instance}', response_model=MarketsResponse)
async def get_markets(
        exchange_id: str,
        instance: str,
        only_new: bool | None = True) -> MarketsResponse | fastapi.responses.JSONResponse:
    logger.info(f'Получен новый запрос на endpoint /{exchange_id}/{instance}')

    # Попытка получить биржу по её названию (название должно соответствовать ccxt)
    exchange = get_exchange_by_id(exchange_id)

    # Если не удалось получить биржу по названию, возвращаю ошибку (response с ошибкой)
    if exchange is None:
        logger.warning(f"Биржи {exchange_id} нет в списках ccxt. Не удалось обработать запрос к /{exchange_id}/{instance}")
        raise ExchangeNotFound(exchange_id)

    # Удалось получить биржу, буду собирать данные, чтобы отправить JSON. Алгоритм загрузки данных:
    # 1. gate_config - конфигурация шлюза, по сути, просто читаем JSON из папки
    # 2. core_config - конфигурация ядра, по сути, просто читаем JSON из папки
    # 3. Проверка, были ли получены данные ранее, и обновлялись ли они с тех пор
    # 4. Загрузка all_markets - это все ассеты биржи. Не записывается в JSON, нужно для составления других полей
    # 5. Получение markets - это торговые пары, их ограничения и т.п. Составляются из all_markets
    # 6. Получение assets_labels - список из стандартных названий ассетов (ccxt) и названий на бирже
    # 7. Составление routes - списки маршрутов, образуются из списка markets по заданным ассетам
    # 8. Составление объекта MarketsResponse - он будет отправлен клиенту
    try:
        # 1. gate_config - конфигурация шлюза, по сути, просто читаем JSON из папки
        gate_config = GateConfig(
            **json.load(open(f'{path_to_configs}/{exchange_id}/{instance}/gate_config.json'))
        )
        # 2. core_config - конфигурация ядра, по сути, просто читаем JSON из папки
        core_config = CoreConfig(
            **json.load(open(f'{path_to_configs}/{exchange_id}/{instance}/core_config.json'))
        )

        configs_last_update_time = max(
            os.path.getmtime(f'{path_to_configs}/{exchange_id}/{instance}/gate_config.json'),
            os.path.getmtime(f'{path_to_configs}/{exchange_id}/{instance}/core_config.json')
        )

        # 3. Проверки, когда последний раз были обновлены конфиги
        # Условие: не отдавать конфиги, если они уже были получены ранее и не обновлялись с того момента.
        # Получаю, обновлялись ли конфиги с прошлого момента запроса (если это первый запрос, то True)
        is_configs_updated = configs_update_time_dict.get(exchange_id + instance, 0) < configs_last_update_time
        if is_configs_updated:
            # записываю время последнего обновления
            configs_update_time_dict[exchange_id + instance] = configs_last_update_time
        # Если запрос требует только обновленные данные, то возвращаю ответ, что новых данных нет.
        elif only_new:
            return fastapi.responses.JSONResponse(status_code=200, content={'is_new': False})

        logger.info(f'Конфиги для /{exchange_id}/{instance} загружены.')

        # 4. Загрузка all_markets - это все ассеты биржи. Не записывается в JSON, нужно для составления других полей
        all_markets: ccxt.Exchange.markets = exchange.load_markets()
        logger.info(f'Данные о бирже {exchange_id} загружены.')

        # 5. Получение markets - это ассеты, из ограничения и т.п. Составляются из all_markets
        markets = await format_markets(all_markets, exchange.precisionMode == ccxt.DECIMAL_PLACES)
        # 6. Получение assets_labels - список из стандартных названий ассетов (ccxt) и названий на бирже
        assets_labels = await format_assets_labels(all_markets)
        # 7. Составление routes - списки маршрутов, образуются из списка markets по заданным ассетам
        routes = construct_routes(markets, route_assets)

        # 8. Составление объекта MarketsResponse - он будет отправлен клиенту
        response = MarketsResponse(
            is_new=is_configs_updated,
            data=MarketsResponseData(
                markets=markets,
                assets_labels=assets_labels,
                routes=routes,
                gate_config=gate_config,
                core_config=core_config
            )
        )

        logger.info(f"Запрос к /{exchange_id}/{instance} обработан.")
        # Возвращаем ответ (то есть отправляем клиенту, который делал запрос к API)
        return response

    # Ошибка чтения JSON, не найден файл - скорее всего, нет конфигурации для биржи/инстанса
    except FileNotFoundError:
        logger.warning(f"Нет конфигурации для /{exchange_id}/{instance}.")
        raise ConfigsNotFound(exchange_id, instance)
    # Ошибка декодирования JSON - синтаксические ошибки внутри JSON конфигурации
    except json.decoder.JSONDecodeError:
        logger.warning(f"Ошибка внутри файлов конфигурации для /{exchange_id}/{instance}.")
        raise ConfigDecodeError(exchange_id, instance)
    # Ошибка декодирования JSON - несоответствие формата конфигурации (отсутствуют поля / неправильный тип)
    except pydantic.error_wrappers.ValidationError:
        logger.warning(f"Ошибка внутри файлов конфигурации для /{exchange_id}/{instance}.")
        raise ConfigDecodeError(exchange_id, instance)
    # Ошибки, связанные с ccxt - эта библиотека делает запрос к бирже для получения списка markets
    except ccxt.errors.BaseError as e:
        logger.warning(f"Не удалось получить данные для биржи, проблема с соединением")
        raise CCXTError(exchange_id, e)
    # Ошибки, которые не удалось обработать. Таких быть не должно.
    except Exception as e:
        logger.error("Неожиданное исключение во время обработки данных.", exc_info=True)
        raise UnexpectedError(exchange_id, e)


# Эндпоинт для пинга
# Возвращает тело запроса с полем {"pong": true}
@app.get('/ping')
async def get_ping():
    return {"pong": True}

if __name__ == "__main__":
    asyncio.run(get_markets('kucoin', '1'))