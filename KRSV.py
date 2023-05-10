import requests
from datetime import datetime
import json
import time
import urllib
from tqdm import tqdm

# Отправка фотографий по созданному списку из DR
# bot_token = ('6015892780:AAFnS3Fx7R5ZJeX4akabdqy0o8mDZclFLqY')
# bot = telebot.TeleBot(bot_token)
#
# @bot.message_handler(commands=['start', 'hello'])
# def send_welcome(message):
#     bot.reply_to(message, "Howdy, how are you doing?")


def read_token_vk():
    with open('Token_VK.txt', 'r') as fale:
        token_vk = fale.read().strip()
        return token_vk


class PhotoVk:
    url = 'https://api.vk.com/method/'

    def __init__(self, my_id_vk, my_token_vk, version=5.131):
        self.id_vk = my_id_vk
        self.params = {
            'access_token': my_token_vk,
            'v': version
        }

    # Ищем, где находятся фотографии, вся их информация и количество фотографий
    def search_all_photo(self):
        photo_search_url = self.url + 'photos.get'
        photo_search_params = {
            'owner_id': self.id_vk,
            'album_id': 'profile',
            'photo_sizes': 1,
            'extended': 1,
            'rev': 1,
            'count': 10
        }
        res = requests.get(url=photo_search_url, params={**self.params, **photo_search_params}).json()['response']
        return res['count'], res['items']

    # Ищем фото большого размера и всю необходимую информацию в дальнейшем
    def search_original_photo(self):
        photo_count, photo_items = self.search_all_photo()

        url_photo, type_photo, likes_in_photo = [], [], []

        keys = ['url_photo', 'size', 'likes_in_photo']
        zipped = zip(url_photo, type_photo, likes_in_photo)

        for i in range(len(photo_items)):
            likes_in_photo.append(photo_items[i]['likes']['count'])
            url_photo.append(photo_items[i]['sizes'][-1]['url'])
            type_photo.append(photo_items[i]['sizes'][-1]['type'])

            # bot.send_photo(770552448, url_list[i]) бот Телеграма, отправка фотографий по списку

        dicts = [dict(zip(keys, values)) for values in zipped]
        return dicts


class YaUploader:

    def __init__(self, my_token_yd: str, my_id_vk: str, photos):
        self.token = my_token_yd
        self.id_vk = my_id_vk
        self.photos = photos
        self.headers = {
            'Authorization': 'OAuth {}'.format(self.token)
        }

    # создаем имя файла
    def file_names(self):
        name_file = []

        for i in range(len(self.photos)):
            name_file.append(str(self.photos[i]['likes_in_photo']))
            if name_file.count(str(self.photos[i]['likes_in_photo'])) > 1:
                name_file[i] += '_' + datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
            elif name_file.count(str(self.photos[i]['likes_in_photo'])) < 1:
                print('Повторов не найдено')

        return name_file

    # Создаем папку на YD
    def folder_creation(self):
        upload_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        params = {'path': f'Photo_VK {datetime.now().strftime("%m_%d_%Y")}'}
        create_dir = requests.api.put(upload_url, headers=self.headers, params=params)

    # Качаем фотографии из VK в YD и возвращаем JSON-файл с информацией о каждом скачанном файле
    def upload(self):
        self.folder_creation()
        file_name = self.file_names()

        info_list = []
        for i in tqdm(range(len(file_name))):
            time.sleep(.30)
            params_string = urllib.parse.urlencode(
                {
                    'path': f'Photo_VK {datetime.now().strftime("%m_%d_%Y")}/{file_name[i]}.jpg',
                    'url': self.photos[i]['url_photo'],
                    'fields': None,
                    'disable_redirects': False,
                }
            )

            liba = requests.post(url='https://cloud-api.yandex.net/v1/disk/resources/upload?{}'.format(params_string),
                                 headers=self.headers).json()

            download_info = {'file_name': file_name[i], 'size': self.photos[i]['size']}
            info_list.append(download_info)

        with open('info.json', 'a') as file:
            json.dump(info_list, file, indent=2)


if __name__ == '__main__':
    token_vk = read_token_vk()
    token_yd = input('Введите свой ТОКЕН Яндекс Диска(НЕ ПЕРЕДАВАЙТЕ ВАШ ТОКЕН ТРЕТЬИМ ЛИЦАМ):')
    id_vk = input('Введите свой ID в ВК:')

    photo_VK = PhotoVk(id_vk, token_vk)
    upload_YD = YaUploader(token_yd, id_vk, photo_VK.search_original_photo())

    upload_photo_in_YD = upload_YD.upload()

