# -*- coding: utf-8 -*-

"""Загрузка аудиозаписей из ВК.
Вариант с асинхронной загрузкой файлов с помощью asyncio и aiohttp.
"""

import os
import asyncio

import aiohttp

from vk_api import VkAPI
from config import *


# Количество одновременных загрузок
PARALLEL_TASKS_NUMB = 10

# Размер буфера для чтения данных с сервера
READ_CHUNK_SIZE = 1024 ** 3

DOWNLOADS_PATH = DOWNLOADS_PATH_ASYNC

@asyncio.coroutine
def download_audio_item(audio_item):

    # Формируем имя файла
    filename = '{artist} - {title}.mp3'.format(**audio_item)
    filepath = os.path.join(DOWNLOADS_PATH, filename)

    # Скачиваем аудиозапись, если она еще не загружена
    if not os.path.exists(filepath):
        print('downloading: {artist} - {title}'.format(**audio_item))

        #
        r = yield from aiohttp.request('GET', audio_item['url'])
        if r.status == 200:
            try:
                with open(filepath, 'wb') as f:
                    while True:
                        chunk = yield from r.content.read(READ_CHUNK_SIZE)
                        if not chunk:
                            break
                        f.write(chunk)
            except OSError:
                pass
    else:
        print('already exist: {0}'.format(filename))


@asyncio.coroutine
def main():

    # Инициализируем API
    vk = VkAPI(VK_LOGIN, VK_PASSWORD)
    response = vk.audio.get(count=50)

    # Проверяем каталог для загрузки
    if not os.path.exists(DOWNLOADS_PATH):
        os.makedirs(DOWNLOADS_PATH)

    coros = []
    for itm in response['items']:
        coros.append(asyncio.Task(download_audio_item(itm)))
        if len(coros) == PARALLEL_TASKS_NUMB:
            yield from asyncio.gather(*coros)
            coros = []


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())