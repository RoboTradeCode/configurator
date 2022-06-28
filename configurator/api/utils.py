"""
\file utils.py
\author github:khanbekov, telegram:qoddrysdaim
\brief В файле находятся вспомогательные функции, нужные для работы API
\data 2022.04.11
"""
import json
import os
import time
from typing import Any

from configurator.responses_models.api_errors import JsonDecodeError
from configurator.logger.logger import logger

# словарь для хранения времени последнего обновления конфигурации core и gate
# строится следующим образом:
# str - exchange_id + instance; Пример: binance1
# float - время изменения, os.path.getmtime()
# Значение в словаре обновляется при каждом запросе этих конфигов
dirs_times_of_update: dict[str, float] = {}


def check_update_of_dir(path_to_dir: str) -> bool:
    """ Функция для проверки, обновлялась ли директория с момента последней проверки.
    Директория считается обновленной, если внутри неё был изменен хотя бы один файл.
    При первой проверки директории всегда возвращает True.

    :param path_to_dir: Путь до директории, которую нужно проверить на обновления. Будет сохранен в функции.
    :return: bool - True, если хотя бы один файл обновился. False, если ни один файл не обновился.
    """

    dir_change_time = get_dir_last_change_time(path_to_dir)

    is_configs_updated = dirs_times_of_update.get(path_to_dir, 0) < dir_change_time
    if is_configs_updated:
        # записываю время последнего обновления
        dirs_times_of_update[path_to_dir] = dir_change_time

    return is_configs_updated


def get_dir_last_change_time(path_to_dir: str) -> float:
    """
    Функция рекурсивно обходит файлы и возвращает время
    последнего изменения среди файлов в директории и вложенных директориях.
    Если в папке нет файлов, будет возвращено значение -1

    Предусловие: директория path_to_dir существует.

    :param path_to_dir: str - название папки, с которой нужно начать обход файлов.
    :return: float - время последнего изменения среди файлов в директории и вложенных директориях
    """
    # переменная будет хранить время последнего изменения
    last_change_time: float = -1
    # начинаем обход директорий
    for root, dirs, files in os.walk(path_to_dir):
        for file in files:
            # получаем время последнего изменения файла
            file_last_change_time = os.path.getmtime(os.path.join(root, file))
            # сравниваем с временем предыдущего последнего изменения другого файла
            if last_change_time < file_last_change_time:
                last_change_time = file_last_change_time

    return last_change_time


def get_jsons_from_dir(path_to_dir: str) -> dict:
    """ Функции для получения содержимого файлов JSON внутри директории

    :param path_to_dir: str - путь до конфига (абсолютный или относительный)
    :return: dict - словарь с соответствием [Имя_файла : Содержимое_файла]
    """
    # Получение списка файлов в папке (нужно для названий в словаре)
    files: list = os.listdir(path_to_dir)

    # Чтение файлов json
    files_content: list = []
    for file_name in files:
        try:
            current_file_content: dict = json.load(open(f'{path_to_dir}{file_name}'))
            # Проверка на пустоту (пустой dict интерпретируется как false)
            if not current_file_content:
                logger.error(f'Файл {path_to_dir}{file_name} пустой.')
            files_content.append(current_file_content)
        except Exception as e:
            logger.error(f'Не удалось прочитать {path_to_dir}{file_name}. Error: {e}')
            raise JsonDecodeError(f'{path_to_dir}{file_name}')

    # Создание словаря с соответствием [Имя_файла : Содержимое_файла]
    result = dict(zip([os.path.splitext(file)[0] for file in files], files_content))

    return result


def get_micro_timestamp() -> int:
    """ Функция для получения текущего timestamp в микросекундах

    :return: int - timestamp в микросекундах
    """
    return round(time.time() * 1000000)


def check_dict_to_unexpected_fields(checking_dict: dict, expected_keys: list[str]) -> bool:
    """ Функция для проверки, есть ли в словаре не ожидаемые ключи (ключи, которых нет в expected_keys).

    :param checking_dict: словарь, который нужно проверить.
    :param expected_keys: ожидаемые ключи.
    :return: True, если есть хотя бы 1 не ожидаемый ключ в словаре.
    """
    for key in checking_dict.keys():
        if key not in expected_keys:
            return True


def check_dict_to_missing_fields(checking_dict: dict, expected_keys: list[str]) -> bool:
    """ Функция для проверки, есть ли в словаре отсутствующие ключи (ключи, которые есть в expected_keys).

    :param checking_dict: словарь, который нужно проверить.
    :param expected_keys: ожидаемые ключи.
    :return: True, если не хватает хотя бы 1 ключа в словаре.
    """
    for key in expected_keys:
        if key not in checking_dict.keys():
            return True


def get_precision(num: float) -> int:
    """Функция возвращает количество символов после запятой"""
    str_num = float_to_str(num)
    if '.' not in str_num:
        return 0

    # Получение строки после точки и возвращение ее длины
    return len(str_num[str_num.index('.') + 1:])


def float_to_str(f):
    float_string = repr(f)
    if 'e' in float_string:  # detect scientific notation
        digits, exp = float_string.split('e')
        digits = digits.replace('.', '').replace('-', '')
        exp = int(exp)
        zero_padding = '0' * (abs(int(exp)) - 1)  # minus 1 for decimal point in the sci notation
        sign = '-' if f < 0 else ''
        if exp > 0:
            float_string = '{}{}{}.0'.format(sign, digits, zero_padding)
        else:
            float_string = '{}0.{}{}'.format(sign, zero_padding, digits)
    return float_string


def convert_precision(precision: int) -> float:
    """Функция конвертирует int знаков после запятой в float,
    т.е. конвертирует 3 -> 0.001, 1 -> 0.1

    :param precision: int - точность, которую нужно конвертировать
    :return: float - преобразованная точность, в виде float
    """
    return float('0.' + '0' * (precision - 1) + '1')


def handle_precision(num, is_decimal_precision: bool) -> float | None | Any:
    if num is None:
        return None
    if is_decimal_precision:
        return convert_precision(num)
    return num
