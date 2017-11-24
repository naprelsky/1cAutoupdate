# -*- coding: utf-8 -*-

import logging
import traceback
import os
from os import getlogin, makedirs as make_dir
from os.path import exists, join as join_path
from platform import node as comp_name

__logger_on = False
__LOGGER = logging.getLogger('assembly')
__ENV_DESC = {'user': getlogin(), 'comp': comp_name()}

def init(print_to_console=True, print_to_file=True):
    """Инициализация объекта логирования"""
    global __logger_on

    log_level = logging.DEBUG
    __LOGGER.setLevel(log_level)
    __logger_on = True

    formatter = logging.Formatter('%(asctime)s %(comp)s(%(user)s)- %(levelname)s: %(message)s')

    # Вывод данных логирования в файл
    if print_to_file:
        file_handle = logging.FileHandler(file_name(), 'a', 'utf-8')
        file_handle.setLevel(log_level)
        file_handle.setFormatter(formatter)
        __LOGGER.addHandler(file_handle)

    if print_to_console:
        # Вывод данных логирования в консоль
        console_handle = logging.StreamHandler()
        console_handle.setLevel(log_level)
        console_handle.setFormatter(formatter)
        __LOGGER.addHandler(console_handle)


def close():
    global __logger_on

    if __LOGGER.hasHandlers():
        for handle in __LOGGER.handlers:
            if isinstance(handle, logging.FileHandler):
                handle.close()
            elif isinstance(handle, logging.StreamHandler):
                handle.flush()
                __LOGGER.removeHandler(handle)

    __logger_on = False


def info(msg, *args):
    global __logger_on

    if __logger_on:
        __LOGGER.info(msg, *args, extra=__ENV_DESC)
    else:
        print(msg)


def warn(msg, *args):
    global __logger_on

    if __logger_on:
        __LOGGER.warning(msg, *args, extra=__ENV_DESC)
    else:
        print(msg)

def debug(msg, *args):
    global __logger_on

    if __logger_on:
        __LOGGER.debug(msg, *args, extra=__ENV_DESC)
    else:
        print(msg)

def error(msg, *args):
    global __logger_on

    trace = traceback.format_exc()
    if not trace or trace is None or trace == 'NoneType\n':
        # Если исключения не было, то фиксируем место откуда был вызов функции
        trace = traceback.format_stack()
        trace = '\n'.join([trace[x] for x in range(0, len(trace)) if x >= len(trace) - 6]) # Только последние шесть записей

    full_msg = msg + "\n\tTRACE:\n" + trace

    if __logger_on:
        __LOGGER.error(full_msg, *args, extra=__ENV_DESC)
    else:
        print(msg)


def directory():
    """Возвращает путь к каталогу для хранения логов"""

    path_to_log = join_path(os.getcwd(), 'logs')

    if not exists(path_to_log):
        make_dir(path_to_log)

    return path_to_log


def file_name():
    """Возвращает наименование основного файла логирования"""
    return join_path(directory(), "main.log")
