import asyncio
from typing import Tuple, Any

import ccxt
import ccxtpro

from configurator.api.limits_by_order_book import get_limits, OrderBook
from configurator.api.utils import get_jsons_from_dir
from configurator.logger.logger import logger
from configurator.market_data_obtaining.markets import get_exchange_by_id, format_markets, format_assets_labels
from configurator.market_data_obtaining.routes import construct_routes
from configurator.responses_models.api_responses import ConfigsResponseData
from configurator.responses_models.market_models import Market


async def collect_configs_data(exchange_id: str, path_to_config: str, assets_filename: str,
                               routes_max_length: int = 3, limits_by_order_book: bool = False) -> ConfigsResponseData:
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

    :param assets_filename: название файла, в котором находится список ассетов;
    :param path_to_config: путь до директории конфигурации торгового сервера (формат <exchange_id>/<instance>/);
    :param exchange_id: название биржи по ccxt;
    :param routes_max_length: максимальная длина роуто;
    :param limits_by_order_book: нужно ли уточнять значения ограничения с помощью ордер-буков;
    :return: заполненный объект ConfigsResponseData, содержащий данные для response
    """
    # 1. Чтение файла assets.txt для получения списка ассетов, которые нужно обрабатывать
    with open(f'{path_to_config}/{assets_filename}') as assets:
        traded_assets = assets.read().replace('\n', '').split(', ')

    # 2. Загрузка данных о маркетах биржи с помощью CCXT
    exchange = get_exchange_by_id(exchange_id)
    if exchange_id == 'bybit':
        all_markets_list: ccxt.Exchange.markets = exchange.fetch_spot_markets({})
        all_markets = {market['symbol']: market for market in all_markets_list}
    elif exchange_id == 'kuna':
        all_markets: ccxt.Exchange.markets = exchange.load_markets({'version': '3'})
    else:
        all_markets: ccxt.Exchange.markets = exchange.load_markets()
    logger.info(f'Загружены данные о бирже {exchange_id}.')

    # 3. Заполнение объектов markets с информацией о маркетах на бирже
    markets = await format_markets(all_markets, exchange.precisionMode == ccxt.DECIMAL_PLACES, traded_assets)

    if limits_by_order_book:
        markets = await refine_limits(exchange_id=exchange_id, markets=markets)

    # 4. Заполнение объектов assets_labels со списком названий ассетов (стандартное название / название на бирже)
    assets_labels = await format_assets_labels(all_markets, traded_assets)

    # 5. Составление routes - списки маршрутов по заданным ассетам
    routes = construct_routes(markets, traded_assets, routes_max_length)
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


async def refine_limits(exchange_id: str, markets: list[Market]) -> list[Market | BaseException]:
    exchange = getattr(ccxtpro, exchange_id, None)()
    coroutines = [refine_limits_in_one_market(exchange, market) for market in markets]
    refined_markets = list(await asyncio.gather(*coroutines))
    await exchange.close()
    return refined_markets


async def refine_limits_in_one_market(exchange, market: Market) -> Market:
    order_book = await exchange.fetch_order_book(symbol=market.common_symbol)
    limits = get_limits(OrderBook(**order_book)).dict()
    return Market(**{**market.dict(), **{k: v for k, v in limits.items() if v}})


    # market.price_increment = limits.price_increment if market.price_increment is None else market.price_increment
    # market.amount_increment = limits.amount_increment if market.amount_increment is None else market.amount_increment
    #
    # market.limits.price.min = limits.limits.price.min if market.limits.price.min is None else market.limits.price.min
    # market.limits.price.max = limits.limits.price.max if market.limits.price.max is None else market.limits.price.max
    #
    # market.limits.amount.min = limits.limits.amount.min if market.limits.amount.min is None else market.limits.amount.min
    # market.limits.amount.max = limits.limits.amount.max if market.limits.amount.max is None else market.limits.amount.max
    #
    # market.limits.cost.min = limits.limits.cost.min if market.limits.cost.min is None else market.limits.cost.min
    # market.limits.cost.max = limits.limits.cost.max if market.limits.cost.max is None else market.limits.cost.max