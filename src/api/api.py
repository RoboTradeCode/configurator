"""
\file api.py
\author github:khanbekov, telegram:qoddrysdaim
\brief В файле загружается конфигурация API, логгирования, создается инициализируется API и его эндпоинты
\data 2022.03.12
"""
import json
import os.path
import typing

import ccxt
import fastapi
from fastapi.responses import JSONResponse
import tomli as tomli

from src.api.utils import get_jsons_from_dir, get_micro_timestamp, check_update_of_dir
from src.logger.logger import logger
from src.market_data_obtaining.markets import get_exchange_by_id, check_existence_of_exchange, format_markets, \
    format_assets_labels
from src.market_data_obtaining.routes import construct_routes
from src.responses_models.api_errors import ExchangeNotFound, ConfigsNotFound, FileNotFound, JsonDecodeError
from src.responses_models.api_responses import ConfigsResponse, ConfigsResponseData, init_response
from src.settings import PATH_TO_TRADE_SERVERS_CONFIGS, API_CONFIGURATION_PATH

# Путь до директории с конфигурациями торговых серверов
path_to_trade_servers_configs = PATH_TO_TRADE_SERVERS_CONFIGS

# Создание приложения fastapi
app = fastapi.FastAPI()

# словарь для хранения времени последнего обновления конфигурации core и gate
# строится следующим образом:
# str - exchange_id + instance; Пример: binance1
# float - время изменения, os.path.getmtime()
# Значение в словаре обновляется при каждом запросе этих конфигов
configs_update_time_dict: dict[str, float] = {}


class IndentedEncoder(JSONResponse):
    def render(self, content: typing.Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=4,
            separators=(",", ":"),
        ).encode("utf-8")


@app.get('/{exchange_id}/{instance}', response_model=ConfigsResponse, response_class=IndentedEncoder)
async def endpoint_get_configs(
        exchange_id: str,
        instance: str,
        only_new: bool | None = True) -> ConfigsResponse:
    """ Главный эндпоинт Configurator.
        Возвращает данные, включая: список маркетов, ассетов, торговых маршрутов,
        конфигураций gate и core.
        Для доступа к эндпоинту нужно указать название биржи и инстанс.
        Они соответствуют папкам конфигурации.
        Возвращает данные, только если они ещё не были получены
        (т.е., если ещё не было запроса на эти "биржа/инстанс") или
        если они обновились с момента последнего запроса.
        Чтобы получить данные вне зависимости от предыдущего условия,
        нужно указать параметр запроса ?only_update=False

    :param exchange_id: название биржи (по ccxt).
    :param instance: название инстанса торгового сервера.
    :param only_new: по умолчанию True. Если True, возвращает данные только
    если есть изменения с последнего запроса.
    :return: ConfigsResponse - структура с конфигурацией для торгового сервера.
    """

    # Загрузка конфигурации для этого эндпоинта
    with open(API_CONFIGURATION_PATH, "rb") as f:
        api_configuration = tomli.load(f)

    default_header = {
        'exchange': exchange_id,
        'node': api_configuration["data"]["default"]["node"],
        'algo': api_configuration["data"]["default"]["algo"],
        'instance': instance,
    }

    # Имя файла со списком ассетов
    assets_filename = api_configuration["data"]["assets_filename"]
    # Имя файла с описанием основных полей response
    header_filename = api_configuration["data"]["header_filename"]
    # Название торгового сервера (exchange_id/instance)
    trade_server_name = f'{exchange_id}/{instance}'
    # Путь к конфигурации конкретного торгового сервера
    path_to_config = f'{path_to_trade_servers_configs}/{trade_server_name}'

    logger.info(f'Получен новый запрос на endpoint /{trade_server_name}')

    # Проверка, доступна ли такая биржа в списках ccxt
    is_exchange_existence = check_existence_of_exchange(exchange_id)

    # Если биржи нет в списках, возвращаю ответ с сообщением об этом
    if not is_exchange_existence:
        logger.error(f"Биржи {exchange_id} нет в списках CCXT."
                     f"е удалось обработать запрос к /{trade_server_name}")
        raise ExchangeNotFound(exchange_id)

    # Проверка, существует ли директория для этого торгового сервера (предусловие get_dir_last_change_time())
    if not os.path.isdir(path_to_config):
        # Возвращаю ответ, что конфигурации для такого торгового сервера нет.
        logger.error(f"Не найдена конфигурация для {trade_server_name}.")
        raise ConfigsNotFound(path_to_config)

    # Проверка, есть ли список ассетов для это торгового сервера
    if not os.path.isfile(f'{path_to_config}/{assets_filename}'):
        # Возвращаю ответ, что для сервера отсутствуют ассеты.
        logger.error(f'Не найден файл {assets_filename} для {trade_server_name}.')
        raise FileNotFound(trade_server_name, assets_filename)

    # Проверка, есть ли файл с описанием полей response для торгового сервера (если нет, создаю его)
    if not os.path.isfile(f'{path_to_config}/{header_filename}'):
        # Автоматически создаю и заполняю файл с описанием полей response, содержащий информацию о полях response
        with open(f'{path_to_config}/{header_filename}', 'w') as header_file:
            json.dump(default_header, header_file, indent=4)

        # Уведомляю, что у торгового сервера нет файла с описанием полей response и он создан автоматически.
        logger.warning(f"Не найден файл {header_filename} для {trade_server_name}. Он был и заполнен автоматически.")

    # Проверка, есть ли обновления конфигурации (обновилась ли с последнего запроса)
    is_configs_updated = check_update_of_dir(path_to_config)

    try:
        # Все необходимые проверки пройдены, создаю объект response API
        response: ConfigsResponse = init_response(f'{path_to_config}/{header_filename}', default_header)
    except json.decoder.JSONDecodeError:
        raise JsonDecodeError(f'{path_to_config}/{header_filename}')

    response.event = api_configuration['endpoint']['main']['event']
    response.timestamp = get_micro_timestamp()

    # Если конфигурация обновилась, или можно вернуть не обновленную конфигурацию, собираю данные для ответа
    if is_configs_updated or not only_new:
        try:
            response.data = await collect_configs_data(exchange_id, path_to_config, assets_filename)
        except JsonDecodeError as e:
            raise e

        response.message = api_configuration['endpoint']['main']['fresh']['message']
        response.action = api_configuration['endpoint']['main']['fresh']['action']
        logger.info(f'Собраны все данные.')

    # Если нужно вернуть свежую конфигурацию, но свежей конфигурации нет
    else:
        response.data = None
        response.message = api_configuration['endpoint']['main']['no_fresh']['message']
        response.action = api_configuration['endpoint']['main']['fresh']['action']
        logger.info(f'Нет обновлений в конфигурации.')

    # Возвращаю ответ на запрос
    return response


