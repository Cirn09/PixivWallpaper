import os
import json
from enum import IntEnum
from typing import NamedTuple as namedtuple
from typing import Iterable, Generator
from time import sleep
from random import randint

from PIL import Image
from pixivpy3 import AppPixivAPI
from tqdm import tqdm

import config

OAUTH_ERROR = '"Error occurred at the OAuth process. Please check your Access Token to fix this. Error Message: invalid_grant"'


class MyAPI(AppPixivAPI):
    def _requests(self, *args, **kwargs):
        if "my_retry" in kwargs:
            my_retry = kwargs.pop("my_retry")
        else:
            my_retry = 0

        try:
            sleep(randint(config.wait_time_min, config.wait_time_max))
            return super().requests_call(*args, **kwargs)
        except Exception as e:
            if my_retry == config.max_retry:
                raise e
            else:
                print("=" * 50)
                print(str(e))
                print(f"retry {my_retry + 1} times")
                return self._requests(my_retry=my_retry + 1, *args, **kwargs)

    def requests_call(self, *args, **kwargs):
        # def requests_call(self, method, url, headers=None, params=None, data=None, stream=False):
        """requests http/https call for Pixiv API"""

        if "my_retry" in kwargs:
            my_retry = kwargs.pop("my_retry")
        else:
            my_retry = 0

        r = self._requests(*args, **kwargs)

        if kwargs.get("stream", True):
            return r

        j = r.json()
        if "error" in j and j["error"]["message"] == OAUTH_ERROR:
            if my_retry == config.max_retry:
                return r
            print(f"OAUTH, try {my_retry + 1} times")
            self.auth()
            return self.requests_call(my_retry=my_retry + 1, *args, **kwargs)


class Illust(namedtuple):
    title: str
    author: str
    pid: str
    uid: str
    url: str
    filename: str


class Status(IntEnum):
    init = 0
    check_last = 10
    get_list = 20
    downloading = 30
    finished = 40


def check_img(path: str, delete: bool = True) -> bool:
    if not os.path.exists(path):
        return False
    try:
        Image.open(path)
        return True
    except:
        if delete:
            os.remove(path)
        return False


def get_illust(illusts: dict) -> Generator[Illust, None, None]:
    title = illusts["title"]
    author = illusts["user"]["name"]
    pid = illusts["id"]
    uid = illusts["user"]["id"]

    if illusts["page_count"] == 1:
        url = illusts["meta_single_page"]["original_image_url"]
        yield Illust(
            title=title,
            author=author,
            pid=pid,
            uid=uid,
            url=url,
            filename=f"{uid}_{os.path.basename(url)}",
        )
    else:
        for illust in illusts["meta_pages"]:
            url = illust["image_urls"]["original"]
            yield Illust(
                title=title,
                author=author,
                pid=pid,
                uid=uid,
                url=url,
                filename=f"{uid}_{os.path.basename(url)}",
            )


def walk_page(page: dict) -> Generator[Illust, None, None]:
    for illust in page["illusts"]:
        for x in get_illust(illust):
            yield x


class Download(object):
    def __init__(self, dir: str, refresh_token: str, requests_kwargs: dict = {}):
        self.status: Status = Status.init

        self.api = MyAPI(**requests_kwargs)
        self.api.set_auth(None, refresh_token=refresh_token)
        self.api.auth()
        self.dir = dir
        self.list: list[Illust] = []
        self.filter_types = ("illust", "manga")
        self.filter_visible = True

    def __del__(self):
        if self.status < Status.downloading:
            # 还没开始下载，列表可能不完整，不保存
            return
        with open("last_log", "w") as f:
            json.dump({"status": self.status, "list": self.list}, f)

    def check_last(self):
        self.status = Status.check_last

        if not os.path.exists("last_log"):
            return
        with open("last_log", "r") as f:
            last = json.load(f)
        if last["status"] != Status.finished:
            return
        if not last["list"]:
            return

        for x in last["list"]:
            ilt = Illust(*x)
            if not check_img(os.path.join(self.dir, ilt.filename)):
                self.list.append(ilt)

    def get_list(self):
        self.status = Status.get_list
        next_arg = {"user_id": self.api.user_id}
        b = False
        cnt = 0
        while page := self.api.user_bookmarks_illust(**next_arg):  # type: ignore

            for illust in walk_page(page):
                if os.path.exists(os.path.join(self.dir, illust.filename)):
                    cnt += 1
                    if cnt == config.max_exist:
                        b = True
                        break
                else:
                    cnt = 0
                    self.list.append(illust)
            if b:
                break

            if page["next_url"]:
                next_arg = self.api.parse_qs(page["next_url"])
            else:
                break

    def download(self):
        self.status = Status.downloading
        with tqdm(total=len(self.list)) as pbar:
            for i, ilt in enumerate(self.list):
                pbar.set_description(ilt.title)
                pbar.update(1)
                self.api.download(ilt.url, path=self.dir, name=ilt.filename)
        self.status = Status.finished

    def process(self):
        self.check_last()
        self.get_list()
        self.download()
        self.__del__()

    def filter(self, illust: dict) -> bool:
        return (illust["type"] in self.filter_types) and (
            not self.filter_visible or illust["visible"]
        )


if __name__ == "__main__":
    d = Download(config.pixiv_download_path, config.pixiv_refresh_token)
    d.process()
