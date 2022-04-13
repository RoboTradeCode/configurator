"""
\file utils.py
\author github:khanbekov, telegram:qoddrysdaim
\brief В файле находятся вспомогательные функции, нужные для работы API
\data 2022.04.11
"""
import json
import os
import time

from src.logger.logger import logger


def get_dir_last_change_time(dir_name: str) -> float:
    """
    Функция рекурсивно обходит файлы и возвращает время
    последнего изменения среди файлов в директории и вложенных директориях.
    Если в папке нет файлов, будет возвращено значение -1

    :param dir_name: str - название папки, с которой нужно начать обход файлов.
    :return: float - время последнего изменения среди файлов в директории и вложенных директориях
    """
    # переменная будет хранить время последнего изменения
    last_change_time: float = -1
    # начинаем обход директорий
    for root, dirs, files in os.walk(dir_name):
        for file in files:
            # получаем время последнего изменения файла
            file_last_change_time = os.path.getmtime(os.path.join(root, file))
            # сравниваем с временем предыдущего последнего изменения другого файла
            if last_change_time < file_last_change_time:
                last_change_time = file_last_change_time

    return last_change_time


def get_json_from_dir(path_to_dir: str) -> dict:
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
    configs = dict(zip([os.path.splitext(file)[0] for file in files], files_content))

    return configs


def get_micro_timestamp() -> int:
    """ Функция для получения текущего timestamp в микросекундах

    :return: int - timestamp в микросекундах
    """
    return round(time.time() * 1000000)