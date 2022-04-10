"""
\file routes.py
\author github:khanbekov, telegram:qoddrysdaim
\brief В файле находятся функции для построение торговых маршрутов
\data 2022.03.12
\version 1.0.1
"""
import itertools
from pprint import pprint

from src.responses_models.api_responses import RouteStep
from src.responses_models.market_models import Market


# Функция фильтрует маркеты, оставляет только те, в которых базовый и котируемый ассеты есть в списке assets.
# markets: list[Market] - список маркетов, который нужно отфильтровать
# assets: list[str] - список ассетов, по ним будет фильтроваться список маркетов
# return listlist[Market] - список отобранных маркетов
def select_markets_by_assets(markets: list[Market], assets: list[str]) -> list[Market]:
    result: list[Market] = []

    for market in markets:
        if market.base_asset in assets and market.quote_asset in assets:
            result.append(market)

    return result


# Функция переводит последовательность маркетов (пример торговой пары маркета: BTC/USDT) в торговый маршрут
# param route_sequence: list[list[str]] - последовательность торговый пар
# return list[list[str]] - получившийся торговый маршрут
# return bool - возможен ли торговый маршрут (обязательно к проверке в коде, использующем функцию)
def route_sequence_to_route(route_sequence: tuple[Market]) -> (list[RouteStep], bool):
    # 1. Нахожу, какой ассет будет первым
    # 2. Пытаюсь обменять ассеты в заданной последовательности
    # 3. Сверяю, совпадают ли первый и последний ассеты.
    # 4. Маршрут успешно построен, возвращаю результат

    # торговый маршрут, буду добавлять в этот список элементы
    result_route: list[RouteStep] = []
    # первый ассет, нужно вернуться к нему, пройдя весь маршрут
    first_asset: str
    # текущий ассет, указывает, какой ассет мне нужно обменять в текущий момент
    curr_asset: str

    # 1. Нахожу, какой ассет будет первым
    if route_sequence[0].base_asset in [route_sequence[-1].base_asset, route_sequence[-1].quote_asset]:
        first_asset = route_sequence[0].base_asset
    elif  route_sequence[0].quote_asset in [route_sequence[-1].base_asset, route_sequence[-1].quote_asset]:
        first_asset = route_sequence[0].quote_asset
    else:
        return result_route, False

    curr_asset = first_asset

    # 2. Пытаюсь обменять ассеты в заданной последовательности
    for market in route_sequence:
        if market.base_asset == curr_asset:
            result_route.append(RouteStep(
                source_asset=curr_asset,
                common_symbol=market.common_symbol,
                operation='sell')
            )
            curr_asset = market.quote_asset
        elif market.quote_asset == curr_asset:
            result_route.append(RouteStep(
                source_asset=curr_asset,
                common_symbol=market.common_symbol,
                operation='buy')
            )
            curr_asset = market.base_asset
        else:
            return result_route, False

    # 3. Сверяю, совпадают ли первый и последний ассеты.
    # Нужно получить тот ассет, который был изначально
    if first_asset != curr_asset:
        return result_route, False

    # 4. Маршрут успешно построен, возвращаю результат
    return result_route, True


# Функция строит торговые маршруты.
# Построенные маршруты это просто все варианты маршрутов, которые можно пройти. Прибыльность не анализируется.
# markets: list[Market] - список объектов Market, содержит данные о всех маркетах биржи
# assets: list[str] - список ассетов, по которым нужно строить торговые маршруты
# return list[tuple[RouteStep]] - список построенных маршрутов (каждый маршрут - tuple из объектов RouteStep)
def construct_routes(markets: list[Market], assets: list[str]) -> list[tuple[RouteStep]]:
    result: list[tuple[RouteStep]] = []

    # Выбираю маркеты (торговые пары), в которых участвуют ассеты
    selected_markets = select_markets_by_assets(markets, assets)

    route_number = itertools.count()
    # Перебираю длины путей, которые можно получить из ассетов.
    # Длина пути не может превышать длину списка ассетов, иначе ассеты будут повторяться
    for i in range(3, len(assets) + 1):
        # Перестановки маркетов (торговых пар) внутри последовательности
        for sequence in itertools.permutations(selected_markets, i):
            # Пробую преобразовать последовательность маркетов (торговых пар) в торговый маршрут
            route, is_valid_route = route_sequence_to_route(sequence)
            # Если удалось преобразовать, сохраняю полученный торговый маршрут
            if is_valid_route:
                result.append(route)

    return result
