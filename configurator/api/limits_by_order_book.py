import dataclasses
from dataclasses import dataclass
from decimal import Decimal
from itertools import chain
from typing import Optional

import datetime

from pydantic import BaseModel

from configurator.responses_models.market_models import Market


@dataclass(init=False)
class OrderBook:
    symbol: Optional[str]
    timestamp: Optional[int]
    datetime: Optional[datetime.datetime]
    bids: list[list[float]]
    asks: list[list[float]]

    def __init__(self, **kwargs):
        names = set([f.name for f in dataclasses.fields(self)])
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)


class Limits(BaseModel):
    amount_increment: float
    price_increment: float
    limits: Market.Limits


def get_limits(order_book: OrderBook) -> Limits:
    return Limits(
        amount_increment=get_amount_increment(order_book=order_book),
        price_increment=get_price_increment(order_book=order_book),
        limits=get_min_max_limits(order_book=order_book)
    )


def get_min_max_limits(order_book: OrderBook) -> Market.Limits:
    """Get limits of market by order book values
        {
            'amount': {'min': 1e-05, 'max': 1000000},
            'price': {'min': 0.1, 'max': 0.23},
            'cost': {'min': 10, 'max': 1000000}
        }
    :return: limits
    """
    order_books_rows = order_book.bids + order_book.asks
    result = Market.Limits(
        amount=Market.Limits.MinMax(
            min=min(order_books_rows, key=lambda x: x[1])[1],
            max=max(order_books_rows, key=lambda x: x[1])[1]
        ),
        price=Market.Limits.MinMax(
            min=min(order_books_rows, key=lambda x: x[0])[0],
            max=max(order_books_rows, key=lambda x: x[0])[0]
        ),
        cost=Market.Limits.MinMax(),
        leverage=Market.Limits.MinMax()
    )
    min_cost_row = min(order_books_rows, key=lambda x: x[0] * x[1])
    max_cost_row = max(order_books_rows, key=lambda x: x[0] * x[1])

    result.cost.min = min_cost_row[0] * min_cost_row[1]
    result.cost.max = max_cost_row[0] * max_cost_row[1]

    return result


def get_price_increment(order_book: OrderBook) -> float:
    """Get precisions of market by order book values
        {
            'price': 0.1
        }
    :return: price and amount precision
    """
    # get all prices from orderbook in ascending order
    order_book_prices = list(map(lambda x: x[0], order_book.bids[::-1] + order_book.asks))

    min_price_increment = get_min_increment(order_book_prices)

    return min_price_increment


def get_amount_increment(order_book: OrderBook) -> float:
    """Get precisions of market by order book values
        {
            'amount': 1e-08,
        }
    :return: price and amount precision
    """
    # get all amounts from orderbook in ascending order
    order_book_amounts = sorted(list(map(lambda x: x[1], order_book.bids + order_book.asks)))

    min_amount_increment = get_min_increment(order_book_amounts)

    return min_amount_increment


def get_min_increment(values: list[float]) -> float:
    last_value = Decimal(str(values[0]))
    min_increment: Decimal = Decimal(str("inf"))

    for price in values[1:]:
        price = Decimal(str(price))

        current_increment = abs(price - last_value)
        if current_increment != 0 and min_increment > current_increment:
            min_increment = current_increment

        last_value = price
    return min_increment.__float__()
