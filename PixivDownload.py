####################################
# File name: PixivDownload.py      #
# Author: Cirn09                   #
####################################
# from pixivpy3 import PixivAPI as pp
from pixivpy3 import AppPixivAPI as pp
import os
from PIL import Image

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_USER = ''
_PASS = ''
_PATH = ''
_EXISTS_TIME = 0
try:
    _SIZE = os.get_terminal_size()[0] - 1
except:
    _SIZE = 200


def download_one(api, urls, last=False):
    '''下载单图'''
    if urls.get('original'):
        url = urls['original']
        file_name = os.path.split(url)[-1]
    else:
        url = urls['large']
        origin_name = os.path.split(url)[-1]
        point_start = origin_name.rfind('_')
        point_end = origin_name.find('.')
        file_name = origin_name[:point_start] + origin_name[point_end:]
    full_path = os.path.join(_PATH, file_name)

    try:
        if os.path.exists(full_path):
            global _EXISTS_TIME
            _EXISTS_TIME += 1
            return True
        api.download(url, path=_PATH, name=file_name)
        return True
    except:
        if last:
            return False
        else:
            # 登陆重试一次
            api.login(_USER, _PASS)
            return download_one(api, url, True)


def download_more(api, urls, last=False):
    '''下载多图'''
    result = True
    for url in urls:
        result &= download_one(api, url['image_urls'])
    return result


def get_favorite_page(api, args=None, last=False):
    '''获取一页收藏'''
    try:
        if not args:
            return api.user_bookmarks_illust(api.user_id)
        else:
            return api.user_bookmarks_illust(**args)

    except:
        if last:
            return False
        else:
            api.login(_USER, _PASS)
            return get_favorite_page(api, args, True)


def log(done, total, pid, title, type, status):
    print(' ' * _SIZE, end='\r')
    print('{}/{}\t{}\t{}\t{}\t'.format(done, total, pid, title, type), end='')
    if status:
        print('Success', end='\r')
    else:
        print('Failure or Skip', end='\n')


def verify(path, delete=False):
    filelist = os.listdir(path)
    for file in filelist:
        try:
            with Image.open(os.path.join(path, file)) as img:
                img.verify()
        except:
            print('Broken file:', file)
            if delete:
                os.remove(os.path.join(path, file))


def download(username, password, save_path, proxy={}, detach_time=-1):
    global _USER
    global _PASS
    global _PATH
    global _EXISTS_TIME
    _USER = username
    _PASS = password
    _PATH = save_path
    total = '?'
    done = 0
    api = pp(**proxy)
    api.login(_USER, _PASS)
    page = 1
    if not os.path.isdir(_PATH):
        os.mkdir(_PATH)
    print('Total\tPID\tTitle\tType\tStatus')
    next_args = None
    while True:
        json = get_favorite_page(api, next_args)
        for fav in json['illusts']:
            if _EXISTS_TIME > detach_time:
                print('\nDetached!')
                return
            if fav['type'] == 'illust' or fav['type'] == 'manga':
                #if fav['work']['type'] == 'illustration':
                # 插画
                # 部分画师在投稿时可能会把多图投稿成漫画
                if fav['page_count'] == 1:
                    done += 1
                    log(done, total, fav['id'], fav['title'], fav['type'],
                        download_one(api, fav['image_urls']))
                else:
                    done += 1
                    log(done, total, fav['id'], fav['title'], fav['type'],
                        download_more(api, fav['meta_pages']))
            else:
                # 动图、漫画、小说
                done += 1
                log(done, total, fav['id'], fav['title'], fav['type'], False)
        if json.get('next_url'):
            next_args = api.parse_qs(json['next_url'])
        else:
            break
