# -*- coding: utf-8 -*-

import sys as system
from utils import worker, log, updateapi

def main(argv):
    """Основная функция выполнения обновления"""
    print(argv)

    log.init()
    log.info('Начало проверки обновлений.')

    # Инициализация настроек обновления из файла settings.json
    settings_dict = worker.init_settings()

    # Создание коннектора для работы с сервисом проверки обновлений 1С
    connector = updateapi.ApiConnector(settings_dict["itsUsername"],
                                       settings_dict["itsPassword"],
                                       settings_dict["proxySettings"])

    # Поиск и скачивание новой версии платформы 1С
    worker.update_platform(connector, settings_dict)

    # Поиск и скачивание новых версий конфигураций 1С
    worker.update_configurations(connector, settings_dict)

    log.info('Завершение проверки обновлений.')
    log.close()

if __name__ == "__main__":
    main(system.argv[1:])
