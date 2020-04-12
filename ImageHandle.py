####################################
# File name: ImageHandle.py          #
# Author: Cirn09                   #
####################################
from PIL import Image, ImageEnhance as IE, \
    ImageFilter as IF, \
    ImageChops as IC, \
    ImageDraw as ID, \
    ImageOps as IO
import os
import shutil
import tempfile
from Main import log_file


def verify():
    if not os.path.exists(log_file):
        return True
    with open(log_file, 'r') as f:
        ld = f.read().split('\n')
    ld.pop()
    if ld:
        try:
            with Image.open(ld[-1]) as img:
                img.verify()
            return False
        except:
            print('Broken file:', ld[-1])
            if os.path.exists(ld[-1]):
                os.remove(ld[-1])
            with open(log_file, 'w') as f:
                f.write('\n'.join(ld[:-1]) + '\n')
            return True

def waifu2x(input_file, output_file, waifu2x_path, ratio):
    command = '{WAIFU2X_PATH}\\waifu2x-caffe-cui.exe -i \
{INPUT_FILE} -o {OUTPUT_FILE} -m noise_scale --scale_ratio \
{RATIO} --noise_level 2'

    com = command.format(
        WAIFU2X_PATH=waifu2x_path,
        INPUT_FILE=input_file,
        OUTPUT_FILE=output_file,
        RATIO=ratio)
    return os.system(com)


