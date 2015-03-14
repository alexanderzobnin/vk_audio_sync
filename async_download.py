# -*- coding: utf-8 -*-

"""Загрузка аудиозаписей из ВК.
Вариант с асинхронной загрузкой файлов с помощью asyncio и aiohttp.
"""

import os
import asyncio

import aiohttp

from vk_api import VkAPI
from config import *


def download_audio_item(audio_item):

    chunk_size = 1024

    # Формируем имя файла
    filename = '{artist} - {title}.mp3'.format(**audio_item)
    filepath = os.path.join(DOWNLOADS_PATH_ASYNC, filename)
    print('{artist} - {title}'.format(**audio_item))

    # Скачиваем аудиозапись, если она еще не загружена
    if not os.path.exists(filepath):

        #
        r = yield from aiohttp.request('GET', audio_item['url'])
        if r.status == 200:
            try:
                with open(filepath, 'wb') as f:
                    while True:
                        chunk = yield from r.content.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
            except OSError:
                pass
    else:
        print('%s already exist' % filename)


def main():

    # Инициализируем API
    vk = VkAPI(VK_LOGIN, VK_PASSWORD)
    response = vk.audio.get(count=10)

    # Проверяем каталог для загрузки
    if not os.path.exists(DOWNLOADS_PATH_ASYNC):
        os.makedirs(DOWNLOADS_PATH_ASYNC)

    coros = []
    for itm in response['items']:
        coros.append(asyncio.Task(download_audio_item(itm)))

    yield from asyncio.gather(*coros)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())