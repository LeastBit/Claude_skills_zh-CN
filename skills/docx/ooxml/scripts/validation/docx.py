"""
用于根据 XSD 架构验证 Word 文档 XML 文件的验证器。
"""

import re
import tempfile
import zipfile

import lxml.etree

from .base import BaseSchemaValidator


class DOCXSchemaValidator(BaseSchemaValidator):
    """用于根据 XSD 架构验证 Word 文档 XML 文件的验证器。"""

    # Word 特定命名空间
    WORD_2006_NAMESPACE = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

    # Word 特定元素到关系类型的映射
    # 从空映射开始 - 在发现具体情况时添加
    ELEMENT_RELATIONSHIP_TYPES = {}

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

        # 测试 3：关系和文件引用验证
        if not self.validate_file_references():
            all_valid = False

        # 测试 4：内容类型声明
        if not self.validate_content_types():
            all_valid = False

        # 测试 5：XSD 架构验证
        if not self.validate_against_xsd():
            all_valid = False

        # 测试 6：空白保留
        if not self.validate_whitespace_preservation():
            all_valid = False

        # 测试 7：删除验证
        if not self.validate_deletions():
            all_valid = False

        # 测试 8：插入验证
        if not self.validate_insertions():
            all_valid = False

        # 测试 9：关系 ID 引用验证
        if not self.validate_all_relationship_ids():
            all_valid = False

        # 计算和比较段落数
        self.compare_paragraph_counts()

        return all_valid

    def validate_whitespace_preservation(self):
        """
        验证包含空白的 w:t 元素是否有 xml:space='preserve' 属性。
        """
        errors = []

        for xml_file in self.xml_files:
            # 只检查 document.xml 文件
            if xml_file.name != "document.xml":
                continue

            try:
                root = lxml.etree.parse(str(xml_file)).getroot()

                # 查找所有 w:t 元素
                for elem in root.iter(f"{{{self.WORD_2006_NAMESPACE}}}t"):
                    if elem.text:
                        text = elem.text
                        # 检查文本是否以空白开头或结尾
                        if re.match(r"^\s.*", text) or re.match(r".*\s$", text):
                            # 检查是否存在 xml:space="preserve" 属性
                            xml_space_attr = f"{{{self.XML_NAMESPACE}}}space"
                            if (
                                xml_space_attr not in elem.attrib
                                or elem.attrib[xml_space_attr] != "preserve"
                            ):
                                # 显示文本预览
                                text_preview = (
                                    repr(text)[:50] + "..."
                                    if len(repr(text)) > 50
                                    else repr(text)
                                )
                                errors.append(
                                    f"  {xml_file.relative_to(self.unpacked_dir)}: "
                                    f"第 {elem.sourceline} 行: 包含空白的 w:t 元素缺少 xml:space='preserve': {text_preview}"
                                )

            except (lxml.etree.XMLSyntaxError, Exception) as e:
                errors.append(
                    f"  {xml_file.relative_to(self.unpacked_dir)}: 错误: {e}"
                )

        if errors:
            print(f"失败 - 发现 {len(errors)} 个空白保留违规:")
            for error in errors:
                print(error)
            return False
        else:
            if self.verbose:
                print("通过 - 所有空白都已正确保留")
            return True

    def validate_deletions(self):
        """
        验证 w:t 元素不在 w:del 元素内。
        由于某种原因，XSD 验证无法捕获此问题，因此我们手动检查。
        """
        errors = []

        for xml_file in self.xml_files:
            # 只检查 document.xml 文件
            if xml_file.name != "document.xml":
                continue

            try:
                root = lxml.etree.parse(str(xml_file)).getroot()

                # 查找所有作为 w:del 元素后代的 w:t 元素
                namespaces = {"w": self.WORD_2006_NAMESPACE}
                xpath_expression = ".//w:del//w:t"
                problematic_t_elements = root.xpath(
                    xpath_expression, namespaces=namespaces
                )
                for t_elem in problematic_t_elements:
                    if t_elem.text:
                        # 显示文本预览
                        text_preview = (
                            repr(t_elem.text)[:50] + "..."
                            if len(repr(t_elem.text)) > 50
                            else repr(t_elem.text)
                        )
                        errors.append(
                            f"  {xml_file.relative_to(self.unpacked_dir)}: "
                            f"第 {t_elem.sourceline} 行: 在 <w:del> 内发现 <w:t>: {text_preview}"
                        )

            except (lxml.etree.XMLSyntaxError, Exception) as e:
                errors.append(
                    f"  {xml_file.relative_to(self.unpacked_dir)}: 错误: {e}"
                )

        if errors:
            print(f"失败 - 发现 {len(errors)} 个删除验证违规:")
            for error in errors:
                print(error)
            return False
        else:
            if self.verbose:
                print("通过 - 在 w:del 元素内未发现 w:t 元素")
            return True

    def count_paragraphs_in_unpacked(self):
        """计算解压文档中的段落数。"""
        count = 0

        for xml_file in self.xml_files:
            # 只检查 document.xml 文件
            if xml_file.name != "document.xml":
                continue

            try:
                root = lxml.etree.parse(str(xml_file)).getroot()
                # 计算所有 w:p 元素
                paragraphs = root.findall(f".//{{{self.WORD_2006_NAMESPACE}}}p")
                count = len(paragraphs)
            except Exception as e:
                print(f"计算解压文档中段落数时出错: {e}")

        return count

    def count_paragraphs_in_original(self):
        """计算原始 docx 文件中的段落数。"""
        count = 0

        try:
            # 创建临时目录以解压原始文件
            with tempfile.TemporaryDirectory() as temp_dir:
                # 解压原始 docx
                with zipfile.ZipFile(self.original_file, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)

                # 解析 document.xml
                doc_xml_path = temp_dir + "/word/document.xml"
                root = lxml.etree.parse(doc_xml_path).getroot()

                # 计算所有 w:p 元素
                paragraphs = root.findall(f".//{{{self.WORD_2006_NAMESPACE}}}p")
                count = len(paragraphs)

        except Exception as e:
            print(f"计算原始文档中段落数时出错: {e}")

        return count

    def validate_insertions(self):
        """
        验证 w:delText 元素不在 w:ins 元素内。
        w:delText 只有在嵌套于 w:del 内时才允许出现在 w:ins 中。
        """
        errors = []

        for xml_file in self.xml_files:
            if xml_file.name != "document.xml":
                continue

            try:
                root = lxml.etree.parse(str(xml_file)).getroot()
                namespaces = {"w": self.WORD_2006_NAMESPACE}

                # 查找 w:ins 中不在 w:del 内的 w:delText
                invalid_elements = root.xpath(
                    ".//w:ins//w:delText[not(ancestor::w:del)]",
                    namespaces=namespaces
                )

                for elem in invalid_elements:
                    text_preview = (
                        repr(elem.text or "")[:50] + "..."
                        if len(repr(elem.text or "")) > 50
                        else repr(elem.text or "")
                    )
                    errors.append(
                        f"  {xml_file.relative_to(self.unpacked_dir)}: "
                        f"第 {elem.sourceline} 行: <w:ins> 内的 <w:delText>: {text_preview}"
                    )

            except (lxml.etree.XMLSyntaxError, Exception) as e:
                errors.append(
                    f"  {xml_file.relative_to(self.unpacked_dir)}: 错误: {e}"
                )

        if errors:
            print(f"失败 - 发现 {len(errors)} 个插入验证违规:")
            for error in errors:
                print(error)
            return False
        else:
            if self.verbose:
                print("通过 - 在 w:ins 元素内未发现 w:delText 元素")
            return True

    def compare_paragraph_counts(self):
        """比较原始文档和新文档之间的段落数。"""
        original_count = self.count_paragraphs_in_original()
        new_count = self.count_paragraphs_in_unpacked()

        diff = new_count - original_count
        diff_str = f"+{diff}" if diff > 0 else str(diff)
        print(f"\n段落数: {original_count} → {new_count} ({diff_str})")


if __name__ == "__main__":
    raise RuntimeError("此模块不应直接运行。")
