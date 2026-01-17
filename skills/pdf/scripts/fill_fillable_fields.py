import json
import sys

from pypdf import PdfReader, PdfWriter

from extract_form_field_info import get_field_info


# 填写 PDF 中的可填写表单字段。参见 forms.md。


def fill_pdf_fields(input_pdf_path: str, fields_json_path: str, output_pdf_path: str):
    with open(fields_json_path) as f:
        fields = json.load(f)
    # 按页码分组。
    fields_by_page = {}
    for field in fields:
        if "value" in field:
            field_id = field["field_id"]
            page = field["page"]
            if page not in fields_by_page:
                fields_by_page[page] = {}
            fields_by_page[page][field_id] = field["value"]

    reader = PdfReader(input_pdf_path)

    has_error = False
    field_info = get_field_info(reader)
    fields_by_ids = {f["field_id"]: f for f in field_info}
    for field in fields:
        existing_field = fields_by_ids.get(field["field_id"])
        if not existing_field:
            has_error = True
            print(f"错误: `{field['field_id']}` 不是有效的字段 ID")
        elif field["page"] != existing_field["page"]:
            has_error = True
            print(f"错误: `{field['field_id']}` 的页码不正确（得到 {field['page']}，期望 {existing_field['page']}）")
        else:
            if "value" in field:
                err = validation_error_for_field_value(existing_field, field["value"])
                if err:
                    print(err)
                    has_error = True
    if has_error:
        sys.exit(1)

    writer = PdfWriter(clone_from=reader)
    for page, field_values in fields_by_page.items():
        writer.update_page_form_field_values(writer.pages[page - 1], field_values, auto_regenerate=False)

    # 这似乎是许多 PDF 查看器正确格式化表单值所必需的。
    # 它可能导致查看器显示"保存更改"对话框，即使用户没有进行任何更改。
    writer.set_need_appearances_writer(True)

    with open(output_pdf_path, "wb") as f:
        writer.write(f)


def validation_error_for_field_value(field_info, field_value):
    field_type = field_info["type"]
    field_id = field_info["field_id"]
    if field_type == "checkbox":
        checked_val = field_info["checked_value"]
        unchecked_val = field_info["unchecked_value"]
        if field_value != checked_val and field_value != unchecked_val:
            return f'错误: 复选框字段 "{field_id}" 的值 "{field_value}" 无效。选中值为 "{checked_val}"，未选中值为 "{unchecked_val}"'
    elif field_type == "radio_group":
        option_values = [opt["value"] for opt in field_info["radio_options"]]
        if field_value not in option_values:
            return f'错误: 单选按钮组字段 "{field_id}" 的值 "{field_value}" 无效。有效值为: {option_values}'
    elif field_type == "choice":
        choice_values = [opt["value"] for opt in field_info["choice_options"]]
        if field_value not in choice_values:
            return f'错误: 选择字段 "{field_id}" 的值 "{field_value}" 无效。有效值为: {choice_values}'
    return None


# pypdf（至少版本 5.7.0）在设置选择列表字段值时有一个 bug。
# 在 _writer.py 大约第 966 行：
#
# if field.get(FA.FT, "/Tx") == "/Ch" and field_flags & FA.FfBits.Combo == 0:
#     txt = "\n".join(annotation.get_inherited(FA.Opt, []))
#
# 问题是对于选择列表，`get_inherited` 返回一个二元素列表的列表，如：
# [["value1", "Text 1"], ["value2", "Text 2"], ...]
# 这导致 `join` 抛出 TypeError，因为它期望一个字符串的可迭代对象。
# 糟糕的解决方法是修补 `get_inherited` 以返回值字符串的列表。
# 我们调用原始方法并仅在 `get_inherited` 的参数是 `FA.Opt`
# 且返回值是二元素列表的列表时调整返回值。
def monkeypatch_pydpf_method():
    from pypdf.generic import DictionaryObject
    from pypdf.constants import FieldDictionaryAttributes

    original_get_inherited = DictionaryObject.get_inherited

    def patched_get_inherited(self, key: str, default = None):
        result = original_get_inherited(self, key, default)
        if key == FieldDictionaryAttributes.Opt:
            if isinstance(result, list) and all(isinstance(v, list) and len(v) == 2 for v in result):
                result = [r[0] for r in result]
        return result

    DictionaryObject.get_inherited = patched_get_inherited


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("用法: fill_fillable_fields.py [输入 PDF] [field_values.json] [输出 PDF]")
        sys.exit(1)
    monkeypatch_pydpf_method()
    input_pdf = sys.argv[1]
    fields_json = sys.argv[2]
    output_pdf = sys.argv[3]
    fill_pdf_fields(input_pdf, fields_json, output_pdf)
