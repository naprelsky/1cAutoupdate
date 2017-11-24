# -*- coding: utf-8 -*-

import os
from os.path import join as join_path
from utils import log, updateapi

def init_settings():
    """Чтение настроек обновления из конфигурационного файла settings.json.
    @return: настройки обновления в виде словаря.
    """
    import json

    settings_dict = dict()
    with open('settings.json', 'r', encoding='utf-8') as file_handle:
        # загружаем из файла данные в словарь settings_dict
        settings_dict = json.load(file_handle)

    return settings_dict


def save_settings(settings_dict):
    """Запись настроек обновления в конфигурационный файл settings.json.
    @param settings_dict: настройки обновления в виде словаря.
    """
    import json

    with open('settings.json', 'w', encoding='utf-8') as file_handle:
        # преобразовываем словарь data в unicode-строку и записываем в файл
        file_handle.write(json.dumps(settings_dict, ensure_ascii=False))


def rename_dir_unicode(directory, exclude_files=[]):
    """Переименование файлов и каталогов в формат Unicode.
    @param directory: родительская директория.
    @param exclude_files: список файлов, которые не нужно переименовывать.
    """
    for item in os.scandir(directory):
        if item.name in exclude_files:
            continue

        unicode_name = item.name.encode('cp437').decode('cp866')
        if not item.name == unicode_name:
            os.rename(join_path(directory, item.name), join_path(directory, unicode_name))

        if os.path.isdir(item.path):
            # Переименовываем вложенные каталоги и файлы в них
            rename_dir_unicode(join_path(directory, unicode_name))


def unzip_unicode(zip_path, directory=None, remove=True):
    """Разархивирование архива с именами файлов в формате Unicode.
    @param zip_path: полный путь к архиву.
    @param directory: директория в которую разархивировать файл.
    @param remove: удалить файл после разархивирования.
    """
    import zipfile

    # По умолчанию распаковываем в текущий каталог
    unzip_dir = os.path.dirname(zip_path)
    if not directory is None:
        unzip_dir = directory

    upd_zip = zipfile.ZipFile(zip_path)
    upd_zip.extractall(unzip_dir)
    upd_zip.close()

    # Приводим имена разархивированных файлов к формату Unicode
    rename_dir_unicode(unzip_dir, os.path.basename(zip_path))

    if remove:
        os.remove(zip_path)


def update_platform(connector: updateapi.ApiConnector, settings: dict):
    """Скачивание текущей релизной версии платформы 1С.
    @param connector: коннектор к сервису 1С.
    @param settings: настройки обновления в виде словаря.
    """
    log.info(' > Начало обновления платформы 1С.')
    platform_settings = settings["platform"].copy()

    # Вычисление начальной версии, с которой начинать проверку
    check_version = platform_settings["startVersion"]
    if not platform_settings["lastDownloaded"] == "":
        check_version = platform_settings["lastDownloaded"]

    # Получение информации об обновлении платформы с сайте 1С
    upd_conf = connector.check_platform_update(check_version)
    if upd_conf is None:
        log.info(' -- Обновление для текущей версии платформы не найдено.')
        log.info(' < Обновление платформы 1С завершено.')
        return

    if upd_conf["platformVersion"] == check_version:
        log.info(' -- Текущая версия платформы является актуальной.')
        log.info(' < Обновление платформы 1С завершено.')
        return

    log.info(' -- Найдена новая версия {} платформы 1С.'.format(upd_conf["platformVersion"]))

    file_size = round(upd_conf["size"] / 1024 / 1024, 2)
    log.info(' -- Размер файла обновления: {} Мб.'.format(file_size))

    log.info(' -- Скачивания архива с платформой 1С...')
    platform_url = connector.get_platform_download_url(upd_conf["distributionUin"])
    platform_binary = connector.download_file(platform_url)
    log.info(' -- Скачивания архива с платформой 1С... Завершено!')

    log.info(' -- Сохранение архива на диск...')
    filename = "{0}.zip".format(upd_conf["platformVersion"])
    full_path = join_path(settings["platformPath"], filename)
    log.info(' -- Полный путь для сохранения: {}'.format(full_path))

    new_file = open(full_path, "wb")
    new_file.write(platform_binary)
    new_file.close()
    log.info(' -- Сохранение архива на диск... Завершено!')

    if settings["unzipFiles"]:
        log.info(' -- Распаковка архива...')
        unzip_unicode(full_path)
        log.info(' -- Распаковка архива... Завершено!')

    platform_settings["lastDownloaded"] = upd_conf["platformVersion"]
    settings["platform"] = platform_settings
    save_settings(settings)

    log.info(' < Обновление платформы 1С завершено.')


def update_configurations(connector: updateapi.ApiConnector, settings: dict):
    """Скачивание обновлений для всех конфигураций, указанных в настройке.
    @param connector: коннектор к сервису 1С.
    @param settings: настройки обновления в виде словаря.
    """
    for configuration in settings["configurations"]:
        log.info(' > Начало обновления конфигурации "{}".'.format(configuration["humanName"]))

        # Вычисление начальной версии, с которой начинать проверку
        check_version = configuration["startVersion"]
        if not configuration["lastDownloaded"] == "":
            check_version = configuration["lastDownloaded"]

        upd_conf = connector.check_conf_update(configuration["programName"], check_version)
        if upd_conf is None:
            log.info(' --  Обновление для текущей версии конфигурации не найдено.')
            log.info(' < Обновление конфигурации завершено.')
            continue

        if (upd_conf["configurationVersion"] is None) or upd_conf["configurationVersion"] == check_version:
            log.info(' -- Текущая версия конфигурации является актуальной.')
            log.info(' < Обновление конфигурации завершено.')
            continue

        log.info(' -- Найдена новая версия "{}" конфигурации.'.format(upd_conf["configurationVersion"]))
        log.info(' -- Скачивание цепочки обновлений...')

        for sequence in upd_conf["upgradeSequence"]:
            download_conf = connector.get_conf_download_data(sequence, upd_conf["programVersionUin"])
            if download_conf is None:
                log.info(' ---- Не удалось скачать обновление с uid={}.'.format(sequence))
                continue

            log.info(' -- > Скачивание цепочки {}...'.format(download_conf["templatePath"]))
            file_size = round(download_conf["size"] / 1024 / 1024, 2)
            log.info(' ---- Размер файла обновления: {} Мб.'.format(file_size))

            log.info(' ---- Скачивание файла обновления...')
            conf_binary = connector.download_file(download_conf["updateFileUrl"])
            log.info(' ---- Скачивание файла обновления... Завершено!')

            log.info(' ---- Сохранение архива на диск...')
            directory_path = join_path(settings["templatePath"], download_conf["templatePath"])
            os.makedirs(directory_path, exist_ok=True)
            full_path = join_path(directory_path, "1cv8.zip")
            log.info(' ---- Полный путь для сохранения: {}'.format(full_path))

            new_file = open(full_path, "wb")
            new_file.write(conf_binary)
            new_file.close()
            log.info(' ---- Сохранение архива на диск... Завершено!')

            if settings["unzipFiles"]:
                log.info(' ---- Распаковка архива...')
                unzip_unicode(full_path)
                log.info(' ---- Распаковка архива... Завершено!')

        log.info(' -- < Скачивание цепочки обновлений... Завершено!')
        log.info(' < Обновление конфигурации завершено.')
        configuration["lastDownloaded"] = upd_conf["configurationVersion"]

    save_settings(settings)
