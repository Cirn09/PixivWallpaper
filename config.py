# 代理
requests_kwargs = {
    "proxies": {"http": "socks5h://c9:51422", "https": "socks5h://c9:51422"},
    #    'verify': False
}
picture_path = "D:\\Pictures\\"

# pixiv
pixiv_username = "username"
pixiv_password = "password"
pixiv_access_token = None
pixiv_refresh_token = "token"
pixiv_download_path = picture_path + "Pixiv\\"

max_retry = 5
max_exist = 10

wait_time_min = 1
wait_time_max = 5

# 处理的输入路径
input_path = [
    pixiv_download_path,
]
# 输出路径
output_path = picture_path + "Wallpaper\\"

waifu2x_path = "C:\\Portable Program\\waifu2x"
log_file = ".\\log"

switch_delay = 30 * 60


try:
    from config_local import *
except ImportError:
    pass
