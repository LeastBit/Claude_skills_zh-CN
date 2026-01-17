#!/usr/bin/env python3
"""
GIF 构建器 - 用于将帧组装成针对 Slack 优化的 GIF 的核心模块。

此模块提供了从程序生成的帧创建 GIF 的主要接口，
并自动针对 Slack 的要求进行优化。
"""

from pathlib import Path
from typing import Optional

import imageio.v3 as imageio
import numpy as np
from PIL import Image


class GIFBuilder:
    """用于从帧创建优化 GIF 的构建器。"""

    def __init__(self, width: int = 480, height: int = 480, fps: int = 15):
        """
        初始化 GIF 构建器。

        参数：
            width: 帧宽度（像素）
            height: 帧高度（像素）
            fps: 每秒帧数
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.frames: list[np.ndarray] = []

    def add_frame(self, frame: np.ndarray | Image.Image):
        """
        向 GIF 添加一帧。

        参数：
            frame: numpy 数组或 PIL Image 格式的帧（将转换为 RGB）
        """
        if isinstance(frame, Image.Image):
            frame = np.array(frame.convert("RGB"))

        # 确保帧尺寸正确
        if frame.shape[:2] != (self.height, self.width):
            pil_frame = Image.fromarray(frame)
            pil_frame = pil_frame.resize(
                (self.width, self.height), Image.Resampling.LANCZOS
            )
            frame = np.array(pil_frame)

        self.frames.append(frame)

    def add_frames(self, frames: list[np.ndarray | Image.Image]):
        """一次添加多个帧。"""
        for frame in frames:
            self.add_frame(frame)

    def optimize_colors(
        self, num_colors: int = 128, use_global_palette: bool = True
    ) -> list[np.ndarray]:
        """
        使用量化减少所有帧的颜色数量。

        参数：
            num_colors: 目标颜色数量（8-256）
            use_global_palette: 对所有帧使用单一调色板（压缩效果更好）

        返回：
            颜色优化后的帧列表
        """
        optimized = []

        if use_global_palette and len(self.frames) > 1:
            # 从所有帧创建全局调色板
            # 采样帧以构建调色板
            sample_size = min(5, len(self.frames))
            sample_indices = [
                int(i * len(self.frames) / sample_size) for i in range(sample_size)
            ]
            sample_frames = [self.frames[i] for i in sample_indices]

            # 将采样帧合并成单个图像用于调色板生成
            # 将每帧展平以获取所有像素，然后堆叠
            all_pixels = np.vstack(
                [f.reshape(-1, 3) for f in sample_frames]
            )  # (总像素数, 3)

            # 从像素数据创建正确形状的 RGB 图像
            # 我们将从所有像素创建一个大致为方形的图像
            total_pixels = len(all_pixels)
            width = min(512, int(np.sqrt(total_pixels)))  # 合理的宽度，最大 512
            height = (total_pixels + width - 1) // width  # 向上取整除法

            # 如果需要，填充以填满矩形
            pixels_needed = width * height
            if pixels_needed > total_pixels:
                padding = np.zeros((pixels_needed - total_pixels, 3), dtype=np.uint8)
                all_pixels = np.vstack([all_pixels, padding])

            # 重塑为正确的 RGB 图像格式 (H, W, 3)
            img_array = (
                all_pixels[:pixels_needed].reshape(height, width, 3).astype(np.uint8)
            )
            combined_img = Image.fromarray(img_array, mode="RGB")

            # 生成全局调色板
            global_palette = combined_img.quantize(colors=num_colors, method=2)

            # 将全局调色板应用于所有帧
            for frame in self.frames:
                pil_frame = Image.fromarray(frame)
                quantized = pil_frame.quantize(palette=global_palette, dither=1)
                optimized.append(np.array(quantized.convert("RGB")))
        else:
            # 使用逐帧量化
            for frame in self.frames:
                pil_frame = Image.fromarray(frame)
                quantized = pil_frame.quantize(colors=num_colors, method=2, dither=1)
                optimized.append(np.array(quantized.convert("RGB")))

        return optimized

    def deduplicate_frames(self, threshold: float = 0.9995) -> int:
        """
        移除重复或近似重复的连续帧。

        参数：
            threshold: 相似度阈值（0.0-1.0）。越高越严格（0.9995 = 几乎相同）。
                      使用 0.9995+ 保留细微动画，使用 0.98 进行激进移除。

        返回：
            移除的帧数
        """
        if len(self.frames) < 2:
            return 0

        deduplicated = [self.frames[0]]
        removed_count = 0

        for i in range(1, len(self.frames)):
            # 与前一帧比较
            prev_frame = np.array(deduplicated[-1], dtype=np.float32)
            curr_frame = np.array(self.frames[i], dtype=np.float32)

            # 计算相似度（归一化）
            diff = np.abs(prev_frame - curr_frame)
            similarity = 1.0 - (np.mean(diff) / 255.0)

            # 如果差异足够大则保留帧
            # 高阈值（0.9995+）意味着只移除几乎相同的帧
            if similarity < threshold:
                deduplicated.append(self.frames[i])
            else:
                removed_count += 1

        self.frames = deduplicated
        return removed_count

    def save(
        self,
        output_path: str | Path,
        num_colors: int = 128,
        optimize_for_emoji: bool = False,
        remove_duplicates: bool = False,
    ) -> dict:
        """
        将帧保存为针对 Slack 优化的 GIF。

        参数：
            output_path: GIF 保存路径
            num_colors: 使用的颜色数量（越少 = 文件越小）
            optimize_for_emoji: 如果为 True，针对表情符号尺寸优化（128x128，更少颜色）
            remove_duplicates: 如果为 True，移除重复的连续帧（可选启用）

        返回：
            包含文件信息的字典（path、size、dimensions、frame_count）
        """
        if not self.frames:
            raise ValueError("没有帧可保存。请先使用 add_frame() 添加帧。")

        output_path = Path(output_path)

        # 移除重复帧以减小文件大小
        if remove_duplicates:
            removed = self.deduplicate_frames(threshold=0.9995)
            if removed > 0:
                print(
                    f"  移除了 {removed} 个几乎相同的帧（保留了细微动画）"
                )

        # 如果请求，针对表情符号优化
        if optimize_for_emoji:
            if self.width > 128 or self.height > 128:
                print(
                    f"  正在将尺寸从 {self.width}x{self.height} 调整为 128x128 以适配表情符号"
                )
                self.width = 128
                self.height = 128
                # 调整所有帧的大小
                resized_frames = []
                for frame in self.frames:
                    pil_frame = Image.fromarray(frame)
                    pil_frame = pil_frame.resize((128, 128), Image.Resampling.LANCZOS)
                    resized_frames.append(np.array(pil_frame))
                self.frames = resized_frames
            num_colors = min(num_colors, 48)  # 表情符号使用更激进的颜色限制

            # 表情符号使用更激进的 FPS 降低
            if len(self.frames) > 12:
                print(
                    f"  正在将帧数从 {len(self.frames)} 减少到约 12 以适配表情符号大小"
                )
                # 保留每第 n 帧以接近 12 帧
                keep_every = max(1, len(self.frames) // 12)
                self.frames = [
                    self.frames[i] for i in range(0, len(self.frames), keep_every)
                ]

        # 使用全局调色板优化颜色
        optimized_frames = self.optimize_colors(num_colors, use_global_palette=True)

        # 计算帧持续时间（毫秒）
        frame_duration = 1000 / self.fps

        # 保存 GIF
        imageio.imwrite(
            output_path,
            optimized_frames,
            duration=frame_duration,
            loop=0,  # 无限循环
        )

        # 获取文件信息
        file_size_kb = output_path.stat().st_size / 1024
        file_size_mb = file_size_kb / 1024

        info = {
            "path": str(output_path),
            "size_kb": file_size_kb,
            "size_mb": file_size_mb,
            "dimensions": f"{self.width}x{self.height}",
            "frame_count": len(optimized_frames),
            "fps": self.fps,
            "duration_seconds": len(optimized_frames) / self.fps,
            "colors": num_colors,
        }

        # 打印信息
        print(f"\n✓ GIF 创建成功！")
        print(f"  路径：{output_path}")
        print(f"  大小：{file_size_kb:.1f} KB（{file_size_mb:.2f} MB）")
        print(f"  尺寸：{self.width}x{self.height}")
        print(f"  帧数：{len(optimized_frames)} @ {self.fps} fps")
        print(f"  时长：{info['duration_seconds']:.1f} 秒")
        print(f"  颜色：{num_colors}")

        # 大小信息
        if optimize_for_emoji:
            print(f"  已针对表情符号优化（128x128，减少颜色）")
        if file_size_mb > 1.0:
            print(f"\n  注意：文件较大（{file_size_kb:.1f} KB）")
            print("  建议：减少帧数、缩小尺寸或减少颜色")

        return info

    def clear(self):
        """清除所有帧（用于创建多个 GIF 时很有用）。"""
        self.frames = []
