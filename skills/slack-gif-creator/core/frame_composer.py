#!/usr/bin/env python3
"""
帧合成器 - 用于将视觉元素合成到帧中的工具。

提供绘制形状、文字、表情符号以及将元素组合在一起以创建动画帧的函数。
"""

from typing import Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def create_blank_frame(
    width: int, height: int, color: tuple[int, int, int] = (255, 255, 255)
) -> Image.Image:
    """
    创建纯色背景的空白帧。

    参数：
        width: 帧宽度
        height: 帧高度
        color: RGB 颜色元组（默认：白色）

    返回：
        PIL Image
    """
    return Image.new("RGB", (width, height), color)


def draw_circle(
    frame: Image.Image,
    center: tuple[int, int],
    radius: int,
    fill_color: Optional[tuple[int, int, int]] = None,
    outline_color: Optional[tuple[int, int, int]] = None,
    outline_width: int = 1,
) -> Image.Image:
    """
    在帧上绘制圆形。

    参数：
        frame: 要绘制的 PIL Image
        center: (x, y) 中心位置
        radius: 圆的半径
        fill_color: RGB 填充颜色（None 表示不填充）
        outline_color: RGB 轮廓颜色（None 表示无轮廓）
        outline_width: 轮廓宽度（像素）

    返回：
        修改后的帧
    """
    draw = ImageDraw.Draw(frame)
    x, y = center
    bbox = [x - radius, y - radius, x + radius, y + radius]
    draw.ellipse(bbox, fill=fill_color, outline=outline_color, width=outline_width)
    return frame


def draw_text(
    frame: Image.Image,
    text: str,
    position: tuple[int, int],
    color: tuple[int, int, int] = (0, 0, 0),
    centered: bool = False,
) -> Image.Image:
    """
    在帧上绘制文字。

    参数：
        frame: 要绘制的 PIL Image
        text: 要绘制的文字
        position: (x, y) 位置（左上角，除非 centered=True）
        color: RGB 文字颜色
        centered: 如果为 True，则将文字居中于该位置

    返回：
        修改后的帧
    """
    draw = ImageDraw.Draw(frame)

    # 使用 Pillow 的默认字体。
    # 如果需要为表情符号更改字体，请在此处添加额外逻辑。
    font = ImageFont.load_default()

    if centered:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = position[0] - text_width // 2
        y = position[1] - text_height // 2
        position = (x, y)

    draw.text(position, text, fill=color, font=font)
    return frame


def create_gradient_background(
    width: int,
    height: int,
    top_color: tuple[int, int, int],
    bottom_color: tuple[int, int, int],
) -> Image.Image:
    """
    创建垂直渐变背景。

    参数：
        width: 帧宽度
        height: 帧高度
        top_color: 顶部的 RGB 颜色
        bottom_color: 底部的 RGB 颜色

    返回：
        带有渐变的 PIL Image
    """
    frame = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(frame)

    # 计算每行的颜色步进
    r1, g1, b1 = top_color
    r2, g2, b2 = bottom_color

    for y in range(height):
        # 插值颜色
        ratio = y / height
        r = int(r1 * (1 - ratio) + r2 * ratio)
        g = int(g1 * (1 - ratio) + g2 * ratio)
        b = int(b1 * (1 - ratio) + b2 * ratio)

        # 绘制水平线
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    return frame


def draw_star(
    frame: Image.Image,
    center: tuple[int, int],
    size: int,
    fill_color: tuple[int, int, int],
    outline_color: Optional[tuple[int, int, int]] = None,
    outline_width: int = 1,
) -> Image.Image:
    """
    绘制五角星。

    参数：
        frame: 要绘制的 PIL Image
        center: (x, y) 中心位置
        size: 星形大小（外半径）
        fill_color: RGB 填充颜色
        outline_color: RGB 轮廓颜色（None 表示无轮廓）
        outline_width: 轮廓宽度

    返回：
        修改后的帧
    """
    import math

    draw = ImageDraw.Draw(frame)
    x, y = center

    # 计算星形顶点
    points = []
    for i in range(10):
        angle = (i * 36 - 90) * math.pi / 180  # 每个顶点 36 度，从顶部开始
        radius = size if i % 2 == 0 else size * 0.4  # 交替使用外半径和内半径
        px = x + radius * math.cos(angle)
        py = y + radius * math.sin(angle)
        points.append((px, py))

    # 绘制星形
    draw.polygon(points, fill=fill_color, outline=outline_color, width=outline_width)

    return frame
