from configurator.api.limits_by_order_book import get_min_max_limits, \
    OrderBook, get_price_increment, get_amount_increment, get_min_increment, OrderLimits, Limits, get_limits

order_book = OrderBook(
    bids=[
        [100, 100],
        [90, 90],
        [89.8, 1],
    ],
    asks=[
        [105, 52.5],
        [108, 400],
        [115, 54],
    ]
)


def test_get_limits():
    expected = Limits(
        price_increment=0.2,
        amount_increment=1.5,
        limits=OrderLimits(
            amount=OrderLimits.MinMax(
                min=1,
                max=400
            ),
            price=OrderLimits.MinMax(
                min=89.8,
                max=115
            ),
            cost=OrderLimits.MinMax(
                min=89.8,
                max=43200
            ),
            leverage=OrderLimits.MinMax(),
        )
    )
    assert get_limits(order_book) == expected


def test_get_min_max_limits():
    expected = OrderLimits(
        amount=OrderLimits.MinMax(
            min=1,
            max=400
        ),
        price=OrderLimits.MinMax(
            min=89.8,
            max=115
        ),
        cost=OrderLimits.MinMax(
            min=89.8,
            max=43200
        ),
        leverage=OrderLimits.MinMax(),
    )
    assert get_min_max_limits(order_book) == expected


def test_get_price_increment():
    assert get_price_increment(order_book) == 0.2


def test_get_amount_increment():
    assert get_amount_increment(order_book) == 1.5


def test_get_min_increment_1():
    assert get_min_increment([1, 3, 5, 7, 8, 9, 14, 16]) == 1


def test_get_min_increment_2():
    assert get_min_increment([1, 3, 5, 7, 9]) == 2


def test_get_min_increment_3():
    assert get_min_increment([10, 11, 11.5, 12.5, 14]) == 0.5
