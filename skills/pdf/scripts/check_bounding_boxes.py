from dataclasses import dataclass
import json
import sys


# 用于检查 Claude 在分析 PDF 时创建的 `fields.json` 文件
# 是否存在重叠的边界框。参见 forms.md。


@dataclass
class RectAndField:
    rect: list[float]
    rect_type: str
    field: dict


# 返回打印到标准输出供 Claude 读取的消息列表。
def get_bounding_box_messages(fields_json_stream) -> list[str]:
    messages = []
    fields = json.load(fields_json_stream)
    messages.append(f"读取了 {len(fields['form_fields'])} 个字段")

    def rects_intersect(r1, r2):
        disjoint_horizontal = r1[0] >= r2[2] or r1[2] <= r2[0]
        disjoint_vertical = r1[1] >= r2[3] or r1[3] <= r2[1]
        return not (disjoint_horizontal or disjoint_vertical)

    rects_and_fields = []
    for f in fields["form_fields"]:
        rects_and_fields.append(RectAndField(f["label_bounding_box"], "label", f))
        rects_and_fields.append(RectAndField(f["entry_bounding_box"], "entry", f))

    has_error = False
    for i, ri in enumerate(rects_and_fields):
        # 这是 O(N^2) 复杂度；如果成为问题可以优化。
        for j in range(i + 1, len(rects_and_fields)):
            rj = rects_and_fields[j]
            if ri.field["page_number"] == rj.field["page_number"] and rects_intersect(ri.rect, rj.rect):
                has_error = True
                if ri.field is rj.field:
                    messages.append(f"失败: `{ri.field['description']}` 的标签和输入边界框相交 ({ri.rect}, {rj.rect})")
                else:
                    messages.append(f"失败: `{ri.field['description']}` 的 {ri.rect_type} 边界框 ({ri.rect}) 与 `{rj.field['description']}` 的 {rj.rect_type} 边界框 ({rj.rect}) 相交")
                if len(messages) >= 20:
                    messages.append("中止进一步检查；请修复边界框后重试")
                    return messages
        if ri.rect_type == "entry":
            if "entry_text" in ri.field:
                font_size = ri.field["entry_text"].get("font_size", 14)
                entry_height = ri.rect[3] - ri.rect[1]
                if entry_height < font_size:
                    has_error = True
                    messages.append(f"失败: `{ri.field['description']}` 的输入边界框高度 ({entry_height}) 对于文本内容来说太小（字体大小: {font_size}）。请增加框高度或减小字体大小。")
                    if len(messages) >= 20:
                        messages.append("中止进一步检查；请修复边界框后重试")
                        return messages

    if not has_error:
        messages.append("成功: 所有边界框均有效")
    return messages

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: check_bounding_boxes.py [fields.json]")
        sys.exit(1)
    # 输入文件应为 forms.md 中描述的 `fields.json` 格式。
    with open(sys.argv[1]) as f:
        messages = get_bounding_box_messages(f)
    for msg in messages:
        print(msg)
