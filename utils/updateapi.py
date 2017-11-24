# -*- coding: utf-8 -*-

import urllib.request as request
import ssl
from utils import log

class ApiConnector:
    """Объект для работы с API сервиса обновлений 1С"""

    __api_url = "https://update-api.1c.ru/update-platform/programs"
    __request_opener = None
    __ssl_context = None
    __request_body_templ = '{{"programName":"{0}","versionNumber":"{1}","platformVersion":"{2}","updateType":"{3}"}}'

    def __init__(self, its_login, its_password, proxy_config=None):
        self.__ssl_context = ssl.create_default_context()
        self.__ssl_context.check_hostname = False
        self.__ssl_context.verify_mode = ssl.CERT_NONE

        self.__its_login = its_login
        self.__its_password = its_password

        self.__proxy_host = '' if proxy_config is None else proxy_config["host"]
        self.__proxy_port = '' if proxy_config is None else proxy_config["port"]
        self.__proxy_username = '' if proxy_config is None else proxy_config["username"]
        self.__proxy_password = '' if proxy_config is None else proxy_config["password"]

        if not self.__proxy_host == '':
            proxy_url = 'http://{0}:{1}/'.format(self.__proxy_host, self.__proxy_port)
            self.__proxy_handler = request.ProxyHandler({'http': proxy_url})

            self.__proxy_auth_handler = request.ProxyBasicAuthHandler()
            self.__proxy_auth_handler.add_password('realm', 'host', self.__proxy_username, self.__proxy_password)

            __request_opener = request.build_opener(self.__proxy_handler, self.__proxy_auth_handler)
            request.install_opener(__request_opener)


    def check_platform_update(self, current_version):
        """Получение информации о доступных обновлениях платформы 1С.
        @param current_version: проверяемая версия платформы 1С.
        @return: информация о доступных обновлениях в виде словаря:
                 {
                     "platformVersion": "8.3.11.2867",
                     "transitionInfoUrl": "http://downloads.v8.1c.ru/content//AutoUpdatesFiles/Platform/8_3_11_2867/V8Update.htm",
                     "releaseUrl": "https://releases.1c.ru/version_files?nick=Platform83&ver=8.3.11.2867&needAccessToken=true",
                     "distributionUin": "f0e3ffa2-c9de-43e0-96e4-ecca51e9f34b",
                     "size": 297891789,
                     "recommended": false
                 }
        """
        import json

        request_url = "{0}/update/info".format(self.__api_url)
        request_body = self.__request_body_templ.format('HRM', '3.1', current_version, 'NewPlatform')
        http_request = request.Request(request_url, request_body.encode("utf-8"), {'Content-Type': 'application/json'})

        result = None
        try:
            http_response = request.urlopen(http_request, context=self.__ssl_context)
            resp_body = http_response.read()
            resp_dict = json.loads(resp_body)
            result = resp_dict["platformUpdateResponse"]
        except Exception as ex:
            log.error('Ошибка при проверке обновлений платформы 1С.', str(ex))

        return result


    def check_conf_update(self, conf_name, conf_version):
        """Получение информации о доступных обновлениях конфигурации 1С.
        @param conf_name: название конфигурации.
        @param conf_version: проверяемая версия конфигурации.
        @return: информация о доступных обновлениях в виде словаря:
                 {
                    "configurationVersion": "3.1.3.274",
                    "size": 109636470,
                    "platformVersion": "8.3.10.2252",
                    "updateInfoUrl": "http://downloads.v8.1c.ru/content//AutoUpdatesFiles/HRM/3_1_3_274/82/News1cv8.htm",
                    "howToUpdateInfoUrl": null,
                    "upgradeSequence": [
                        "f800aa79-62ca-46d5-9608-b2879f2a3468",
                        "34347f2f-42a5-43ad-8143-1be5cbd3ad99"
                    ],
                    "programVersionUin": "de35e1b9-2e0d-4f32-8269-cf61a6010c04"
                 }
        """
        import json

        request_url = "{0}/update/info".format(self.__api_url)
        request_body = self.__request_body_templ.format(conf_name, conf_version, '', 'NewProgramOrRedaction')
        http_request = request.Request(request_url, request_body.encode("utf-8"), {'Content-Type': 'application/json'})

        result = None
        try:
            http_response = request.urlopen(http_request, context=self.__ssl_context)
            resp_body = http_response.read()
            resp_dict = json.loads(resp_body)
            result = resp_dict["configurationUpdateResponse"]
        except Exception as ex:
            log.error('Ошибка при проверке обновлений конфигурации 1С.', str(ex))

        return result


    def get_platform_download_url(self, distribution_uin):
        """Получение ссылки на скачивание платформы 1С.
        @param distribution_uin: идентификатор релизной версии платформы (напр. "f0e3ffa2-c9de-43e0-96e4-ecca51e9f34b"),
                                 возвращается при вызове check_platform_update().
        @return: прямая ссылка на скачивание.
        """
        import json

        request_url = "{0}/update/".format(self.__api_url)

        dict_body = {"upgradeSequence": None, "programVersionUin": None,
                     "platformDistributionUin": distribution_uin,
                     "login": self.__its_login, "password": self.__its_password}
        request_body = json.dumps(dict_body)

        http_request = request.Request(request_url, request_body.encode("utf-8"), {'Content-Type': 'application/json'})

        result = None
        try:
            http_response = request.urlopen(http_request, context=self.__ssl_context)
            resp_body = http_response.read()
            resp_dict = json.loads(resp_body)
            result = resp_dict["platformDistributionUrl"]
        except Exception as ex:
            log.error('Ошибка при получении ссылки на скачивание платформы 1С.', str(ex))

        return result


    def get_conf_download_data(self, distribution_uin, program_uin):
        """Получение данных для скачивания обновления конфигурации 1С.
        @param distribution_uin: идентификатор версии конфигурации 1С (напр. "f0e3ffa2-c9de-43e0-96e4-ecca51e9f34b"),
                                 возвращается при вызове check_conf_update().
        @param program_uin: идентификатор программы (напр. "f0e3ffa2-c9de-43e0-96e4-ecca51e9f34b"),
                            возвращается при вызове check_conf_update().
        @return: информация о доступных обновлениях в виде словаря:
                 {
                    "templatePath": "1c\\Accounting\\3_0_52_32",
                    "executeUpdateProcess": false,
                     "updateFileUrl": "http://downloads.v8.1c.ru/tmplts//1c/Accounting/3_0_52_32/1cv8.zip",
                     "updateFileName": "1cv8.cfu",
                     "updateFileFormat": "ZIP",
                     "size": 110289944,
                     "hashSum": "fEPkf6KV2CG2cWZ7674W5Q=="
                 }
        """
        import json

        request_url = "{0}/update/".format(self.__api_url)

        dict_body = {"upgradeSequence": [distribution_uin], "programVersionUin": program_uin,
                     "platformDistributionUin": None,
                     "login": self.__its_login, "password": self.__its_password}
        request_body = json.dumps(dict_body)

        http_request = request.Request(request_url, request_body.encode("utf-8"), {'Content-Type': 'application/json'})

        resp_dict = None
        try:
            http_response = request.urlopen(http_request, context=self.__ssl_context)
            resp_body = http_response.read()
            resp_dict = json.loads(resp_body)
        except Exception as ex:
            log.error('Ошибка при получении ссылки на скачивание конфигурации 1С.', str(ex))

        result = None
        if (not resp_dict is None) and (not resp_dict["configurationUpdateDataList"] is None):
            result = resp_dict["configurationUpdateDataList"][0]

        return result


    def download_file(self, url):
        """Скачать файл с сайта обновлений 1С.
        @param url: адрес файла для скачивания.
        @return: двоичные данные файла
        """
        import base64

        auth_str = "{0}:{1}".format(self.__its_login, self.__its_password)
        base64_auth_str = base64.b64encode(auth_str.encode("utf-8"))
        authorization = "Basic {0}".format(base64_auth_str.decode())
        http_request = request.Request(url, None, {'User-Agent': '1C+Enterprise/8.3', 'Authorization': authorization})

        result = None
        try:
            http_response = request.urlopen(http_request, context=self.__ssl_context)
            result = http_response.read()
        except Exception as ex:
            log.error('Ошибка при скачивании файла обновления.', str(ex))

        return result
