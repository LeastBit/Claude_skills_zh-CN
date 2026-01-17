import json
import sys

from pypdf import PdfReader, PdfWriter
from pypdf.annotations import FreeText


# 通过添加 `fields.json` 中定义的文本注释来填写 PDF。参见 forms.md。


def transform_coordinates(bbox, image_width, image_height, pdf_width, pdf_height):
    """将边界框从图像坐标转换为 PDF 坐标"""
    # 图像坐标：原点在左上角，y 向下增加
    # PDF 坐标：原点在左下角，y 向上增加
    x_scale = pdf_width / image_width
    y_scale = pdf_height / image_height

    left = bbox[0] * x_scale
    right = bbox[2] * x_scale

    # 翻转 Y 坐标以适应 PDF
    top = pdf_height - (bbox[1] * y_scale)
    bottom = pdf_height - (bbox[3] * y_scale)

    return left, bottom, right, top


def fill_pdf_form(input_pdf_path, fields_json_path, output_pdf_path):
    """使用 fields.json 中的数据填写 PDF 表单"""

    # `fields.json` 格式在 forms.md 中描述。
    with open(fields_json_path, "r") as f:
        fields_data = json.load(f)

    # 打开 PDF
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()

    # 将所有页面复制到 writer
    writer.append(reader)

    # 获取每页的 PDF 尺寸
    pdf_dimensions = {}
    for i, page in enumerate(reader.pages):
        mediabox = page.mediabox
        pdf_dimensions[i + 1] = [mediabox.width, mediabox.height]

    # 处理每个表单字段
    annotations = []
    for field in fields_data["form_fields"]:
        page_num = field["page_number"]

        # 获取页面尺寸并转换坐标。
        page_info = next(p for p in fields_data["pages"] if p["page_number"] == page_num)
        image_width = page_info["image_width"]
        image_height = page_info["image_height"]
        pdf_width, pdf_height = pdf_dimensions[page_num]

        transformed_entry_box = transform_coordinates(
            field["entry_bounding_box"],
            image_width, image_height,
            pdf_width, pdf_height
        )

        # 跳过空字段
        if "entry_text" not in field or "text" not in field["entry_text"]:
            continue
        entry_text = field["entry_text"]
        text = entry_text["text"]
        if not text:
            continue

        font_name = entry_text.get("font", "Arial")
        font_size = str(entry_text.get("font_size", 14)) + "pt"
        font_color = entry_text.get("font_color", "000000")

        # 字体大小/颜色在不同查看器中似乎不能可靠工作：
        # https://github.com/py-pdf/pypdf/issues/2084
        annotation = FreeText(
            text=text,
            rect=transformed_entry_box,
            font=font_name,
            font_size=font_size,
            font_color=font_color,
            border_color=None,
            background_color=None,
        )
        annotations.append(annotation)
        # pypdf 的 page_number 从 0 开始
        writer.add_annotation(page_number=page_num - 1, annotation=annotation)

    # 保存已填写的 PDF
    with open(output_pdf_path, "wb") as output:
        writer.write(output)

    print(f"已成功填写 PDF 表单并保存到 {output_pdf_path}")
    print(f"添加了 {len(annotations)} 个文本注释")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("用法: fill_pdf_form_with_annotations.py [输入 PDF] [fields.json] [输出 PDF]")
        sys.exit(1)
    input_pdf = sys.argv[1]
    fields_json = sys.argv[2]
    output_pdf = sys.argv[3]

    fill_pdf_form(input_pdf, fields_json, output_pdf)
