import PixivDownload
import ImageHandle


def download(username, password, path, proxy, detach):
    PixivDownload.verify(path, True)
    PixivDownload.download(username, password, path, proxy, detach)


def handle(input_path, output_path, newsize, waifu2x_path):
    PixivDownload.verify(output_path, True)
    ImageHandle.main(input_path, output_path, newsize, waifu2x_path)


if __name__ == '__main__':
    proxy = {'proxies': {'https': '127.0.0.1:1080'}, 'verify': False}
    # 设定代理
    username = 'your username'
    # 用户名
    password = 'your password'
    # 用户密码
    download_path = 'D:\\Pictures\\Pixiv\\'
    # 下载图片保存路径
    detach = 1
    # 遇到多少次以下载就停止下载
    input_path = download_path
    # 处理的输入路径
    output_path = 'D:\\Pictures\\Handled\\'
    # 输出路径
    newsize = (1920, 1080)
    # 输出分辨路
    waifu2x_path = 'D:\Tool\waifu2x'

    download(username, password, download_path, proxy, detach)
    handle(input_path, output_path, newsize, waifu2x_path)