proxy = {
    'proxies': {'http': 'socks5h://127.0.0.1:15633', 'https': 'socks5h://127.0.0.1:15633'},
    'verify': False
}
# 设定代理
username = 'c1rn09'
# 用户名
password = ''
# 用户密码
access_token = None
refresh_token = None
download_path = 'E:\\Image\\Pixiv\\'
# 下载图片保存路径
input_path = download_path
# 处理的输入路径
output_path = 'E:\\Image\\Wallpaper\\'
# 输出路径
newsize = (1920, 1080)
# 输出分辨路
waifu2x_path = 'D:\Tool\waifu2x'
log_file = 'D:\\Work\\Py\\PixivWallpaper\\log'

import PixivDownload
import ImageHandle

if __name__ == '__main__':

    ImageHandle.verify()
    PixivDownload.download(download_path, proxy, username=username, password=password, at=access_token, rt=refresh_token)
    input('wait..')
    ImageHandle.main(input_path, output_path, newsize, waifu2x_path)