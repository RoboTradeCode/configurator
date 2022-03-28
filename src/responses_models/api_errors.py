"""
\file api_errors.py
\author github:khanbekov, telegram:qoddrysdaim
\brief В файле находятся классы исключений, которые может возвращать API
\data 2022.03.12
\version 1.0.1
"""
import fastapi


# Класс исключения, биржа не найдена.
# Может быть возвращен API в качестве ответа
class ExchangeNotFound(fastapi.HTTPException):
    # exchange_id: str - название биржи
    def __init__(self, exchange_id: str):
        self.status_code = 404
        self.detail = {
                "title": "Биржа не найдена",
                "detail": f'Биржа «{exchange_id}» не найдена в списке бирж, поддерживаемых ccxt. '
                          f'Пожалуйста, проверьте, указан ли правильный exchange id из списка: '
                          f'https://github.com/ccxt/ccxt/wiki/Exchange-Markets'
            }


# Класс исключения, не найдена конфигурация для core и/или gate.
# Может быть возвращен API в качестве ответа
class ConfigsNotFound(fastapi.HTTPException):
    # exchange_id: str - название биржи
    # instance: str - номер инстанса торговой системы
    def __init__(self, exchange_id: str, instance: str):
        self.status_code = 404
        self.detail = {
                "title": f'Конфигурация ен найдена.',
                "detail": f'Не найдена конфигурация для gate или core «/{exchange_id}/{instance}».'
            }


# Класс исключения, проблема с чтением конфигурации core или gate.
# Если возникло это исключение, значит проблема с форматом конфига.
# Может быть возвращен API в качестве ответа
class ConfigDecodeError(fastapi.HTTPException):
    def __init__(self, exchange_id: str, instance: str):
        self.status_code = 500
        self.detail = {
                "title": f'Проблема при чтении конфигурации.',
                "detail": f'Не удалось обработать конфигурацию для «/{exchange_id}/{instance}». '
                          f'Пожалуйста, проверьте формат конфигурации на сервере.'
            }


# Класс исключения, при ошибке во время получения данных о бирже. Исключение возникает в ccxt.
# Может быть возвращен API в качестве ответа
class CCXTError(fastapi.HTTPException):
    def __init__(self, exchange_id: str, exception: Exception):
        self.status_code = 502
        self.detail = {
                "title": f'Не удалось загрузить маркеты.',
                "detail": f'Не удалось загрузить маркеты для биржи «{exchange_id}». Ошибка:' + str(exception)
            }


# Класс исключения, при неожиданном исключении во время обработки запроса.
# Может быть возвращен API в качестве ответа.
# Никогда не должен быть возвращен.
class UnexpectedError(fastapi.HTTPException):
    def __init__(self, exchange_id: str, exception: Exception):
        self.status_code = 500
        self.detail = {
                "title": f'Неожиданная ошибка.',
                "detail": f'Неожиданная ошибка при обработке биржи «{exchange_id}». '
                          f'Ошибка:' + str(exception)
            }