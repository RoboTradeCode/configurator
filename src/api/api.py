"""
\file api.py
\author github:khanbekov, telegram:qoddrysdaim
\brief В файле загружается конфигурация API, логгирования, создается инициализируется API и его эндпоинты
\data 2022.03.12
\version 1.1.3.1
"""
import json

import ccxt
import fastapi
import pydantic

from src.api.utils import get_dir_last_change_time, get_json_from_dir, get_micro_timestamp
from src.market_data_obtaining.markets import get_exchange_by_id, format_markets, format_assets_labels
from src.responses_models.api_errors import ExchangeNotFound, ConfigsNotFound, ConfigDecodeError, CCXTError, UnexpectedError
from src.responses_models.api_responses import ConfigsResponse, ConfigsResponseData
from src.market_data_obtaining.routes import construct_routes
from src.settings import PATH_TO_CONFIGS_FOLDER
from src.api.logger import logger

# Конфигурация API
path_to_configs_folder = PATH_TO_CONFIGS_FOLDER


# Создание приложения fastapi
app = fastapi.FastAPI()

# словарь для хранения времени последнего обновления конфигурации core и gate
# строится следующим образом:
# str - exchange_id + instance; Пример: binance1
# float - время изменения, os.path.getmtime()
# Значение в словаре обновляется при каждом запросе этих конфигов
configs_update_time_dict: dict[str, float] = {}


@app.get('/{exchange_id}/{instance}', response_model=ConfigsResponse)
async def get_markets(
        exchange_id: str,
        instance: str,
        only_new: bool | None = True) -> ConfigsResponse:
    """ Главный эндпоинт Configurator.
        Возвращает данные, включая: список маркетов, ассетов, торговых маршрутов, конфигураций gate и core
        Для доступа к эндпоинту нужно указать название биржи и инстанс. Они соответствуют папкам конфигурации.
        Возвращает данные, только если они ещё не были получены (т.е., если ещё не было запроса на эти "биржа/инстанс") или
        если они обновились с момента последнего запроса.
        Чтобы получить данные вне зависимости от предыдущего условия, нужно указать параметр запроса ?only_update=False

    :param exchange_id: название биржи (по ccxt).
    :param instance: название инстанса торгового сервера.
    :param only_new: по умолчанию True. Если True, возвращает данные только если есть изменения с последнего запроса.
    :return: ConfigsResponse - структура с конфигурацией для торгового сервера.
    """
    logger.info(f'Получен новый запрос на endpoint /{exchange_id}/{instance}')

    # Попытка получить биржу по её названию (название должно соответствовать ccxt)
    exchange = get_exchange_by_id(exchange_id)

    # Если не удалось получить биржу по названию, возвращаю ошибку (response с ошибкой)
    if exchange is None:
        logger.warning(f"Биржи {exchange_id} нет в списках ccxt. Не удалось обработать запрос к /{exchange_id}/{instance}")
        raise ExchangeNotFound(exchange_id)

    # Удалось получить биржу, буду собирать данные, чтобы отправить JSON. Алгоритм загрузки данных:
    # 1. Получение sections - чтение файлов JSON из соответствующей папки
    # 2. Получение ассетов для построения маршрутов (чтение из файла)
    # 3. Проверка, были ли получены данные ранее, и обновлялись ли они с тех пор
    # 4. Загрузка all_markets - это все ассеты биржи. Не записывается в JSON, нужно для составления других полей
    # 5. Получение markets - это торговые пары, их ограничения и т.п. Составляются из all_markets
    # 6. Получение assets_labels - список из стандартных названий ассетов (ccxt) и названий на бирже
    # 7. Составление routes - списки маршрутов, образуются из списка markets по заданным ассетам
    # 8. Составление объекта MarketsResponse - он будет отправлен клиенту
    try:
     
        # 1. Получение конфигурации для данного торгового сервера
        configs = get_json_from_dir(f'{path_to_configs_folder}/{exchange_id}/{instance}/sections/')

        # Получение времени последнего обновления конфигов
        configs_last_update_time = get_dir_last_change_time(f'{path_to_configs_folder}/{exchange_id}/{instance}')

        # 2. Получение ассетов для построения маршрутов (чтение из файла)
        traded_assets = []
        with open(f'{path_to_configs_folder}/{exchange_id}/{instance}/assets.txt') as assets:
            traded_assets = assets.read().replace('\n', '').split(', ')

        # 3. Проверки, когда последний раз были обновлены конфиги
        # Условие: не отдавать конфиги, если они уже были получены ранее и не обновлялись с того момента.
        # Получаю, обновлялись ли конфиги с прошлого момента запроса (если это первый запрос, то True)
        is_configs_updated = configs_update_time_dict.get(exchange_id + instance, 0) < configs_last_update_time
        if is_configs_updated:
            # записываю время последнего обновления
            configs_update_time_dict[exchange_id + instance] = configs_last_update_time
        # Если запрос требует только обновленные данные, то возвращаю ответ, что новых данных нет.
        elif only_new:
            return ConfigsResponse(
                exchange=exchange_id,
                instance=instance,
                message='There is no fresh configs.',
                timestamp=get_micro_timestamp()
            )
        logger.info(f'Конфиги для /{exchange_id}/{instance} загружены.')

        # 4. Загрузка all_markets - это все ассеты биржи. Не записывается в JSON, нужно для составления других полей
        all_markets: ccxt.Exchange.markets = exchange.load_markets()
        logger.info(f'Данные о бирже {exchange_id} загружены.')

        # 5. Получение markets - это ассеты, из ограничения и т.п. Составляются из all_markets
        markets = await format_markets(all_markets, exchange.precisionMode == ccxt.DECIMAL_PLACES, traded_assets)
        # 6. Получение assets_labels - список из стандартных названий ассетов (ccxt) и названий на бирже
        assets_labels = await format_assets_labels(all_markets, traded_assets)

        # 7. Составление routes - списки маршрутов, образуются из списка markets по заданным ассетам

        routes = construct_routes(markets, traded_assets)
        
        logger.info(f'Собраны все данные.')
        # 8. Составление объекта MarketsResponse - он будет отправлен клиенту
        response = ConfigsResponse(
            exchange=exchange_id,
            instance=instance,
            action='send_full_config',
            timestamp=get_micro_timestamp(),
            data=ConfigsResponseData(
                markets=markets,
                assets_labels=assets_labels,
                routes=routes,
                configs=configs
            )
        )
        logger.info(instance)
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
    except pydantic.error_wrappers.ValidationError as e:
        logger.warning(f"Ошибка внутри файлов конфигурации для /{exchange_id}/{instance}. Error: {e}")
        raise ConfigDecodeError(exchange_id, instance)
    # Ошибки, связанные с ccxt - эта библиотека делает запрос к бирже для получения списка markets
    except ccxt.errors.BaseError as e:
        logger.warning(f"Не удалось получить данные для биржи, проблема с соединением")
        raise CCXTError(exchange_id, e)
    # Ошибки, которые не удалось обработать. Таких быть не должно.
    except Exception as e:
        logger.error("Неожиданное исключение во время обработки данных.", exc_info=True)
        raise UnexpectedError(exchange_id, e)


@app.get('/ping')
async def get_ping():
    """ Эндпоинт для пинга API

    :return: Возвращает тело запроса с полем {"pong": true}
    """
    return {"pong": True}

