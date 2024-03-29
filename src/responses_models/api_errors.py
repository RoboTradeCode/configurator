"""
\file api_errors.py
\author github:khanbekov, telegram:qoddrysdaim
\brief В файле находятся классы исключений, которые может возвращать API
\data 2022.03.12
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
    def __init__(self, trade_server_name: str):
        self.status_code = 404
        self.detail = {
                "title": f'Конфигурация не найдена.',
                "detail": f'Не найдена конфигурация для «/{trade_server_name}».'
            }


# Класс исключения, не найден необходимый файл конфигурации для торгового сервера.
# Может быть возвращен API в качестве ответа
class FileNotFound(fastapi.HTTPException):
    # exchange_id: str - название биржи
    # instance: str - номер инстанса торговой системы
    def __init__(self, trade_server_name: str, filename: str):
        self.status_code = 500
        self.detail = {
                "title": f'Не найден необходимый файл «{filename}».',
                "detail": f'Не найден файл «{filename}» по пути «{trade_server_name}/{filename}».'
        }


# Класс исключения, проблема с чтением конфигурации core или gate.
# Если возникло это исключение, значит проблема с форматом конфига.
# Может быть возвращен API в качестве ответа
class JsonDecodeError(fastapi.HTTPException):
    def __init__(self, path_to_file: str):
        self.status_code = 500
        self.detail = {
                "title": f'Ошибка при получении данных.',
                "detail": f'Не удалось обработать конфигурацию. '
                          f'Пожалуйста, проверьте файл {path_to_file} на сервере.'
            }


# Класс исключения, проблема с чтением конфигурации core или gate.
# Если возникло это исключение, значит проблема с форматом конфига.
# Может быть возвращен API в качестве ответа
class ConfigDecodeError(fastapi.HTTPException):
    def __init__(self, trade_server_name: str):
        self.status_code = 500
        self.detail = {
                "title": f'Ошибка при получении данных.',
                "detail": f'Не удалось сформировать данные для '
                          f'«/{trade_server_name}».'
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