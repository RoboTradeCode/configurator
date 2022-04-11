"""
\file markets.py
\author github:khanbekov, telegram:qoddrysdaim
\brief В файле находятся функции для получения информации от бирж
\data 2022.03.12
\version 1.1.3.1

Для получения данных используется библиотека ccxt
Для хранения структурированных данных используется библиотека pydantic
"""

import ccxt

import src.responses_models.market_models as market_models


def convert_precision(precision: int) -> float:
    """Функция конвертирует int знаков после запятой в float,
    т.е. конвертирует 3 -> 0.001, 1 -> 0.1

    :param precision: int - точность, которую нужно конвертировать
    :return: float - преобразованная точность, в виде float
    """
    return float('0.' + '0' * (precision - 1) + '1')


async def format_assets_labels(markets: ccxt.Exchange.markets, chosen_assets: list[str]) \
        -> list[market_models.AssetLabel]:
    """ Функция форматирует список markets, который возвращает ccxt, в список названий ассетов
    Если markets пустой, возвращается пустой список. Данные внутри списка ассетов не повторяются.

    :param markets: ccxt.Exchange.markets - список маркетов в том виде, в котором их дает ccxt
    :param chosen_assets: выбранные ассеты. Только они будут добавлены в возвращаемый массив.
    :return: список названий ассетов, т.е. стандартное название и название на бирже
    """
    if markets is None:
        return []

    results: list[market_models.AssetLabel] = []

    # список уже добавленных активов
    added: list[str] = []

    # В цикле перебираются все элементы markets - каждый из них это валютная пара с двумя ассетами
    for market in markets.values():
        # Проверяю, нужно ли мне обрабатывать этот ассет (есть ли он среди выбранных)
        if market['baseId'] in chosen_assets and \
                market['quoteId'] in chosen_assets:
            # проверяю, обрабатывал ли я базовый ассет
            if market['baseId'] not in added:
                # добавляю ассет в списки добавленных ассетов и итоговый список
                added.append(market['baseId'])
                results.append(
                    market_models.AssetLabel(
                        exchange=market['baseId'],
                        common=market['base']
                    )
                )
            # проверяю, обрабатывал ли я котируемый ассет
            if market['quoteId'] not in added:
                # добавляю ассет в списки добавленных ассетов и итоговый список
                added.append(market['quoteId'])
                results.append(
                    market_models.AssetLabel(
                        exchange=market['quoteId'],
                        common=market['quote']
                    )
                )

    return results


async def format_markets(markets: ccxt.Exchange.markets, is_decimal_precision: bool, chosen_assets: list[str]) \
        -> list[market_models.Market]:
    """Функция форматирует список markets, который возвращает ccxt, в список объектов Market
    Основная задача - отбрасывание лишних данных, в объекты Market добавляются только нужные.
    Отбрасываются все ассеты, не указанные в choset_assets

    :param markets: ccxt.Exchange.markets - список маркетов в том виде, в котором их дает ccxt
    :param is_decimal_precision: bool - нужно ли конвертировать точность из int в float
    :param chosen_assets: list[str] - выбранные ассеты. Только они будут добавлены в возвращаемый массив.
    :return: list[market_models.Market] - список объектов Market, полученный из markets
    """
    if markets is None:
        return []

    results: list[market_models.Market] = []

    # В цикле перебираются все элементы markets
    for market in markets.values():
        # Проверяю, нужно ли мне обрабатывать этот ассет (есть ли он среди выбранных)
        if market['baseId'] in chosen_assets and \
                market['quoteId'] in chosen_assets:
            # в итоговый список добавляются объекты Market, собранные из данных списка markets
            results.append(
                market_models.Market(
                    exchange_symbol=market['id'],
                    common_symbol=market['symbol'],
                    # точность и округление: принятым форматом является float.
                    # если точность представлена в виде int (кол-во знаков после запятой), конвертирую
                    price_increment=(
                        convert_precision(market['precision']['price'])
                        if is_decimal_precision
                        else market['precision']['price']
                    ),
                    # точность и округление: принятым форматом является float.
                    # если точность представлена в виде int (кол-во знаков после запятой), конвертирую
                    amount_increment=(
                        convert_precision(market['precision']['amount'])
                        if is_decimal_precision
                        else market['precision']['amount']
                    ),
                    base_asset=market['baseId'],
                    quote_asset=market['quoteId']
                )
            )

    return results


def get_exchange_by_id(exchange_id: str, config: dict = None) -> ccxt.Exchange:
    """Функция для получения объекта биржи ccxt по названию биржи
    Если биржу не удалось найти, возвращает None

    :param exchange_id: str - название биржи (примеры: binance, okx, kucoin)
    :param config: dict - конфигурация, с которой будет создан объект биржи ccxt
    :return: ccxt.Exchange - объект биржи ccxt, можно использовать его методы, предоставленные библиотекой ccxt
    """
    if config is None:
        config = {}

    # получаю биржу из ccxt по её названию (exchange_id)
    exchange = getattr(ccxt, exchange_id, None)
    # если удалось получить биржу
    if exchange is not None:
        exchange = exchange(config)
    return exchange
