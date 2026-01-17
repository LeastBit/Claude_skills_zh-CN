import json
import sys

from PIL import Image, ImageDraw


# 创建"验证"图像，其中包含 Claude 在确定 PDF 中添加文本注释位置时
# 创建的边界框信息的矩形。参见 forms.md。


def create_validation_image(page_number, fields_json_path, input_path, output_path):
    # 输入文件应为 forms.md 中描述的 `fields.json` 格式。
    with open(fields_json_path, 'r') as f:
        data = json.load(f)

        img = Image.open(input_path)
        draw = ImageDraw.Draw(img)
        num_boxes = 0

        for field in data["form_fields"]:
            if field["page_number"] == page_number:
                entry_box = field['entry_bounding_box']
                label_box = field['label_bounding_box']
                # 在输入边界框上绘制红色矩形，在标签上绘制蓝色矩形。
                draw.rectangle(entry_box, outline='red', width=2)
                draw.rectangle(label_box, outline='blue', width=2)
                num_boxes += 2

        img.save(output_path)
        print(f"已在 {output_path} 创建验证图像，包含 {num_boxes} 个边界框")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("用法: create_validation_image.py [页码] [fields.json 文件] [输入图像路径] [输出图像路径]")
        sys.exit(1)
    page_number = int(sys.argv[1])
    fields_json_path = sys.argv[2]
    input_image_path = sys.argv[3]
    output_image_path = sys.argv[4]
    create_validation_image(page_number, fields_json_path, input_image_path, output_image_path)
