import json
import sys

from pypdf import PdfReader


# 提取 PDF 中可填写表单字段的数据，并输出 Claude 用于填写字段的 JSON。
# 参见 forms.md。


# 此格式与 PdfReader 的 `get_fields` 和 `update_page_form_field_values` 方法使用的格式匹配。
def get_full_annotation_field_id(annotation):
    components = []
    while annotation:
        field_name = annotation.get('/T')
        if field_name:
            components.append(field_name)
        annotation = annotation.get('/Parent')
    return ".".join(reversed(components)) if components else None


def make_field_dict(field, field_id):
    field_dict = {"field_id": field_id}
    ft = field.get('/FT')
    if ft == "/Tx":
        field_dict["type"] = "text"
    elif ft == "/Btn":
        field_dict["type"] = "checkbox"  # 单选按钮组单独处理
        states = field.get("/_States_", [])
        if len(states) == 2:
            # "/Off" 似乎总是未选中的值，如以下文档所述：
            # https://opensource.adobe.com/dc-acrobat-sdk-docs/standards/pdfstandards/pdf/PDF32000_2008.pdf#page=448
            # 它可以是 "/_States_" 列表中的第一个或第二个。
            if "/Off" in states:
                field_dict["checked_value"] = states[0] if states[0] != "/Off" else states[1]
                field_dict["unchecked_value"] = "/Off"
            else:
                print(f"复选框 `${field_id}` 的状态值异常。其选中和未选中的值可能不正确；如果您尝试选中它，请视觉验证结果。")
                field_dict["checked_value"] = states[0]
                field_dict["unchecked_value"] = states[1]
    elif ft == "/Ch":
        field_dict["type"] = "choice"
        states = field.get("/_States_", [])
        field_dict["choice_options"] = [{
            "value": state[0],
            "text": state[1],
        } for state in states]
    else:
        field_dict["type"] = f"unknown ({ft})"
    return field_dict


# 返回可填写 PDF 字段的列表：
# [
#   {
#     "field_id": "name",
#     "page": 1,
#     "type": ("text"、"checkbox"、"radio_group" 或 "choice")
#     // 每种类型的附加字段在 forms.md 中描述
#   },
# ]
def get_field_info(reader: PdfReader):
    fields = reader.get_fields()

    field_info_by_id = {}
    possible_radio_names = set()

    for field_id, field in fields.items():
        # 如果这是一个带有子元素的容器字段则跳过，但它可能是
        # 单选按钮选项的父组。
        if field.get("/Kids"):
            if field.get("/FT") == "/Btn":
                possible_radio_names.add(field_id)
            continue
        field_info_by_id[field_id] = make_field_dict(field, field_id)

    # 边界矩形存储在页面对象的注释中。

    # 单选按钮选项的每个选择都有单独的注释；
    # 所有选择都有相同的字段名称。
    # 参见 https://westhealth.github.io/exploring-fillable-forms-with-pdfrw.html
    radio_fields_by_id = {}

    for page_index, page in enumerate(reader.pages):
        annotations = page.get('/Annots', [])
        for ann in annotations:
            field_id = get_full_annotation_field_id(ann)
            if field_id in field_info_by_id:
                field_info_by_id[field_id]["page"] = page_index + 1
                field_info_by_id[field_id]["rect"] = ann.get('/Rect')
            elif field_id in possible_radio_names:
                try:
                    # ann['/AP']['/N'] 应该有两个项目。其中一个是 '/Off'，
                    # 另一个是激活值。
                    on_values = [v for v in ann["/AP"]["/N"] if v != "/Off"]
                except KeyError:
                    continue
                if len(on_values) == 1:
                    rect = ann.get("/Rect")
                    if field_id not in radio_fields_by_id:
                        radio_fields_by_id[field_id] = {
                            "field_id": field_id,
                            "type": "radio_group",
                            "page": page_index + 1,
                            "radio_options": [],
                        }
                    # 注意：至少在 macOS 15.7 上，Preview.app 无法正确显示已选择的
                    # 单选按钮。（如果删除值前面的斜杠，它会正确显示，但这会导致
                    # 在 Chrome/Firefox/Acrobat 等中无法正确显示）。
                    radio_fields_by_id[field_id]["radio_options"].append({
                        "value": on_values[0],
                        "rect": rect,
                    })

    # 某些 PDF 的表单字段定义没有对应的注释，
    # 所以我们无法确定它们的位置。暂时忽略这些字段。
    fields_with_location = []
    for field_info in field_info_by_id.values():
        if "page" in field_info:
            fields_with_location.append(field_info)
        else:
            print(f"无法确定字段 ID 的位置: {field_info.get('field_id')}，已忽略")

    # 按页码排序，然后按 Y 位置（PDF 坐标系中翻转），然后按 X。
    def sort_key(f):
        if "radio_options" in f:
            rect = f["radio_options"][0]["rect"] or [0, 0, 0, 0]
        else:
            rect = f.get("rect") or [0, 0, 0, 0]
        adjusted_position = [-rect[1], rect[0]]
        return [f.get("page"), adjusted_position]

    sorted_fields = fields_with_location + list(radio_fields_by_id.values())
    sorted_fields.sort(key=sort_key)

    return sorted_fields


def write_field_info(pdf_path: str, json_output_path: str):
    reader = PdfReader(pdf_path)
    field_info = get_field_info(reader)
    with open(json_output_path, "w") as f:
        json.dump(field_info, f, indent=2)
    print(f"已将 {len(field_info)} 个字段写入 {json_output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: extract_form_field_info.py [输入 PDF] [输出 JSON]")
        sys.exit(1)
    write_field_info(sys.argv[1], sys.argv[2])
