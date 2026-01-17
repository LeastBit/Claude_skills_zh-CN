import os
import sys

from pdf2image import convert_from_path


# 将 PDF 的每一页转换为 PNG 图像。


def convert(pdf_path, output_dir, max_dim=1000):
    images = convert_from_path(pdf_path, dpi=200)

    for i, image in enumerate(images):
        # 如果需要，缩放图像以保持宽度/高度在 `max_dim` 以下
        width, height = image.size
        if width > max_dim or height > max_dim:
            scale_factor = min(max_dim / width, max_dim / height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height))

        image_path = os.path.join(output_dir, f"page_{i+1}.png")
        image.save(image_path)
        print(f"已将第 {i+1} 页保存为 {image_path}（尺寸: {image.size}）")

    print(f"已将 {len(images)} 页转换为 PNG 图像")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: convert_pdf_to_images.py [输入 PDF] [输出目录]")
        sys.exit(1)
    pdf_path = sys.argv[1]
    output_directory = sys.argv[2]
    convert(pdf_path, output_directory)
