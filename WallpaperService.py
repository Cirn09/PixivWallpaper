import ctypes
import os
import random
from screeninfo import get_monitors

import config
from Convert import convertMultiple


def main():
    wallpaperPath = os.path.join(config.output_path, 'wallpaper.png')

    # for filename in os.listdir(config.output_path):
    #     os.remove(os.path.join(config.output_path, filename))

    images = []
    images = [os.path.join(folder, file)
              for folder in config.input_path for file in os.listdir(folder)]
    imageSelected = []  # {path, x, y, width, height}
    widthTotal = heightTotal = 0
    info = ''

    monitors = get_monitors()

    offset_x = min(monitors, key=lambda x: x.x).x
    offset_y = min(monitors, key=lambda x: x.y).y

    for monitor in monitors:
        path = random.choice(images)
        # path = 'D:\Pictures\Pixiv\\62299336_p0.jpg'
        info += f'{path}\n'
        x, y = monitor.x, monitor.y
        width, height = monitor.width, monitor.height
        real_x = x - offset_x
        real_y = y - offset_y

        imageSelected.append(
            {'path': path, 'x': real_x, 'y': real_y, 'width': width, 'height': height})

        if width + real_x > widthTotal:
            widthTotal = width + real_x
        if height + real_y > heightTotal:
            heightTotal = height + real_y

    convertMultiple((widthTotal, heightTotal),
                    imageSelected).save(wallpaperPath)
    with open(os.path.join(config.output_path, 'info.txt'), 'w') as f:
        f.write(info)

    SPI_SETDESKWALLPAPER = 20
    ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER, 0, wallpaperPath, 0)


if __name__ == "__main__":
    main()
