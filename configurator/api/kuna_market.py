from decimal import Decimal
from itertools import chain


def load_markets_from_kuna() -> dict:
    """
    Kuna markets structure
    {
        "id":                "btcusdt",  # ключ валютной пары
        "base_unit":         "btc",      # базовая валюта
        "quote_unit":        "usdt",     # валюта котировки
        "base_precision":    6,          # округление базовой валюты
        "quote_precision":   2,          # округление валюты котировки
        "display_precision": 1,          # точность для групировки ордеров в ордербуке
        "price_change":      -1.89       # изменение цены в % за 24 часа
    }

    CCXT market structure:
    {
        'id':       'btc',       // string literal for referencing within an exchange
        'code':     'BTC',       // uppercase unified string literal code the currency
        'name':     'Bitcoin',   // string, human-readable name, if specified
        'active':    true,       // boolean, currency status (tradeable and withdrawable)
        'fee':       0.123,      // withdrawal fee, flat
        'precision': 8,          // number of decimal digits "after the dot" (depends on exchange.precisionMode)
        'deposit':   true        // boolean, deposits are available
        'withdraw':  true        // boolean, withdraws are available
        'limits': {              // value limits when placing orders on this market
            'amount': {
                'min': 0.01,     // order amount should be > min
                'max': 1000,     // order amount should be < max
            },
            'withdraw': { ... }, // withdrawal limits
            'deposit': {...},
        },
        'networks': {...}        // network structures indexed by unified network identifiers (ERC20, TRC20, BSC, etc)
        'info': { ... },         // the original unparsed currency info from the exchange
    }
    """
    ...


def get_limits_from_order_book(order_book: dict) -> dict:
    """Get limits and precisions of market by order book values"""
    limits = {}


def get_increments_from_order_book(order_book: dict) -> (float, float):
    """Get price increment of market by order book values

    :return: price_increment, amount_increment
    """
    price_increment: Decimal = Decimal(0)
    amount_increment: Decimal = Decimal(0)
    last_price = Decimal(0)
    last_volume = Decimal(0)
    for price, volume in chain(order_book['bids'], order_book['asks']):
        price = Decimal(str(price))
        volume = Decimal(str(volume))
        current_price_increment = abs(price - last_price)
        if price_increment > current_price_increment or price_increment == 0:
            price_increment = current_price_increment
        current_amount_increment = abs(volume - last_volume)
        if amount_increment > current_amount_increment or amount_increment == 0:
            amount_increment = current_amount_increment
        last_volume = volume
        last_price = price
    return price_increment.__float__(), amount_increment.__float__()
