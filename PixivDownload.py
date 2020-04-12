####################################
# File name: PixivDownload.py      #
# Author: Cirn09                   #
####################################
# from pixivpy3 import PixivAPI as pp
from pixivpy3 import AppPixivAPI as pp
import os
from PIL import Image
from Main import log_file, download_path as path

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

path = ''
stop = False
_LOG_FILE = None
_SKIP = 0
try:
    _SIZE = os.get_terminal_size()[0] - 1
except:
    _SIZE = 200


def download_one(api, url):
    '''下载单图'''
    global _SKIP
    file_name = os.path.split(url)[-1]
    full_path = os.path.join(path, file_name)
    _LOG_FILE.write(full_path+'\n')
    if _SKIP:
        _SKIP -= 1
        return True
    _LOG_FILE.flush()
        
    if os.path.exists(full_path):
        global stop
        stop = True
        return False
    api.download(url, path=path, name=file_name)
    return True


def download_more(api, urls, last=False):
    '''下载多图'''
    result = True
    for url in urls:
        l = download_one(api, url['image_urls']['original'])
        result &= l
    global stop
    if stop and l:
        stop = False
        return True
    return result


def get_favorite_page(api, args=None):
    '''获取一页收藏'''
    if not args:
        return api.user_bookmarks_illust(api.user_id)
    else:
        return api.user_bookmarks_illust(**args)


def log(done, total, pid, title, type, status):
    print(' ' * _SIZE, end='\r')
    print('{}/{}\t{}\t{}\t{}\t'.format(done, total, pid, title, type), end='')
    if status:
        print('Success')
    else:
        print('Failure or Skip', end='\n')




def download(save_path, proxy={}, username=None, password=None, at=None, rt=None):
    global _LOG_FILE
    global path
    global _SKIP
    path = save_path
    total = '?'
    done = 0
    api = pp(**proxy)
    if username and password:
        api.login(username, password)
    elif at:
        api.set_auth(at, rt)
    else:
        return
    page = 1
    if not os.path.isdir(path):
        os.mkdir(path)
    print('Total\tPID\tTitle\tType\tStatus')
    next_args = None
    while True:
        json = get_favorite_page(api, next_args)
        if next_args is None:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    last = f.read().split('\n')
                if last and str(json['illusts'][0]['id']) in last[0]:
                    t = len(last) - 1
                    _SKIP = t
                    # while t > len(json['illusts']):
                    #    t -= len(json['illusts'])
                    #    next_args = api.parse_qs(json['next_url'])
                    # json['illusts'] = json['illusts'][t:]
            _LOG_FILE = open(log_file, 'w')
        for fav in json['illusts']:
            if stop:
                print('\nDetached!')
                return
            if (fav['type'] == 'illust' or fav['type'] == 'manga') and fav['visible']:
                #if fav['work']['type'] == 'illustration':
                # 插画
                # 部分画师在投稿时可能会把多图投稿成漫画
                if fav['page_count'] == 1:
                    done += 1
                    log(done, total, fav['id'], fav['title'], fav['type'],
                        download_one(
                            api,
                            fav['meta_single_page']['original_image_url']))
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
    _LOG_FILE.close()