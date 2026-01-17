"""
用于根据 XSD 架构验证 PowerPoint 演示文稿 XML 文件的验证器。
"""

import re

from .base import BaseSchemaValidator


class PPTXSchemaValidator(BaseSchemaValidator):
    """用于根据 XSD 架构验证 PowerPoint 演示文稿 XML 文件的验证器。"""

    # PowerPoint 演示文稿命名空间
    PRESENTATIONML_NAMESPACE = (
        "http://schemas.openxmlformats.org/presentationml/2006/main"
    )

    # PowerPoint 特定元素到关系类型的映射
    ELEMENT_RELATIONSHIP_TYPES = {
        "sldid": "slide",
        "sldmasterid": "slidemaster",
        "notesmasterid": "notesmaster",
        "sldlayoutid": "slidelayout",
        "themeid": "theme",
        "tablestyleid": "tablestyles",
    }

    def validate(self):
        """运行所有验证检查，如果全部通过则返回 True。"""
        # 测试 0：XML 格式正确性
        if not self.validate_xml():
            return False

        # 测试 1：命名空间声明
        all_valid = True
        if not self.validate_namespaces():
            all_valid = False

        # 测试 2：唯一 ID
        if not self.validate_unique_ids():
            all_valid = False

        # 测试 3：UUID ID 验证
        if not self.validate_uuid_ids():
            all_valid = False

        # 测试 4：关系和文件引用验证
        if not self.validate_file_references():
            all_valid = False

        # 测试 5：幻灯片版式 ID 验证
        if not self.validate_slide_layout_ids():
            all_valid = False

        # 测试 6：内容类型声明
        if not self.validate_content_types():
            all_valid = False

        # 测试 7：XSD 架构验证
        if not self.validate_against_xsd():
            all_valid = False

        # 测试 8：备注幻灯片引用验证
        if not self.validate_notes_slide_references():
            all_valid = False

        # 测试 9：关系 ID 引用验证
        if not self.validate_all_relationship_ids():
            all_valid = False

        # 测试 10：重复幻灯片版式引用验证
        if not self.validate_no_duplicate_slide_layouts():
            all_valid = False

        return all_valid

    def validate_uuid_ids(self):
        """验证看起来像 UUID 的 ID 属性只包含十六进制值。"""
        import lxml.etree

        errors = []
        # UUID 模式：8-4-4-4-12 十六进制数字，可选花括号/连字符
        uuid_pattern = re.compile(
            r"^[\{\(]?[0-9A-Fa-f]{8}-?[0-9A-Fa-f]{4}-?[0-9A-Fa-f]{4}-?[0-9A-Fa-f]{4}-?[0-9A-Fa-f]{12}[\}\)]?$"
        )

        for xml_file in self.xml_files:
            try:
                root = lxml.etree.parse(str(xml_file)).getroot()

                # 检查所有元素的 ID 属性
                for elem in root.iter():
                    for attr, value in elem.attrib.items():
                        # 检查是否为 ID 属性
                        attr_name = attr.split("}")[-1].lower()
                        if attr_name == "id" or attr_name.endswith("id"):
                            # 检查值是否看起来像 UUID（具有正确的长度和模式结构）
                            if self._looks_like_uuid(value):
                                # 验证它在正确位置只包含十六进制字符
                                if not uuid_pattern.match(value):
                                    errors.append(
                                        f"  {xml_file.relative_to(self.unpacked_dir)}: "
                                        f"第 {elem.sourceline} 行: ID '{value}' 看起来像 UUID 但包含无效的十六进制字符"
                                    )

            except (lxml.etree.XMLSyntaxError, Exception) as e:
                errors.append(
                    f"  {xml_file.relative_to(self.unpacked_dir)}: 错误: {e}"
                )

        if errors:
            print(f"失败 - 发现 {len(errors)} 个 UUID ID 验证错误:")
            for error in errors:
                print(error)
            return False
        else:
            if self.verbose:
                print("通过 - 所有类 UUID 的 ID 都包含有效的十六进制值")
            return True

    def _looks_like_uuid(self, value):
        """检查值是否具有 UUID 的一般结构。"""
        # 移除常见的 UUID 分隔符
        clean_value = value.strip("{}()").replace("-", "")
        # 检查是否为 32 个类十六进制字符（可能包含无效的十六进制字符）
        return len(clean_value) == 32 and all(c.isalnum() for c in clean_value)

    def validate_slide_layout_ids(self):
        """验证幻灯片母版中的 sldLayoutId 元素引用的是有效的幻灯片版式。"""
        import lxml.etree

        errors = []

        # 查找所有幻灯片母版文件
        slide_masters = list(self.unpacked_dir.glob("ppt/slideMasters/*.xml"))

        if not slide_masters:
            if self.verbose:
                print("通过 - 未找到幻灯片母版")
            return True

        for slide_master in slide_masters:
            try:
                # 解析幻灯片母版文件
                root = lxml.etree.parse(str(slide_master)).getroot()

                # 查找此幻灯片母版对应的 _rels 文件
                rels_file = slide_master.parent / "_rels" / f"{slide_master.name}.rels"

                if not rels_file.exists():
                    errors.append(
                        f"  {slide_master.relative_to(self.unpacked_dir)}: "
                        f"缺少关系文件: {rels_file.relative_to(self.unpacked_dir)}"
                    )
                    continue

                # 解析关系文件
                rels_root = lxml.etree.parse(str(rels_file)).getroot()

                # 构建指向幻灯片版式的有效关系 ID 集合
                valid_layout_rids = set()
                for rel in rels_root.findall(
                    f".//{{{self.PACKAGE_RELATIONSHIPS_NAMESPACE}}}Relationship"
                ):
                    rel_type = rel.get("Type", "")
                    if "slideLayout" in rel_type:
                        valid_layout_rids.add(rel.get("Id"))

                # 查找幻灯片母版中的所有 sldLayoutId 元素
                for sld_layout_id in root.findall(
                    f".//{{{self.PRESENTATIONML_NAMESPACE}}}sldLayoutId"
                ):
                    r_id = sld_layout_id.get(
                        f"{{{self.OFFICE_RELATIONSHIPS_NAMESPACE}}}id"
                    )
                    layout_id = sld_layout_id.get("id")

                    if r_id and r_id not in valid_layout_rids:
                        errors.append(
                            f"  {slide_master.relative_to(self.unpacked_dir)}: "
                            f"第 {sld_layout_id.sourceline} 行: id='{layout_id}' 的 sldLayoutId "
                            f"引用的 r:id='{r_id}' 在幻灯片版式关系中未找到"
                        )

            except (lxml.etree.XMLSyntaxError, Exception) as e:
                errors.append(
                    f"  {slide_master.relative_to(self.unpacked_dir)}: 错误: {e}"
                )

        if errors:
            print(f"失败 - 发现 {len(errors)} 个幻灯片版式 ID 验证错误:")
            for error in errors:
                print(error)
            print(
                "请移除无效引用或将缺失的幻灯片版式添加到关系文件中。"
            )
            return False
        else:
            if self.verbose:
                print("通过 - 所有幻灯片版式 ID 都引用有效的幻灯片版式")
            return True

    def validate_no_duplicate_slide_layouts(self):
        """验证每个幻灯片只有一个 slideLayout 引用。"""
        import lxml.etree

        errors = []
        slide_rels_files = list(self.unpacked_dir.glob("ppt/slides/_rels/*.xml.rels"))

        for rels_file in slide_rels_files:
            try:
                root = lxml.etree.parse(str(rels_file)).getroot()

                # 查找所有 slideLayout 关系
                layout_rels = [
                    rel
                    for rel in root.findall(
                        f".//{{{self.PACKAGE_RELATIONSHIPS_NAMESPACE}}}Relationship"
                    )
                    if "slideLayout" in rel.get("Type", "")
                ]

                if len(layout_rels) > 1:
                    errors.append(
                        f"  {rels_file.relative_to(self.unpacked_dir)}: 有 {len(layout_rels)} 个 slideLayout 引用"
                    )

            except Exception as e:
                errors.append(
                    f"  {rels_file.relative_to(self.unpacked_dir)}: 错误: {e}"
                )

        if errors:
            print("失败 - 发现包含重复 slideLayout 引用的幻灯片:")
            for error in errors:
                print(error)
            return False
        else:
            if self.verbose:
                print("通过 - 所有幻灯片都只有一个 slideLayout 引用")
            return True

    def validate_notes_slide_references(self):
        """验证每个 notesSlide 文件只被一个幻灯片引用。"""
        import lxml.etree

        errors = []
        notes_slide_references = {}  # 跟踪哪些幻灯片引用每个 notesSlide

        # 查找所有幻灯片关系文件
        slide_rels_files = list(self.unpacked_dir.glob("ppt/slides/_rels/*.xml.rels"))

        if not slide_rels_files:
            if self.verbose:
                print("通过 - 未找到幻灯片关系文件")
            return True

        for rels_file in slide_rels_files:
            try:
                # 解析关系文件
                root = lxml.etree.parse(str(rels_file)).getroot()

                # 查找所有 notesSlide 关系
                for rel in root.findall(
                    f".//{{{self.PACKAGE_RELATIONSHIPS_NAMESPACE}}}Relationship"
                ):
                    rel_type = rel.get("Type", "")
                    if "notesSlide" in rel_type:
                        target = rel.get("Target", "")
                        if target:
                            # 规范化目标路径以处理相对路径
                            normalized_target = target.replace("../", "")

                            # 跟踪哪个幻灯片引用此 notesSlide
                            slide_name = rels_file.stem.replace(
                                ".xml", ""
                            )  # 例如 "slide1"

                            if normalized_target not in notes_slide_references:
                                notes_slide_references[normalized_target] = []
                            notes_slide_references[normalized_target].append(
                                (slide_name, rels_file)
                            )

            except (lxml.etree.XMLSyntaxError, Exception) as e:
                errors.append(
                    f"  {rels_file.relative_to(self.unpacked_dir)}: 错误: {e}"
                )

        # 检查重复引用
        for target, references in notes_slide_references.items():
            if len(references) > 1:
                slide_names = [ref[0] for ref in references]
                errors.append(
                    f"  备注幻灯片 '{target}' 被多个幻灯片引用: {', '.join(slide_names)}"
                )
                for slide_name, rels_file in references:
                    errors.append(f"    - {rels_file.relative_to(self.unpacked_dir)}")

        if errors:
            print(
                f"失败 - 发现 {len([e for e in errors if not e.startswith('    ')])} 个备注幻灯片引用验证错误:"
            )
            for error in errors:
                print(error)
            print("每个幻灯片可以选择性地拥有自己的备注幻灯片文件。")
            return False
        else:
            if self.verbose:
                print("通过 - 所有备注幻灯片引用都是唯一的")
            return True


if __name__ == "__main__":
    raise RuntimeError("此模块不应直接运行。")
