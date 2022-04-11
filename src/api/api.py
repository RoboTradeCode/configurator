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
from src.responses_models.api_responses import ConfigsResponse, ConfigsResponseData
from src.market_data_obtaining.routes import construct_routes
from src.settings import PATH_TO_CONFIGS_FOLDER, LOGGING_CONFIG

# Конфигурация API
path_to_configs_folder = PATH_TO_CONFIGS_FOLDER

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = fastapi.FastAPI()

# словарь для хранения времени последнего обновления конфигурации core и gate
# строится следующим образом:
# str - exchange_id + instance; Пример: binance1
# float - время изменения, os.path.getmtime()
# Значение в словаре обновляется при каждом запросе этих конфигов
configs_update_time_dict: dict[str, float] = {}

# Функци для получния конфигурации по торговому серверу
# path_to_configs: str - путь до конфига (абсолютный или относительный
# return dict - словарь с соответствием Имя_файла_конфига : Содержимое_файла
def get_configs(path_to_configs: str) -> dict:
    # Получение списка файлов в папке с конфигами (нужно для названий секций)
    files: list = os.listdir(path_to_configs)

    # Чтение файлов для получения конфигурации
    files_content: lsit = []
    for file_name in files:
        try: 
            current_file_content: dict = json.load(open(f'{path_to_configs}{file_name}'))
            # Проверка на пустоту (пустой dict интерпретируется как false) 
            if current_file_content:
                logger.error(f'Файл конфигурации {file_name} пустой.')
            files_content.append(current_file_content)
        except Exception as e: 
            logger.error(f'Не удалось получить конфигурацию {file_name}. Error: {e}')
        
    # Создание словаря с соответствием Название секции : Содержимое соответствующего JSON
    configs = dict(zip([os.path.splitext(file)[0] for file in files], files_content))
    
    return configs 

# Функция для получения текущего timestamp в микросекундах
# return int - timestamp в микросекундах
def get_micro_timestamp() -> int:
    return round(time.time() * 1000000)

# Главный эндпоинт Configurator
# Возвращает данные, включая: список маркетов, ассетов, торговых маршрутов, конфигураций gate и core
# Для доступа к эндпоинту нужно указать название биржи и инстанс. Они соответствуют папкам конфигурации
# Вовзращает данные, только если они ещё не были получены (т.е., если ещё не было запроса на эти "биржа/инстанс") или
# если они обновились с момента последнего запроса.
# Чтобы получить данные вне зависимости от предыдущего условия, нужно указать параметр запроса ?only_update=False
@app.get('/{exchange_id}/{instance}', response_model=ConfigsResponse)
async def get_markets(
        exchange_id: str,
        instance: str,
        only_new: bool | None = True) -> ConfigsResponse:
    logger.info(f'Получен новый запрос на endpoint /{exchange_id}/{instance}')

    # Попытка получить биржу по её названию (название должно соответствовать ccxt)
    exchange = get_exchange_by_id(exchange_id)

    # Если не удалось получить биржу по названию, возвращаю ошибку (response с ошибкой)
    if exchange is None:
        logger.warning(f"Биржи {exchange_id} нет в списках ccxt. Не удалось обработать запрос к /{exchange_id}/{instance}")
        raise ExchangeNotFound(exchange_id)

    # Удалось получить биржу, буду собирать данные, чтобы отправить JSON. Алгоритм загрузки данных:
    # 1. Получение sections - чтение файлов JSON из соответствующей папки
    # 2. Проверка, были ли получены данные ранее, и обновлялись ли они с тех пор
    # 3. Загрузка all_markets - это все ассеты биржи. Не записывается в JSON, нужно для составления других полей
    # 4. Получение markets - это торговые пары, их ограничения и т.п. Составляются из all_markets
    # 5. Получение assets_labels - список из стандартных названий ассетов (ccxt) и названий на бирже
    # 6. Получение ассетов для построения маршрутов (чтение из файла)
    # 7. Составление routes - списки маршрутов, образуются из списка markets по заданным ассетам
    # 8. Составление объекта MarketsResponse - он будет отправлен клиенту
    try: 
        # Путь до файлов с конфигурацией
        path_to_current_configs = f'{path_to_configs_folder}/{exchange_id}/{instance}/sections/'
     
        # 1. Получение конфигурации для данного торгового сервеа
        configs = get_configs(path_to_current_configs)

        # Получение времени последнего обновления конфигов
        configs_last_update_time = os.path.getmtime(path_to_current_configs + '../../')
        

        # 2. Проверки, когда последний раз были обновлены конфиги
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

        # 3. Загрузка all_markets - это все ассеты биржи. Не записывается в JSON, нужно для составления других полей
        all_markets: ccxt.Exchange.markets = exchange.load_markets()
        logger.info(f'Данные о бирже {exchange_id} загружены.')

        # 4. Получение markets - это ассеты, из ограничения и т.п. Составляются из all_markets
        markets = await format_markets(all_markets, exchange.precisionMode == ccxt.DECIMAL_PLACES)
        # 5. Получение assets_labels - список из стандартных названий ассетов (ccxt) и названий на бирже
        assets_labels = await format_assets_labels(all_markets)
        
        # 6. Получение ассетов для построения маршрутов (чтение из файла)
        route_assets = []
        with open(f'{path_to_configs_folder}/{exchange_id}/{instance}/assets.txt') as assets:
            route_assets = assets.read().replace('\n', '').split(', ')
        # 7. Составление routes - списки маршрутов, образуются из списка markets по заданным ассетам

        routes = construct_routes(markets, route_assets)
        
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


# Эндпоинт для пинга
# Возвращает тело запроса с полем {"pong": true}
@app.get('/ping')
async def get_ping():
    return {"pong": True}

if __name__ == "__main__":
    asyncio.run(get_markets('kucoin', '1'))
