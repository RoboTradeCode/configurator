# Configurator
## Версия 1.1.3.1

[![Python](https://img.shields.io/badge/python-3.10.2-blue)](https://www.python.org/downloads/)
[![Linux](https://img.shields.io/badge/platform-linux-lightgrey)](https://ru.wikipedia.org/wiki/Linux)

Предназначен для предоставления гейтам и ядру конфигураций и информации о торгуемых рынках

Актуальный хост: `3.68.58.96`

Пример URL для подключения: 

- https://configurator.robotrade.io/binance/1
- https://configurator.robotrade.io/ping

Общее описание Configurator
--------

Программное обеспечение которое предназначено для обеспечения гейтов и ядер следующими данными:

 - информация о торгуемых ценных бумагах
 - рабочие конфигурации

Эндпоинты
--------

### Основной эндпоинт Configurator

Endpoint: `GET /{exchange_id}/{instance}`

Ответ: 

<details>
<summary><u>Развернуть JSON</u></summary>

```json
{
  "is_new": true,
  "data": {
    "markets": [
      {
        "exchange_symbol": "ETH-BTC",
        "price_increment": 0.25,
        "amount_increment": 0.0001,
        "common_symbol": "ETH/BTC",
        "assets": {
          "base": "ETH",
          "quote": "BTC"
        }
      },
      {
        "exchange_symbol": "fBTCUST",
        "price_increment": 0.25,
        "amount_increment": 0.0001,
        "common_symbol": "BTC/USDT",
        "assets": {
          "base": "BTC",
          "quote": "UST"
        }
      }
    ],
    "assets_labels": [
      {
        "exchange": "UST",
        "common": "USDT"
      },
      {
        "exchange": "BTC",
        "common": "BTC"
      }
    ],
    "routes": [
      [
        {
          "source_asset": "ETH",
          "common_symbol": "ETH/USDT",
          "operation": "sell"
        },
        {
          "source_asset": "USDT",
          "common_symbol": "BTC/USDT",
          "operation": "buy"
        },
        {
          "source_asset": "BTC",
          "common_symbol": "ETH/BTC",
          "operation": "buy"
        }
      ],
      [
        {
          "source_asset": "USDT",
          "common_symbol": "ETH/USDT",
          "operation": "buy"
        },
        {
          "source_asset": "ETH",
          "common_symbol": "ETH/BTC",
          "operation": "sell"
        },
        {
          "source_asset": "BTC",
          "common_symbol": "BTC/USDT",
          "operation": "sell"
        }
      ],
      [
        {
          "source_asset": "BTC",
          "common_symbol": "BTC/USDT",
          "operation": "sell"
        },
        {
          "source_asset": "USDT",
          "common_symbol": "ETH/USDT",
          "operation": "buy"
        },
        {
          "source_asset": "ETH",
          "common_symbol": "ETH/BTC",
          "operation": "sell"
        }
      ]
    ],
    "gate_config": {
      "exchange": {
        "name": "kucoin",
        "instance": 1
      },
      "account": {
        "api_key": "61d213fc48bacd88816474cc",
        "secret_key": "8dga8934-02b7-4b66-963e-18b413f4e6cb",
        "passphrase": "i1i1id04d0c"
      },
      "aeron": {
        "publishers": {
          "orderbook": {
            "channel": "aeron:udp?control=172.31.14.205:40456|control-mode=dynamic",
            "stream_id": 1001
          },
          "balance": {
            "channel": "aeron:udp?control=172.31.14.205:40456|control-mode=dynamic",
            "stream_id": 1002
          },
          "log": {
            "channel": "aeron:udp?endpoint=3.66.183.27:44444|control-mode=dynamic",
            "stream_id": 1001
          }
        },
        "subscribers": {
          "core": {
            "channel": "aeron:udp?endpoint=172.31.14.205:40457|control=172.31.14.205:40456",
            "stream_id": 1003
          }
        }
      }
    },
    "core_config": {
      "aeron": {
        "publishers": {
          "gateway": {
            "channel": "aeron:udp?control=172.31.14.205:40456|control-mode=dynamic",
            "stream_id": 1003
          },
          "metrics": {
            "channel": "aeron:udp?endpoint=3.66.183.27:44444",
            "stream_id": 1001
          },
          "log": {
            "channel": "aeron:udp?control=172.31.14.205:40456|control-mode=dynamic",
            "stream_id": 1005
          }
        },
        "subscribers": {
          "balance": {
            "channel": "aeron:udp?control-mode=manual",
            "destinations": [
              "aeron:udp?endpoint=172.31.14.205:40461|control=172.31.14.205:40456"
            ],
            "stream_id": 1002
          },
          "orderbooks": {
            "channel": "aeron:udp?control-mode=manual",
            "destinations": [
              "aeron:udp?endpoint=172.31.14.205:40458|control=172.31.14.205:40456",
              "aeron:udp?endpoint=172.31.14.205:40459|control=18.159.92.185:40456",
              "aeron:udp?endpoint=172.31.14.205:40460|control=54.248.171.18:40456"
            ],
            "stream_id": 1001
          }
        }
      }
    }
  }
}
```

</details>


Это основной эндпоинт Configurator, он предоставляет информацию о маркетах, ассетах, конфигурациях, а также торговые маршруты.

#### Примеры:

`https://configurator.robotrade.io/binance/1`

`https://configurator.robotrade.io/kucoin/1?only_new=false`

Подробное описание доступно в [Wiki](https://github.com/RoboTradeCode/configurator/wiki/%D0%9E%D1%81%D0%BD%D0%BE%D0%B2%D0%BD%D0%BE%D0%B9-%D1%8D%D0%BD%D0%B4%D0%BF%D0%BE%D0%B8%D0%BD%D1%82-Configurator).

### Ping

Endpoint: `GET /ping`

Ответ:

``` js
{
  "pong": true
}
```

Эндпоинт используется для пинга - проверки, работает Configurator или нет. Регулярно отправлять пинг не нужно, эндпоинт нужен только для проверок.

#### Примеры:

`https://configurator.robotrade.io/ping`

Описание также доступно в [Wiki](https://github.com/RoboTradeCode/configurator/wiki/%D0%AD%D0%BD%D0%B4%D0%BF%D0%BE%D0%B8%D0%BD%D1%82-ping).

Обобщенный алгоритм 
--------

Configurator реализует API, которые использует Агент для получения информации о торгуемых бумагах и конфигурации для работы гейта и шлюза.

Алгоритм работы можно представить так:

1. Агент совершает запрос к API конфигуратора
2. Конфигуратор получает данные из биржи, из конфигов, генерирует торговые маршруты
3. Конфигуратор отправляет JSON  с данными или с ошибкой.

Деплой на сервере
--------

[Описание процесса деплоя (ссылка на Wiki)](https://github.com/RoboTradeCode/configurator/wiki/%D0%94%D0%B5%D0%BF%D0%BB%D0%BE%D0%B9-%D0%BD%D0%B0-%D1%81%D0%B5%D1%80%D0%B2%D0%B5%D1%80%D0%B5).
