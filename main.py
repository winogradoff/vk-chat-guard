from os import environ, remove
from datetime import datetime
from hashlib import md5
from time import sleep
from requests import get, post
from vk import API
from apscheduler.schedulers.blocking import BlockingScheduler


class ChatGuard:
    def __init__(self, token, chat_id, title, cache_url, cache_file, cache_temp, sleep_time,
                 scheduler_interval):
        """
        Конструктор ChatGuard
        :param token: токен авторизации в VK
        :param chat_id: ID беседы
        :param title: ожидаемое название беседы
        :param cache_url: URL изображения беседы
        :param cache_file: кеш файл-изображение беседы
        :param cache_temp: файл для временного хранения
        :param sleep_time: пауза перед chat_job (в секундах)
        :param scheduler_interval: интервал chat_job (в секундах)
        """
        self.token = token
        self.chat_id = chat_id
        self.chat_title = title
        self.cache_url = cache_url
        self.cache_file = cache_file
        self.cache_temp = cache_temp
        self.sleep_time = sleep_time
        self.scheduler_interval = scheduler_interval
        self.buffer_size = 8192

        print('Authorization... ', end='')
        self.api = API(access_token=self.token)
        print('READY.')

    def md5_file(self, path):
        """
        Подсчёт md5 хеша файла
        :param path: путь к файлу
        :return: md5 hash
        """
        print('Calculation hash of file {:s}... '.format(path), end='')
        with open(path, 'rb') as file:
            md5hash = md5()
            buffer = file.read(self.buffer_size)
            while len(buffer) > 0:
                md5hash.update(buffer)
                buffer = file.read(self.buffer_size)
            print('READY.')
            return md5hash.hexdigest()

    def update_photo(self):
        """
        Обновление фото чата
        """
        print('Updating photo... ', end='')
        response = self.api.messages.setChatPhoto(
            file=post(
                url=self.api.photos.getChatUploadServer(chat_id=self.chat_id)['upload_url'],
                files={'file': open('images/mai-logo.png', 'rb')}
            ).json()['response']
        )
        print('READY.')
        if 'photo_200' in response['chat']:
            print('Saving cache URL... ', end='')
            self.save_cache_url(response['chat']['photo_200'])
            print('READY.')

    def get_cache_url(self):
        """
        Получение кешированной ссылки
        :return: ссылка из файла кеша
        """
        print('Getting the cache url... ', end='')
        with open(self.cache_url, 'r') as file:
            content = file.readline()
            print('READY.')
            return content

    def save_cache_url(self, url):
        """
        Сохраниение ссылки в кеш
        :param url: URL изображения
        """
        print('Updating the cache url... ', end='')
        with open(self.cache_url, 'w') as file:
            file.write(url)
        print('READY.')

    def save_temp(self, content):
        """
        Сохранение временного файла
        :param content: содержимое файла
        """
        print('Saving the temp file... ', end='')
        with open(self.cache_temp, 'wb') as file:
            file.write(content)
        print('READY.')

    def remove_temp(self):
        """
        Удаление временного файла
        """
        print('Removing the temp file... ', end='')
        remove(self.cache_temp)
        print('READY.')

    def photo_changed(self, chat_response):
        """
        Проверка изменения фото беседы
        :param chat_response: ответ VK API messages.getChat
        :return: результат проверки
        """
        result = False

        if 'photo_200' not in chat_response:
            result = True
            print('The chat photo is empty.')
        else:
            photo_200_url = chat_response['photo_200']
            if self.get_cache_url() != photo_200_url:
                # Если url отличается
                print('The chat photo URL has been updated.')
                print('Checking the md5 hash of file...')
                response = get(photo_200_url)
                self.save_temp(response.content)

                if self.md5_file(self.cache_file) != self.md5_file(self.cache_temp):
                    result = True
                    print('md5_file(CACHE_FILE) != md5_file(CACHE_TEMP)')
                else:
                    print('Files are the same.')
                    # Если md5 одинаковые, то обновить cache-url
                    print('Updating chat url... ', end='')
                    self.save_cache_url(photo_200_url)

                self.remove_temp()

        return result

    def title_changed(self, chat_response):
        """
        Проверка изменения названия беседы
        :param chat_response: ответ VK API messages.getChat
        :return: результат проверки
        """
        return 'title' not in chat_response or chat_response['title'] != self.chat_title

    def update_title(self):
        """
        Обновление названия беседы
        """
        print('Updating the chat title... ', end='')
        self.api.messages.editChat(chat_id=self.chat_id, title=self.chat_title)
        print('READY.')

    def chat_job(self):
        """
        Ежеминутное задание проверки названия и фото беседы
        """
        print()
        print('=== Begin ===')

        # Метка времени
        print(str(datetime.now()))

        print('Waiting for {:d} seconds...'.format(self.sleep_time))

        # Пауза во избежании блокироки
        sleep(self.sleep_time)

        print('Getting information about the chat... ', end='')
        chat_response = self.api.messages.getChat(chat_id=self.chat_id)
        print('READY.')

        if self.photo_changed(chat_response):
            print('The chat photo has been changed!')
            self.update_photo()
        else:
            print('The chat photo is OK.')

        if self.title_changed(chat_response):
            print('The chat title has been changed!')
            self.update_title()
        else:
            print('The title is OK.')

        print('=== End ===')
        print()

    def run(self):
        scheduler = BlockingScheduler()
        scheduler.add_job(self.chat_job, 'interval', seconds=self.scheduler_interval)
        scheduler.start()


if __name__ == '__main__':
    ChatGuard(
        token=environ.get("VK_AUTH_TOKEN", ""),
        chat_id=int(environ.get("VK_CHAT_ID", 0)),
        title=environ.get("VK_CHAT_TITLE", ""),
        sleep_time=int(environ.get("VK_SLEEP_SECONDS", 0)),
        scheduler_interval=int(environ.get("VK_SCHEDULER_INTERVAL_SECONDS", 0)),
        cache_url='images/cache/cache-url',
        cache_file='images/cache/cache-file',
        cache_temp='images/cache/cache-temp'
    ).run()
