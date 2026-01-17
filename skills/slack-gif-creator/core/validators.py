#!/usr/bin/env python3
"""
验证器 - 检查 GIF 是否符合 Slack 的要求。

这些验证器帮助确保您的 GIF 符合 Slack 的大小和尺寸限制。
"""

from pathlib import Path


def validate_gif(
    gif_path: str | Path, is_emoji: bool = True, verbose: bool = True
) -> tuple[bool, dict]:
    """
    验证 GIF 是否适用于 Slack（尺寸、大小、帧数）。

    参数：
        gif_path: GIF 文件路径
        is_emoji: 对于表情符号为 True（推荐 128x128），对于消息 GIF 为 False
        verbose: 打印验证详情

    返回：
        元组 (passes: bool, results: dict 包含所有详情)
    """
    from PIL import Image

    gif_path = Path(gif_path)

    if not gif_path.exists():
        return False, {"error": f"文件未找到：{gif_path}"}

    # 获取文件大小
    size_bytes = gif_path.stat().st_size
    size_kb = size_bytes / 1024
    size_mb = size_kb / 1024

    # 获取尺寸和帧信息
    try:
        with Image.open(gif_path) as img:
            width, height = img.size

            # 计算帧数
            frame_count = 0
            try:
                while True:
                    img.seek(frame_count)
                    frame_count += 1
            except EOFError:
                pass

            # 获取持续时间
            try:
                duration_ms = img.info.get("duration", 100)
                total_duration = (duration_ms * frame_count) / 1000
                fps = frame_count / total_duration if total_duration > 0 else 0
            except:
                total_duration = None
                fps = None

    except Exception as e:
        return False, {"error": f"无法读取 GIF：{e}"}

    # 验证尺寸
    if is_emoji:
        optimal = width == height == 128
        acceptable = width == height and 64 <= width <= 128
        dim_pass = acceptable
    else:
        aspect_ratio = (
            max(width, height) / min(width, height)
            if min(width, height) > 0
            else float("inf")
        )
        dim_pass = aspect_ratio <= 2.0 and 320 <= min(width, height) <= 640

    results = {
        "file": str(gif_path),
        "passes": dim_pass,
        "width": width,
        "height": height,
        "size_kb": size_kb,
        "size_mb": size_mb,
        "frame_count": frame_count,
        "duration_seconds": total_duration,
        "fps": fps,
        "is_emoji": is_emoji,
        "optimal": optimal if is_emoji else None,
    }

    # 如果 verbose 则打印
    if verbose:
        print(f"\n正在验证 {gif_path.name}：")
        print(
            f"  尺寸：{width}x{height}"
            + (
                f"（{'最优' if optimal else '可接受'}）"
                if is_emoji and acceptable
                else ""
            )
        )
        print(
            f"  大小：{size_kb:.1f} KB"
            + (f"（{size_mb:.2f} MB）" if size_mb >= 1.0 else "")
        )
        print(
            f"  帧数：{frame_count}"
            + (f" @ {fps:.1f} fps（{total_duration:.1f} 秒）" if fps else "")
        )

        if not dim_pass:
            print(
                f"  注意：{'表情符号应为 128x128' if is_emoji else '对于 Slack 来说尺寸不常见'}"
            )

        if size_mb > 5.0:
            print(f"  注意：文件较大 - 建议减少帧数/颜色")

    return dim_pass, results


def is_slack_ready(
    gif_path: str | Path, is_emoji: bool = True, verbose: bool = True
) -> bool:
    """
    快速检查 GIF 是否可用于 Slack。

    参数：
        gif_path: GIF 文件路径
        is_emoji: 对于表情符号 GIF 为 True，对于消息 GIF 为 False
        verbose: 打印反馈

    返回：
        如果尺寸可接受则为 True
    """
    passes, _ = validate_gif(gif_path, is_emoji, verbose)
    return passes
