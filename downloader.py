# -*- coding: utf-8 -*-

"""Загрузка аудиозаписей из ВК.
"""

import os
import requests
# import shutil

from vk_api import VkAPI
from config import *


# Инициализируем API
vk = VkAPI(VK_LOGIN, VK_PASSWORD)
response = vk.audio.get(count=5)

# Проверяем каталог для загрузки
if not os.path.exists(DOWNLOADS_PATH):
    os.makedirs(DOWNLOADS_PATH)

# Загружаем аудиозаписи
for audio_item in response['items']:

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
