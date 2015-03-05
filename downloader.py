# -*- coding: utf-8 -*-

"""
Загрузка аудиозаписей из ВК.

"""

import os
import requests
# import shutil

import vk_api
from config import *

VK_API_VERSION = '5.27'

# Авторизуемся
auth_obj = vk_api.authorize(VK_LOGIN, VK_PASSWORD)

# Получаем список аудиозаписей пользователя
json_response = vk_api.api_request('audio.get',
                                   owner_id=auth_obj['user_id'],
                                   access_token=auth_obj['access_token'],
                                   count=0,
                                   v=VK_API_VERSION)

# Проверяем каталог для загрузки
if not os.path.exists(DOWNLOADS_PATH):
    os.makedirs(DOWNLOADS_PATH)

# Загружаем аудиозаписи
for audio_item in json_response['response']['items']:

    # Формируем имя файла
    filename = '{artist} - {title}.mp3'.format(**audio_item)
    filepath = os.path.join(DOWNLOADS_PATH, filename)
    print('{artist} - {title}'.format(**audio_item))

    # Скачиваем аудиозапись, если она еще не загружена
    if not os.path.exists(filepath):
        r = requests.get(audio_item['url'], stream=True)
        if r.status_code == 200:
            try:
                with open(filepath, 'wb') as f:
                    f.write(r.content)
            except OSError:
                # TODO: реализовать обработку исключений
                pass
    else:
        print('%s already exist' % filename)
