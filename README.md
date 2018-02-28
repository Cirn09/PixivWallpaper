# PixivWallpaper
包含P站收藏内容下载和将图片简单的处理为预期尺寸两部分。
图片比例合适的直接[waifu2x](https://github.com/lltcggie/waifu2x-caffe)处理之，比例不合适的则将其放大剪裁模糊之后作为背景，然后视情况将原图贴至背景左方、中间或偏下方
## Require
* Python 3.x
* [Pixivpy](https://github.com/upbit/pixivpy)
* PIL
* [waifu2x](https://github.com/lltcggie/waifu2x-caffe)

## TODO
* 将下载模块改为无需登陆
* 判断图片是否为白色背景的函数效率和可靠性较低
* 利用原图生成背景时，放大模糊处理之后是直接剪裁中间部分作为背景，可以考虑使用人脸识别或分析图片各部的复杂度来决定剪裁哪部分作为背景。