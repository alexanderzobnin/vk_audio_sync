# -*- coding: utf-8 -*-

"""
Простое API для работы с Вконтакте.

"""

import urllib.parse
from html.parser import HTMLParser
import json
import requests


VK_OAUTH_URL = "https://oauth.vk.com/authorize"
VK_OAUTH_REDIRECT_URI = "https://oauth.vk.com/blank.html"

VK_BASE_API_METHOD_URL = "https://api.vk.com/method/"


class VkAuthParser(HTMLParser):
    """
    Парсер для разбора страницы авторизации приложения.
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
        """
        Инициализируем парсер.

        """
        HTMLParser.__init__(self)
        self.url = None
        self.auth_params = {}

    def handle_starttag(self, tag, attrs):
        """
        Переопределяем метод handle_starttag для поиска интересующей нас информации.

        :param tag:
        :param attrs:
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
    """
    Авторизует клиентское приложение для доступа к API ВКонтакте.

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

    # Парсим страницу и сохраняем нужные параметры для авторизации
    parser = VkAuthParser()
    parser.feed(r.text)

    # Подставляем логин и пароль
    parser.auth_params.update({'email': login, 'pass': password})

    # Отправляем форму на сервер и получаем ответ
    auth_response = requests.post(parser.url, data=parser.auth_params)

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


def api_request(api_method, **params):
    """
    Метод для выполнения запроса к API.

    :param api_method: название метода из списка функций API (см. документацию API ВКонтакте)
    :param params: параметры соответствующего метода API
    :return: данные в формате JSON
    """

    # Формируем URL метода
    api_method_url = urllib.parse.urljoin(VK_BASE_API_METHOD_URL, api_method)

    # Делаем запрос к API и возвращаем JSON-объект
    r = requests.get(api_method_url, params=params)
    json_response = json.loads(r.content.decode())
    return json_response