def isblank_border(img):
    '''判断图片是否为白色背景'''
    # 统计0.1边框上的近白色像素点数量
    # 四角有较大的权重，会被重复统计两次
    ratio = 0.05
    size = img.size
    xlen = int(size[0] * ratio)
    ylen = int(size[1] * ratio)
    pixels = int(size[0] * size[1] - size[0] * (1 - ratio * 2) * size[1] *
                 (1 - ratio * 2))
    blank_pixels = 0
    data = list(img.getdata())
    if img.mode == 'RGB':
        for pixel in data[:size[0] * ylen]:
            # 便利上方像素点
            if sum(pixel) > 0xe0 * 3:
                blank_pixels += 1
        for pixel in data[size[0] * (size[1] - ylen):]:
            # 便利下方像素点
            if sum(pixel) > 0xe0 * 3:
                blank_pixels += 1
        for x in range(size[1] * xlen):
            # 左方
            pixel = data[x // xlen * size[0] + x % xlen]
            if sum(pixel) > 0xe0 * 3:
                blank_pixels += 1
            # 右方
            pixel = data[x // xlen * size[0] + x % xlen + size[0] - xlen]
            if sum(pixel) > 0xe0 * 3:
                blank_pixels += 1
    elif img.mode == 'RGBA':
        for pixel in data[:int(size[0] * ylen)]:
            # 便利上方像素点
            if sum(pixel[:3]) > 0xe0 * 3 or pixel[3] < 0x10:
                blank_pixels += 1
        for pixel in data[int(size[0] * (size[1] - ylen)):]:
            # 便利下方像素点
            if sum(pixel[:3]) > 0xe0 * 3 or pixel[3] < 0x10:
                blank_pixels += 1
        for x in range(xlen * size[1]):
            # 左方
            pixel = data[x // xlen * size[0] + x % xlen]
            if sum(pixel[:3]) > 0xe0 * 3 or pixel[3] < 0x10:
                blank_pixels += 1
            # 右方
            pixel = data[x // xlen * size[0] + x % xlen + size[0] - xlen]
            if sum(pixel[:3]) > 0xe0 * 3 or pixel[3] < 0x10:
                blank_pixels += 1
    return blank_pixels / pixels > 0.80


BLUR_NONE = 0
BLUR_UP = 0b0001
BLUR_DOWN = 0b0010
BLUR_RIGHT = 0b0100
BLUR_LEFT = 0b1000
BLUR_VERTICAL = BLUR_UP | BLUR_DOWN
BLUR_HORIZONTAL = BLUR_RIGHT | BLUR_LEFT
BLUR_FULL = BLUR_VERTICAL | BLUR_HORIZONTAL


def blur_border(img, direction=BLUR_FULL, blur_level=3, blur_width_ratio=0.02):
    '''返回模糊边缘的图片(RGBA)'''
    size = img.size
    cut_point = list(
        map(int,
            (size[0] * blur_width_ratio, size[1] * blur_width_ratio, size[0] *
             (1 - blur_width_ratio), size[1] * (1 - blur_width_ratio))))
    crop_point = [0, 0, size[0] + 40, size[1] + 40]
    paste_point = [cut_point[0] + 20, cut_point[1] + 20]
    if not (direction & BLUR_UP):
        # 不需要上方模糊
        cut_point[1] = 0
        crop_point[1] = 20
        paste_point[1] = 0
    if not (direction & BLUR_DOWN):
        cut_point[3] = size[1]
        crop_point[3] = size[1] + 20
    if not (direction & BLUR_RIGHT):
        cut_point[2] = size[0]
        crop_point[2] = size[0] + 20
    if not (direction & BLUR_LEFT):
        cut_point[0] = 0
        crop_point[0] = 20
        paste_point[0] = 0
    expand_img = IO.expand(img.convert('RGBA'), 20, '#FFFFFF00')
    expand_img = expand_img.crop(crop_point)
    expand_img = expand_img.filter(IF.GaussianBlur(blur_level))
    expand_img.paste(img.crop(cut_point), paste_point)
    return expand_img


def background(img, newsize, blur_level, color_level, blend_level,
               mirror=True):
    '''填充处理生成背景'''
    size = img.size
    resize_raito = min(x / y for x, y in zip(newsize, size))
    resize = tuple(map(lambda x: int(x * resize_raito), size))
    resize_img = IO.fit(img.resize(resize), newsize)
    if mirror:
        mirror_img = IO.mirror(resize_img)
    else:
        mirror_img = resize_img
    if mirror_img.mode == 'RGBA':
        bg = Image.new('RGB', newsize, 'white')
        bg.paste(mirror_img, (0, 0), mirror_img)
    else:
        bg = mirror_img.convert('RGB')
    # bg = mirror_img.convert('RGB')
    bg = bg.filter(IF.GaussianBlur(blur_level))
    bg = IE.Color(bg).enhance(color_level)
    bg = Image.blend(Image.new('RGB', newsize, 'white'), bg, blend_level)
    return bg


def prehandle(img, newsize):
    '''预处理，缩小一下过大的图片，给出模糊方向'''
    size = img.size
    if size[0] > newsize[0] or size[1] > newsize[1]:
        xratio = newsize[0] / size[0]
        yratio = newsize[1] / size[1]
        if xratio < yratio:
            # 太宽
            img.thumbnail((newsize[0], int(size[1] * newsize[0] / size[0])),
                          Image.ANTIALIAS)
            # thumbnail直接对原图像进行操作
            return BLUR_VERTICAL
        else:
            # 太高
            img.thumbnail((int(size[0] * newsize[1] / size[1]), newsize[1]),
                          Image.ANTIALIAS)
            return BLUR_HORIZONTAL
    else:
        return BLUR_FULL


PASTE_V_TOP = 1 << 0
PASTE_V_CENTER = 1 << 1
PASTE_V_BOTTOM = 1 << 2
PASTE_H_LEFT = 1 << 3
PASTE_H_CENTER = 1 << 4
PASTE_H_RIGHT = 1 << 5

PASTE_CENTER = PASTE_V_CENTER | PASTE_H_CENTER
PASTE_RIGHT = PASTE_V_CENTER | PASTE_H_RIGHT
PASTE_BOTTOM = PASTE_V_BOTTOM | PASTE_H_CENTER


def handle(img,
           newsize,
           border_blur=True,
           border_blur_level=3,
           border_blur_direct=BLUR_FULL,
           bg_blank=False,
           bg_mirror=True,
           paste_pos=PASTE_CENTER,
           bg_blur_level=5,
           bg_color_level=0.9,
           bg_blend_level=0.16):
    '''处理图片'''
    size = img.size
    if border_blur:
        expand_img = blur_border(img, border_blur_direct, border_blur_level)
    else:
        expand_img = img.copy()
    size = expand_img.size
    paste_point = [0, 0]
    if paste_pos & PASTE_H_RIGHT:
        paste_point[0] = int(newsize[0] * 0.75 - size[0] * 0.5)
    elif paste_pos & PASTE_H_CENTER:
        paste_point[0] = int(newsize[0] * 0.5 - size[0] * 0.5)
    elif paste_pos & PASTE_H_LEFT:
        paste_point[0] = int(newsize[0] * 0.25 - size[0] * 0.5)
    if paste_pos & PASTE_V_CENTER:
        paste_point[1] = int(newsize[1] * 0.5 - size[1] * 0.5)
    elif paste_pos & PASTE_V_BOTTOM:
        paste_point[1] = int(newsize[1] * 0.6 - size[1] * 0.5)
    elif paste_pos & PASTE_V_TOP:
        paste_ponit[1] = int(newsize[1] * 0.4 - size[1] * 0.5)
    if bg_blank:
        bg = Image.new('RGB', newsize, 'white')
    else:
        bg = background(img, newsize, bg_blur_level, bg_color_level,
                        bg_blend_level, bg_mirror)
    bg.paste(expand_img, paste_point, expand_img)
    return bg


def main(input_path, output_path, newsize, waifu2x_path, ignore_list={}):
    filelist = os.listdir(input_path)
    td = tempfile.TemporaryDirectory()
    for file in filelist:
        if file in ignore_list:
            continue
        filepath = os.path.join(input_path, file)
        newfilename = os.path.splitext(file)[0] + '.png'
        newpath = os.path.join(output_path, newfilename)
        if os.path.exists(newpath):
            continue
        print(filepath)
        with Image.open(filepath) as img:
            size = img.size
            ratio = size[0] / size[1] / (newsize[0] / newsize[1])
            if 0.85 < ratio < 1.15:
                xratio = newsize[0] / size[0]
                yratio = newsize[1] / size[1]
                resize_ratio = xratio if xratio > yratio else yratio
                if img.mode=='RGBA':
                    filepath = os.path.join(td.name, file)
                    background(img, img.size, 0, 1, 1, False).convert('RGB').save(filepath)
                if resize_ratio <= 0.95:
                    # 什么也不做
                    shutil.copyfile(filepath, newpath)
                else:
                    waifu2x(filepath, newpath, waifu2x_path, resize_ratio)
            elif size[0] / size[1] <= 0.5:
                # 条幅
                blur_direct = prehandle(img, newsize)
                if img.size[0] > newsize[0] * 0.5:
                    paste_pos = PASTE_CENTER
                else:
                    paste_pos = PASTE_RIGHT
                handle(
                    img,
                    newsize,
                    bg_blank=True,
                    paste_pos=paste_pos,
                    border_blur_direct=blur_direct).save(newpath)
            elif size[0] / size[1] >= 2.0:
                # 横幅
                blur_direct = prehandle(img, newsize)
                blank = isblank_border(img)
                if img.size[1] > newsize[1] * 0.5:
                    paste_pos = PASTE_CENTER
                else:
                    paste_pos = PASTE_BOTTOM
                handle(
                    img,
                    newsize,
                    bg_blank=blank,
                    paste_pos=paste_pos,
                    bg_mirror=False).save(newpath)
            else:
                blur_direct = prehandle(img, newsize)
                size = img.size
                paste_pos = 0
                mirror = True
                blank = isblank_border(img)
                # if size[0] / size[1] > 1:
                #     if size[0] >= newsize[0] * 0.5:
                #         paste_pos = PASTE_CENTER
                #         mirror = False
                #     else:
                #         paste_pos = PASTE_RIGHT
                # else:
                #     paste_pos = PASTE_CENTER
                #     mirror = False
                if newsize[0] * 0.25 - size[0] * 0.5 < newsize[0] * 0.065:
                    paste_pos |= PASTE_H_CENTER
                    mirror = False
                else:
                    paste_pos |= PASTE_H_RIGHT
                    mirror = True
                if size[1] > newsize[1] * 0.5:
                    paste_pos |= PASTE_V_CENTER
                else:
                    paste_pos |= PASTE_V_BOTTOM

                if size[0] < newsize[0] * 0.25 or size[1] < newsize[1] * 0.25:
                    paste_pos = PASTE_RIGHT
                    blank = True
                handle(
                    img,
                    newsize,
                    paste_pos=paste_pos,
                    bg_blank=blank,
                    bg_mirror=mirror).save(newpath)


if __name__ == '__main__':
    input_path = r'D:\Pictures\Pixiv'
    # input_path = r'D:\Work\Py\img'
    output_path = r'D:\Pictures\Handled'
    waifu2x_path = r'D:\Tool\waifu2x'
    newsize = (1920, 1080)
    main(input_path, output_path, newsize, waifu2x_path)
    main(r'D:\Pictures\NP', output_path, newsize, waifu2x_path)