async def collect_configs_data(exchange_id: str, path_to_config: str, assets_filename: str) -> ConfigsResponseData:
    """ Функция собирает данные для эндпоинта /<exchange_id>/<instance>

    Предусловие: биржа exchange_id существует, и доступна через CCXT
    Предусловие: директорий, указанная в path_to_config существует и содержит необходимые данные

    Алгоритм загрузки данных:
        1. Чтение файла assets.txt для получения списка ассетов, которые нужно обрабатывать
        2. Получение данных о маркетах биржи с помощью CCXT
        3. Заполнение объектов markets с информацией о маркетах на бирже
        4. Заполнение объектов assets_labels со списком названий ассетов (стандартное название / название на бирже)
        5. Составление routes - списки маршрутов по заданным ассетам
        6. Получение configs - файлы JSON, находящиеся в директории внутри конфигурации торгового сервера
        7. Объединяю собранные данные в один объект ConfigsResponseData
        8. Возвращение ответа с данными для response

    :param assets_filename: название файла, в котором находится список ассетов.
    :param path_to_config: путь до директории конфигурации торгового сервера (формат <exchange_id>/<instance>/)
    :param exchange_id: название биржи по ccxt
    :return: заполненный объект ConfigsResponseData, содержащий данные для response
    """
    # 1. Чтение файла assets.txt для получения списка ассетов, которые нужно обрабатывать
    with open(f'{path_to_config}/{assets_filename}') as assets:
        traded_assets = assets.read().replace('\n', '').split(', ')

    # 2. Загрузка данных о маркетах биржи с помощью CCXT
    exchange = get_exchange_by_id(exchange_id)
    all_markets: ccxt.Exchange.markets = exchange.load_markets()
    logger.info(f'Загружены данные о бирже {exchange_id}.')

    # 3. Заполнение объектов markets с информацией о маркетах на бирже
    markets = await format_markets(all_markets, exchange.precisionMode == ccxt.DECIMAL_PLACES, traded_assets)

    # 4. Заполнение объектов assets_labels со списком названий ассетов (стандартное название / название на бирже)
    assets_labels = await format_assets_labels(all_markets, traded_assets)

    # 5. Составление routes - списки маршрутов по заданным ассетам
    routes = construct_routes(markets, traded_assets)
    logger.info(f'Данные о бирже форматированы и построены торговые маршруты.')

    # 6. Получение configs - файлы JSON, находящиеся в директории внутри конфигурации торгового сервера
    configs = get_jsons_from_dir(f'{path_to_config}/sections/')


    logger.info(f'Файлы из папки {path_to_config}/sections/ загружены.')

    # 7. Объединяю собранные данные в один объект ConfigsResponseData
    result = ConfigsResponseData(
            markets=markets,
            assets_labels=assets_labels,
            routes=routes,
            configs=configs
        )

    # 7. Возвращение ответа с данными для response
    return result


@app.get('/ping')
async def get_ping():
    """ Эндпоинт для пинга API

    :return: Возвращает тело запроса с полем {"pong": true}
    """
    return {"pong": True}


    # # Ошибка чтения JSON, не найден файл - скорее всего, нет конфигурации для биржи/инстанса
    # except FileNotFoundError:
    #     logger.warning(f"Нет конфигурации для /{exchange_id}/{instance}.")
    #     raise ConfigsNotFound(exchange_id, instance)
    # # Ошибка декодирования JSON - синтаксические ошибки внутри JSON конфигурации
    # except json.decoder.JSONDecodeError:
    #     logger.warning(f"Ошибка при декодировании JSON для /{exchange_id}/{instance}.")
    #     raise JsonDecodeError(exchange_id, instance)
    # # Ошибка декодирования JSON - несоответствие формата конфигурации (отсутствуют поля / неправильный тип)
    # except pydantic.error_wrappers.ValidationError as e:
    #     logger.warning(f"Ошибка при формировании данных для /{exchange_id}/{instance}. Error: {e}")
    #     raise ConfigDecodeError(exchange_id, instance)
    # # Ошибки, связанные с ccxt - эта библиотека делает запрос к бирже для получения списка markets
    # except ccxt.errors.BaseError as e:
    #     logger.warning(f"Не удалось получить данные для биржи, проблема с соединением")
    #     raise CCXTError(exchange_id, e)
    # # Ошибки, которые не удалось обработать. Таких быть не должно.
    # except Exception as e:
    #     logger.error("Неожиданное исключение во время обработки данных.", exc_info=True)
    #     raise UnexpectedError(exchange_id, e)

