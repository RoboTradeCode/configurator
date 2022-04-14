"""
\file utils.py
\author github:khanbekov, telegram:qoddrysdaim
\brief В файле находятся вспомогательные функции, нужные для работы API
\data 2022.04.11
"""
import json
import os
import time

from pydantic.main import BaseModel

from src.logger.logger import logger

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

class HeaderFile(BaseModel):
    exchange: str
    instance: str
    node: str = "configurator"
    algo: str = "spread_bot_cpp"

def validate_header_file(path_to_file: str):
    with open(f'{path_to_file}', 'rw') as header_file:
        header_data = json.load(header_file)
        header = HeaderFile(**header_data)
        print(header)
        header_file.write(json.dumps(header.dict()))




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

    # Создание словаря с соответствием [Имя_файла : Содержимое_файла]
    result = dict(zip([os.path.splitext(file)[0] for file in files], files_content))

    return result


def get_micro_timestamp() -> int:
    """ Функция для получения текущего timestamp в микросекундах

    :return: int - timestamp в микросекундах
    """
    return round(time.time() * 1000000)
