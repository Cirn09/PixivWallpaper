####################################
# File name: PixivDownload.py      #
# Author: Cirn09                   #
####################################
from pixivpy3 import PixivAPI as pp
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


def download_one(api, url, last=False):
    '''下载单图'''
    try:
        if os.path.exists(os.path.join(_PATH, os.path.split(url)[-1])):
            global _EXISTS_TIME
            _EXISTS_TIME += 1
            return True
        api.download(url, path=_PATH)
        return True
    except:
        if last:
            return False
        else:
            # 登陆重试一次
            api.login(_USER, _PASS)
            return download_one(api, url, True)


def download_more(api, pid, last=False):
    '''下载多图'''
    try:
        img = api.works(pid)
        if img['status'] == 'success':
            # 获取成功
            for page in img['response'][0]['metadata']['pages']:
                if os.path.exists(
                        os.path.join(_PATH,
                                     os.path.split(
                                         page['image_urls']['large'])[-1])):
                    global _EXISTS_TIME
                    _EXISTS_TIME += 1
                    # 发现一个已存在就跳脱吧
                    return True
                api.download(page['image_urls']['large'], path=_PATH)
            return True
        else:
            raise
    except:
        if last:
            return False
        else:
            # 登陆重试一次
            api.login(_USER, _PASS)
            return download_more(api, pid, True)


def get_favorite_page(api, page, last=False):
    '''获取一页收藏'''
    try:
        json = api.me_favorite_works(page, image_sizes=['large'])
        if json['status'] == 'success':
            return json
        else:
            raise
    except:
        if last:
            return False
        else:
            api.login(_USER, _PASS)
            return get_favorite_page(api, page, True)


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
    total = 0
    done = 0
    api = pp(**proxy)
    api.login(_USER, _PASS)
    page = 1
    if not os.path.isdir(_PATH):
        os.mkdir(_PATH)
    print('Total\tPID\tTitle\tType\tStatus')
    while True:
        json = get_favorite_page(api, page)
        total = json['pagination']['total']
        for fav in json['response']:
            if _EXISTS_TIME > detach_time:
                print('\nDetached!')
                return
            # if fav['work']['type'] == 'illustration' or fav['work']['type'] == 'manga':
            if fav['work']['type'] == 'illustration':
                # 插画
                # 部分画师在投稿时可能会把多图投稿成漫画
                if fav['work']['page_count'] == 1:
                    done += 1
                    log(done, total, fav['work']['id'], fav['work']['title'],
                        fav['work']['type'],
                        download_one(api, fav['work']['image_urls']['large']))
                else:
                    done += 1
                    log(done, total, fav['work']['id'], fav['work']['title'],
                        fav['work']['type'],
                        download_more(api, fav['work']['id']))
            else:
                # 动图、漫画、小说
                done += 1
                log(done, total, fav['work']['id'], fav['work']['title'],
                    fav['work']['type'], False)
        if json['pagination']['next']:
            page = json['pagination']['next']
        else:
            break
