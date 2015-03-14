# -*- coding: utf-8 -*-

"""Простое API для работы с ВКонтакте на Python.
"""

import urllib.parse
from html.parser import HTMLParser
import json

import requests


# Адреса для авторизации на базе протокола OAuth
VK_OAUTH_URL = "https://oauth.vk.com/authorize"
VK_OAUTH_REDIRECT_URI = "https://oauth.vk.com/blank.html"

# Версия API ВКонтакте
VK_API_VERSION = '5.29'

# Базовый url для формирования запросов к API
VK_BASE_API_METHOD_URL = "https://api.vk.com/method/"


class VkAuthParser(HTMLParser):
    """Парсер для разбора страницы авторизации приложения.

    После открытия формы авторизации, пользователю будет предложено ввести логин и пароль. Нужно распарсить форму
    и извлечь из нее параметры, которые мы будем передавать на сервер:
        <form method="post" action="https://login.vk.com/?act=login&soft=1&utf8=1">
        извлекаем 'action' и сохраняем в self.url - это url, на который нужно отправить данные.

        <input type="hidden" name="_origin" value="https://oauth.vk.com">
        <input type="hidden" name="ip_h" value="477b...d1" />
        <input type="hidden" name="to" value="aHR0c...bGU-">
        извлекаем '_origin', 'ip_h', 'to' и сохраняем в self.auth_params - это данные, которые передаются
        вместе с 'email' и 'pass' в POST запросе (<form method="post"...>).

    """

    def __init__(self):
        """Инициализируем парсер.

        """
        HTMLParser.__init__(self)
        self.url = None
        self.auth_params = {}

    def handle_starttag(self, tag, attrs):
        """Переопределяем метод handle_starttag для поиска интересующей нас информации.

        """
        if tag == 'input':
            attrs_dict = dict(attrs)
            if 'name' in attrs_dict and 'value' in attrs_dict:
                self.auth_params[attrs_dict['name']] = attrs_dict['value']
        if tag == 'form':
            attrs_dict = dict(attrs)
            if 'action' in attrs_dict:
                self.url = attrs_dict['action']


def authorize(login, password):
    """Авторизует клиентское приложение для доступа к API ВКонтакте.

    :param login: Логин (email).
    :param password: Пароль.
    :return: словарь, содержащий access_token и другие данные авторизации.
    """

    # Открываем страницу авторизации приложения
    payload = {'client_id': '4732457',
               'scope': 'audio',
               'redirect_uri': VK_OAUTH_REDIRECT_URI,
               'display': 'mobile',
               'v': '5.28',
               'response_type': 'token'}
    r = requests.get(VK_OAUTH_URL, params=payload)

    # Парсим страницу с помощью VkAuthParser и сохраняем нужные параметры для авторизации
    auth_parser = VkAuthParser()
    auth_parser.feed(r.text)

    # Подставляем логин и пароль
    auth_parser.auth_params.update({'email': login, 'pass': password})

    # Отправляем форму на сервер и получаем ответ
    auth_response = requests.post(auth_parser.url, data=auth_parser.auth_params)

    # URL, на который перенаправляется клиент после успешной авторизации имеет вид:
    # https://oauth.vk.com/blank.html#access_token=<token>&expires_in=<exp_in>&user_id=<userid>
    # Извлекаем часть URL после #
    qs = urllib.parse.urlparse(auth_response.url)[5]
    parse_obj = urllib.parse.parse_qs(qs)

    # Сохраняем все  это в словарь auth_obj
    auth_obj = {'access_token': parse_obj['access_token'][0],
                'expires_in': parse_obj['expires_in'][0],
                'user_id': parse_obj['user_id'][0]}

    return auth_obj


class VkAPI:
    """Реализация API.

    """

    def __init__(self, login, password):
        """Инициализируем API.

        """
        auth_obj = authorize(login, password)
        self.access_token = auth_obj['access_token']
        self.expires_in = auth_obj['expires_in']
        self.user_id = auth_obj['user_id']

    def api_request(self, api_method, **params):
        """Метод для выполнения запроса к API.

        :param api_method: название метода из списка функций API (см. документацию API ВКонтакте)
        :param params: параметры соответствующего метода API
        :return: данные в формате JSON
        """

        # Добавляем общие для всех методов параметры
        params['v'] = VK_API_VERSION
        params['access_token'] = self.access_token

        # Формируем URL метода
        api_method_url = urllib.parse.urljoin(VK_BASE_API_METHOD_URL, api_method)

        # Делаем запрос к API и возвращаем JSON-объект
        r = requests.get(api_method_url, params=params)
        json_response = json.loads(r.content.decode())
        if 'response' in json_response:
            return json_response['response']
        elif 'error' in json_response:
            raise VkAPIException(json_response['error']['error_msg'])
        else:
            raise VkAPIException('Unknown error')

    def __getattr__(self, attr):
        """Создаем объекты API динамически, например, VkAPI.users

        """
        return VkAPIObject(attr, self)


class VkAPIObject:
    """Динамически вычисляемы объект API.

    """
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent

    def __getattr__(self, attr):
        """Динамически создаем методы объекта API.

        """

        # Создаем метод объекта, например, VkAPI.users.get()
        def object_method(**kwargs):
            return self.parent.api_request(api_method='{0}.{1}'.format(self.name, attr), **kwargs)

        return object_method


class VkAPIException(Exception):
    """Общее исключение API.

    """
    pass