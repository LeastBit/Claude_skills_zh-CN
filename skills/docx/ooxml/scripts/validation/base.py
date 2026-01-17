"""
文档文件通用验证逻辑的基础验证器。
"""

import re
from pathlib import Path

import lxml.etree


class BaseSchemaValidator:
    """文档文件通用验证逻辑的基础验证器。"""

    # 'id' 属性必须在其文件内唯一的元素
    # 格式：element_name -> (attribute_name, scope)
    # scope 可以是 'file'（文件内唯一）或 'global'（跨所有文件唯一）
    UNIQUE_ID_REQUIREMENTS = {
        # Word 元素
        "comment": ("id", "file"),  # comments.xml 中的批注 ID
        "commentrangestart": ("id", "file"),  # 必须与批注 ID 匹配
        "commentrangeend": ("id", "file"),  # 必须与批注 ID 匹配
        "bookmarkstart": ("id", "file"),  # 书签起始 ID
        "bookmarkend": ("id", "file"),  # 书签结束 ID
        # 注意：ins 和 del（修订追踪）在同一修订的一部分时可以共享 ID
        # PowerPoint 元素
        "sldid": ("id", "file"),  # presentation.xml 中的幻灯片 ID
        "sldmasterid": ("id", "global"),  # 幻灯片母版 ID 必须全局唯一
        "sldlayoutid": ("id", "global"),  # 幻灯片版式 ID 必须全局唯一
        "cm": ("authorid", "file"),  # 批注作者 ID
        # Excel 元素
        "sheet": ("sheetid", "file"),  # workbook.xml 中的工作表 ID
        "definedname": ("id", "file"),  # 命名区域 ID
        # 绘图/形状元素（所有格式）
        "cxnsp": ("id", "file"),  # 连接形状 ID
        "sp": ("id", "file"),  # 形状 ID
        "pic": ("id", "file"),  # 图片 ID
        "grpsp": ("id", "file"),  # 组合形状 ID
    }

    # 元素名称到预期关系类型的映射
    # 子类应使用特定于格式的映射覆盖此项
    ELEMENT_RELATIONSHIP_TYPES = {}

    # 所有 Office 文档类型的统一架构映射
    SCHEMA_MAPPINGS = {
        # 文档类型特定架构
        "word": "ISO-IEC29500-4_2016/wml.xsd",  # Word 文档
        "ppt": "ISO-IEC29500-4_2016/pml.xsd",  # PowerPoint 演示文稿
        "xl": "ISO-IEC29500-4_2016/sml.xsd",  # Excel 电子表格
        # 通用文件类型
        "[Content_Types].xml": "ecma/fouth-edition/opc-contentTypes.xsd",
        "app.xml": "ISO-IEC29500-4_2016/shared-documentPropertiesExtended.xsd",
        "core.xml": "ecma/fouth-edition/opc-coreProperties.xsd",
        "custom.xml": "ISO-IEC29500-4_2016/shared-documentPropertiesCustom.xsd",
        ".rels": "ecma/fouth-edition/opc-relationships.xsd",
        # Word 特定文件
        "people.xml": "microsoft/wml-2012.xsd",
        "commentsIds.xml": "microsoft/wml-cid-2016.xsd",
        "commentsExtensible.xml": "microsoft/wml-cex-2018.xsd",
        "commentsExtended.xml": "microsoft/wml-2012.xsd",
        # 图表文件（跨文档类型通用）
        "chart": "ISO-IEC29500-4_2016/dml-chart.xsd",
        # 主题文件（跨文档类型通用）
        "theme": "ISO-IEC29500-4_2016/dml-main.xsd",
        # 绘图和媒体文件
        "drawing": "ISO-IEC29500-4_2016/dml-main.xsd",
    }

    # 统一命名空间常量
    MC_NAMESPACE = "http://schemas.openxmlformats.org/markup-compatibility/2006"
    XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"

    # 验证器中使用的通用 OOXML 命名空间
    PACKAGE_RELATIONSHIPS_NAMESPACE = (
        "http://schemas.openxmlformats.org/package/2006/relationships"
    )
    OFFICE_RELATIONSHIPS_NAMESPACE = (
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    )
    CONTENT_TYPES_NAMESPACE = (
        "http://schemas.openxmlformats.org/package/2006/content-types"
    )

    # 我们应该清理可忽略命名空间的文件夹
    MAIN_CONTENT_FOLDERS = {"word", "ppt", "xl"}

    # 所有允许的 OOXML 命名空间（所有文档类型的超集）
    OOXML_NAMESPACES = {
        "http://schemas.openxmlformats.org/officeDocument/2006/math",
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "http://schemas.openxmlformats.org/schemaLibrary/2006/main",
        "http://schemas.openxmlformats.org/drawingml/2006/main",
        "http://schemas.openxmlformats.org/drawingml/2006/chart",
        "http://schemas.openxmlformats.org/drawingml/2006/chartDrawing",
        "http://schemas.openxmlformats.org/drawingml/2006/diagram",
        "http://schemas.openxmlformats.org/drawingml/2006/picture",
        "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
        "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
        "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
        "http://schemas.openxmlformats.org/presentationml/2006/main",
        "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "http://schemas.openxmlformats.org/officeDocument/2006/sharedTypes",
        "http://www.w3.org/XML/1998/namespace",
    }

    def __init__(self, unpacked_dir, original_file, verbose=False):
        self.unpacked_dir = Path(unpacked_dir).resolve()
        self.original_file = Path(original_file)
        self.verbose = verbose

        # 设置架构目录
        self.schemas_dir = Path(__file__).parent.parent.parent / "schemas"

        # 获取所有 XML 和 .rels 文件
        patterns = ["*.xml", "*.rels"]
        self.xml_files = [
            f for pattern in patterns for f in self.unpacked_dir.rglob(pattern)
        ]

        if not self.xml_files:
            print(f"警告：在 {self.unpacked_dir} 中未找到 XML 文件")

    def validate(self):
        """运行所有验证检查，如果全部通过则返回 True。"""
        raise NotImplementedError("子类必须实现 validate 方法")

    def validate_xml(self):
        """验证所有 XML 文件格式是否正确。"""
        errors = []

        for xml_file in self.xml_files:
            try:
                # 尝试解析 XML 文件
                lxml.etree.parse(str(xml_file))
            except lxml.etree.XMLSyntaxError as e:
                errors.append(
                    f"  {xml_file.relative_to(self.unpacked_dir)}: "
                    f"第 {e.lineno} 行: {e.msg}"
                )
            except Exception as e:
                errors.append(
                    f"  {xml_file.relative_to(self.unpacked_dir)}: "
                    f"意外错误: {str(e)}"
                )

        if errors:
            print(f"失败 - 发现 {len(errors)} 个 XML 违规:")
            for error in errors:
                print(error)
            return False
        else:
            if self.verbose:
                print("通过 - 所有 XML 文件格式正确")
            return True

    def validate_namespaces(self):
        """验证 Ignorable 属性中的命名空间前缀是否已声明。"""
        errors = []

        for xml_file in self.xml_files:
            try:
                root = lxml.etree.parse(str(xml_file)).getroot()
                declared = set(root.nsmap.keys()) - {None}  # 排除默认命名空间

                for attr_val in [
                    v for k, v in root.attrib.items() if k.endswith("Ignorable")
                ]:
                    undeclared = set(attr_val.split()) - declared
                    errors.extend(
                        f"  {xml_file.relative_to(self.unpacked_dir)}: "
                        f"命名空间 '{ns}' 在 Ignorable 中但未声明"
                        for ns in undeclared
                    )
            except lxml.etree.XMLSyntaxError:
                continue

        if errors:
            print(f"失败 - {len(errors)} 个命名空间问题:")
            for error in errors:
                print(error)
            return False
        if self.verbose:
            print("通过 - 所有命名空间前缀已正确声明")
        return True

    def validate_unique_ids(self):
        """验证特定 ID 是否根据 OOXML 要求唯一。"""
        errors = []
        global_ids = {}  # 跟踪跨所有文件的全局唯一 ID

        for xml_file in self.xml_files:
            try:
                root = lxml.etree.parse(str(xml_file)).getroot()
                file_ids = {}  # 跟踪必须在此文件内唯一的 ID

                # 从树中移除所有 mc:AlternateContent 元素
                mc_elements = root.xpath(
                    ".//mc:AlternateContent", namespaces={"mc": self.MC_NAMESPACE}
                )
                for elem in mc_elements:
                    elem.getparent().remove(elem)

                # 现在检查清理后的树中的 ID
                for elem in root.iter():
                    # 获取不带命名空间的元素名称
                    tag = (
                        elem.tag.split("}")[-1].lower()
                        if "}" in elem.tag
                        else elem.tag.lower()
                    )

                    # 检查此元素类型是否有 ID 唯一性要求
                    if tag in self.UNIQUE_ID_REQUIREMENTS:
                        attr_name, scope = self.UNIQUE_ID_REQUIREMENTS[tag]

                        # 查找指定的属性
                        id_value = None
                        for attr, value in elem.attrib.items():
                            attr_local = (
                                attr.split("}")[-1].lower()
                                if "}" in attr
                                else attr.lower()
                            )
                            if attr_local == attr_name:
                                id_value = value
                                break

                        if id_value is not None:
                            if scope == "global":
                                # 检查全局唯一性
                                if id_value in global_ids:
                                    prev_file, prev_line, prev_tag = global_ids[
                                        id_value
                                    ]
                                    errors.append(
                                        f"  {xml_file.relative_to(self.unpacked_dir)}: "
                                        f"第 {elem.sourceline} 行: <{tag}> 中的全局 ID '{id_value}' "
                                        f"已在 {prev_file} 的第 {prev_line} 行 <{prev_tag}> 中使用"
                                    )
                                else:
                                    global_ids[id_value] = (
                                        xml_file.relative_to(self.unpacked_dir),
                                        elem.sourceline,
                                        tag,
                                    )
                            elif scope == "file":
                                # 检查文件级唯一性
                                key = (tag, attr_name)
                                if key not in file_ids:
                                    file_ids[key] = {}

                                if id_value in file_ids[key]:
                                    prev_line = file_ids[key][id_value]
                                    errors.append(
                                        f"  {xml_file.relative_to(self.unpacked_dir)}: "
                                        f"第 {elem.sourceline} 行: <{tag}> 中重复的 {attr_name}='{id_value}' "
                                        f"（首次出现在第 {prev_line} 行）"
                                    )
                                else:
                                    file_ids[key][id_value] = elem.sourceline

            except (lxml.etree.XMLSyntaxError, Exception) as e:
                errors.append(
                    f"  {xml_file.relative_to(self.unpacked_dir)}: 错误: {e}"
                )

        if errors:
            print(f"失败 - 发现 {len(errors)} 个 ID 唯一性违规:")
            for error in errors:
                print(error)
            return False
        else:
            if self.verbose:
                print("通过 - 所有必需的 ID 都是唯一的")
            return True

    def validate_file_references(self):
        """
        验证所有 .rels 文件正确引用文件，并且所有文件都被引用。
        """
        errors = []

        # 查找所有 .rels 文件
        rels_files = list(self.unpacked_dir.rglob("*.rels"))

        if not rels_files:
            if self.verbose:
                print("通过 - 未找到 .rels 文件")
            return True

        # 获取解压目录中的所有文件（排除引用文件）
        all_files = []
        for file_path in self.unpacked_dir.rglob("*"):
            if (
                file_path.is_file()
                and file_path.name != "[Content_Types].xml"
                and not file_path.name.endswith(".rels")
            ):  # 此文件不被 .rels 引用
                all_files.append(file_path.resolve())

        # 跟踪被任何 .rels 文件引用的所有文件
        all_referenced_files = set()

        if self.verbose:
            print(
                f"找到 {len(rels_files)} 个 .rels 文件和 {len(all_files)} 个目标文件"
            )

        # 检查每个 .rels 文件
        for rels_file in rels_files:
            try:
                # 解析关系文件
                rels_root = lxml.etree.parse(str(rels_file)).getroot()

                # 获取此 .rels 文件所在的目录
                rels_dir = rels_file.parent

                # 查找所有关系及其目标
                referenced_files = set()
                broken_refs = []

                for rel in rels_root.findall(
                    ".//ns:Relationship",
                    namespaces={"ns": self.PACKAGE_RELATIONSHIPS_NAMESPACE},
                ):
                    target = rel.get("Target")
                    if target and not target.startswith(
                        ("http", "mailto:")
                    ):  # 跳过外部 URL
                        # 相对于 .rels 文件位置解析目标路径
                        if rels_file.name == ".rels":
                            # 根 .rels 文件 - 目标相对于 unpacked_dir
                            target_path = self.unpacked_dir / target
                        else:
                            # 其他 .rels 文件 - 目标相对于其父目录的父目录
                            # 例如，word/_rels/document.xml.rels -> 目标相对于 word/
                            base_dir = rels_dir.parent
                            target_path = base_dir / target

                        # 规范化路径并检查是否存在
                        try:
                            target_path = target_path.resolve()
                            if target_path.exists() and target_path.is_file():
                                referenced_files.add(target_path)
                                all_referenced_files.add(target_path)
                            else:
                                broken_refs.append((target, rel.sourceline))
                        except (OSError, ValueError):
                            broken_refs.append((target, rel.sourceline))

                # 报告损坏的引用
                if broken_refs:
                    rel_path = rels_file.relative_to(self.unpacked_dir)
                    for broken_ref, line_num in broken_refs:
                        errors.append(
                            f"  {rel_path}: 第 {line_num} 行: 对 {broken_ref} 的损坏引用"
                        )

            except Exception as e:
                rel_path = rels_file.relative_to(self.unpacked_dir)
                errors.append(f"  解析 {rel_path} 时出错: {e}")

        # 检查未引用的文件（存在但未在任何地方引用的文件）
        unreferenced_files = set(all_files) - all_referenced_files

        if unreferenced_files:
            for unref_file in sorted(unreferenced_files):
                unref_rel_path = unref_file.relative_to(self.unpacked_dir)
                errors.append(f"  未引用的文件: {unref_rel_path}")

        if errors:
            print(f"失败 - 发现 {len(errors)} 个关系验证错误:")
            for error in errors:
                print(error)
            print(
                "严重：这些错误将导致文档显示为损坏。"
                + "必须修复损坏的引用，"
                + "未引用的文件必须被引用或删除。"
            )
            return False
        else:
            if self.verbose:
                print(
                    "通过 - 所有引用都有效，所有文件都已正确引用"
                )
            return True

    def validate_all_relationship_ids(self):
        """
        验证 XML 文件中的所有 r:id 属性引用了对应 .rels 文件中存在的 ID，
        并可选验证关系类型。
        """
        import lxml.etree

        errors = []

        # 处理每个可能包含 r:id 引用的 XML 文件
        for xml_file in self.xml_files:
            # 跳过 .rels 文件本身
            if xml_file.suffix == ".rels":
                continue

            # 确定对应的 .rels 文件
            # 对于 dir/file.xml，它是 dir/_rels/file.xml.rels
            rels_dir = xml_file.parent / "_rels"
            rels_file = rels_dir / f"{xml_file.name}.rels"

            # 如果没有对应的 .rels 文件则跳过（这是可以的）
            if not rels_file.exists():
                continue

            try:
                # 解析 .rels 文件以获取有效的关系 ID 及其类型
                rels_root = lxml.etree.parse(str(rels_file)).getroot()
                rid_to_type = {}

                for rel in rels_root.findall(
                    f".//{{{self.PACKAGE_RELATIONSHIPS_NAMESPACE}}}Relationship"
                ):
                    rid = rel.get("Id")
                    rel_type = rel.get("Type", "")
                    if rid:
                        # 检查重复的 rId
                        if rid in rid_to_type:
                            rels_rel_path = rels_file.relative_to(self.unpacked_dir)
                            errors.append(
                                f"  {rels_rel_path}: 第 {rel.sourceline} 行: "
                                f"重复的关系 ID '{rid}'（ID 必须唯一）"
                            )
                        # 从完整 URL 中仅提取类型名称
                        type_name = (
                            rel_type.split("/")[-1] if "/" in rel_type else rel_type
                        )
                        rid_to_type[rid] = type_name

                # 解析 XML 文件以查找所有 r:id 引用
                xml_root = lxml.etree.parse(str(xml_file)).getroot()

                # 查找所有具有 r:id 属性的元素
                for elem in xml_root.iter():
                    # 检查 r:id 属性（关系 ID）
                    rid_attr = elem.get(f"{{{self.OFFICE_RELATIONSHIPS_NAMESPACE}}}id")
                    if rid_attr:
                        xml_rel_path = xml_file.relative_to(self.unpacked_dir)
                        elem_name = (
                            elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                        )

                        # 检查 ID 是否存在
                        if rid_attr not in rid_to_type:
                            errors.append(
                                f"  {xml_rel_path}: 第 {elem.sourceline} 行: "
                                f"<{elem_name}> 引用了不存在的关系 '{rid_attr}' "
                                f"（有效 ID: {', '.join(sorted(rid_to_type.keys())[:5])}{'...' if len(rid_to_type) > 5 else ''})"
                            )
                        # 检查此元素是否有类型期望
                        elif self.ELEMENT_RELATIONSHIP_TYPES:
                            expected_type = self._get_expected_relationship_type(
                                elem_name
                            )
                            if expected_type:
                                actual_type = rid_to_type[rid_attr]
                                # 检查实际类型是否匹配或包含预期类型
                                if expected_type not in actual_type.lower():
                                    errors.append(
                                        f"  {xml_rel_path}: 第 {elem.sourceline} 行: "
                                        f"<{elem_name}> 引用的 '{rid_attr}' 指向 '{actual_type}' "
                                        f"但应该指向 '{expected_type}' 关系"
                                    )

            except Exception as e:
                xml_rel_path = xml_file.relative_to(self.unpacked_dir)
                errors.append(f"  处理 {xml_rel_path} 时出错: {e}")

        if errors:
            print(f"失败 - 发现 {len(errors)} 个关系 ID 引用错误:")
            for error in errors:
                print(error)
            print("\n这些 ID 不匹配将导致文档显示为损坏！")
            return False
        else:
            if self.verbose:
                print("通过 - 所有关系 ID 引用都有效")
            return True

    def _get_expected_relationship_type(self, element_name):
        """
        获取元素的预期关系类型。
        首先检查显式映射，然后尝试模式检测。
        """
        # 将元素名称规范化为小写
        elem_lower = element_name.lower()

        # 首先检查显式映射
        if elem_lower in self.ELEMENT_RELATIONSHIP_TYPES:
            return self.ELEMENT_RELATIONSHIP_TYPES[elem_lower]

        # 尝试常见模式的模式检测
        # 模式 1：以 "Id" 结尾的元素通常期望前缀类型的关系
        if elem_lower.endswith("id") and len(elem_lower) > 2:
            # 例如，"sldId" -> "sld"，"sldMasterId" -> "sldMaster"
            prefix = elem_lower[:-2]  # 移除 "id"
            # 检查是否是像 "sldMasterId" 这样的复合词
            if prefix.endswith("master"):
                return prefix.lower()
            elif prefix.endswith("layout"):
                return prefix.lower()
            else:
                # 简单情况如 "sldId" -> "slide"
                # 常见转换
                if prefix == "sld":
                    return "slide"
                return prefix.lower()

        # 模式 2：以 "Reference" 结尾的元素期望前缀类型的关系
        if elem_lower.endswith("reference") and len(elem_lower) > 9:
            prefix = elem_lower[:-9]  # 移除 "reference"
            return prefix.lower()

        return None

    def validate_content_types(self):
        """验证所有内容文件是否在 [Content_Types].xml 中正确声明。"""
        errors = []

        # 查找 [Content_Types].xml 文件
        content_types_file = self.unpacked_dir / "[Content_Types].xml"
        if not content_types_file.exists():
            print("失败 - 未找到 [Content_Types].xml 文件")
            return False

        try:
            # 解析并获取所有声明的部件和扩展名
            root = lxml.etree.parse(str(content_types_file)).getroot()
            declared_parts = set()
            declared_extensions = set()

            # 获取 Override 声明（特定文件）
            for override in root.findall(
                f".//{{{self.CONTENT_TYPES_NAMESPACE}}}Override"
            ):
                part_name = override.get("PartName")
                if part_name is not None:
                    declared_parts.add(part_name.lstrip("/"))

            # 获取 Default 声明（按扩展名）
            for default in root.findall(
                f".//{{{self.CONTENT_TYPES_NAMESPACE}}}Default"
            ):
                extension = default.get("Extension")
                if extension is not None:
                    declared_extensions.add(extension.lower())

            # 需要内容类型声明的根元素
            declarable_roots = {
                "sld",
                "sldLayout",
                "sldMaster",
                "presentation",  # PowerPoint
                "document",  # Word
                "workbook",
                "worksheet",  # Excel
                "theme",  # 通用
            }

            # 应该声明的常见媒体文件扩展名
            media_extensions = {
                "png": "image/png",
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "gif": "image/gif",
                "bmp": "image/bmp",
                "tiff": "image/tiff",
                "wmf": "image/x-wmf",
                "emf": "image/x-emf",
            }

            # 获取解压目录中的所有文件
            all_files = list(self.unpacked_dir.rglob("*"))
            all_files = [f for f in all_files if f.is_file()]

            # 检查所有 XML 文件的 Override 声明
            for xml_file in self.xml_files:
                path_str = str(xml_file.relative_to(self.unpacked_dir)).replace(
                    "\\", "/"
                )

                # 跳过非内容文件
                if any(
                    skip in path_str
                    for skip in [".rels", "[Content_Types]", "docProps/", "_rels/"]
                ):
                    continue

                try:
                    root_tag = lxml.etree.parse(str(xml_file)).getroot().tag
                    root_name = root_tag.split("}")[-1] if "}" in root_tag else root_tag

                    if root_name in declarable_roots and path_str not in declared_parts:
                        errors.append(
                            f"  {path_str}: 具有 <{root_name}> 根元素的文件未在 [Content_Types].xml 中声明"
                        )

                except Exception:
                    continue  # 跳过无法解析的文件

            # 检查所有非 XML 文件的 Default 扩展名声明
            for file_path in all_files:
                # 跳过 XML 文件和元数据文件（上面已检查）
                if file_path.suffix.lower() in {".xml", ".rels"}:
                    continue
                if file_path.name == "[Content_Types].xml":
                    continue
                if "_rels" in file_path.parts or "docProps" in file_path.parts:
                    continue

                extension = file_path.suffix.lstrip(".").lower()
                if extension and extension not in declared_extensions:
                    # 检查是否是应该声明的已知媒体扩展名
                    if extension in media_extensions:
                        relative_path = file_path.relative_to(self.unpacked_dir)
                        errors.append(
                            f'  {relative_path}: 扩展名为 \'{extension}\' 的文件未在 [Content_Types].xml 中声明 - 应添加: <Default Extension="{extension}" ContentType="{media_extensions[extension]}"/>'
                        )

        except Exception as e:
            errors.append(f"  解析 [Content_Types].xml 时出错: {e}")

        if errors:
            print(f"失败 - 发现 {len(errors)} 个内容类型声明错误:")
            for error in errors:
                print(error)
            return False
        else:
            if self.verbose:
                print(
                    "通过 - 所有内容文件都已在 [Content_Types].xml 中正确声明"
                )
            return True

    def validate_file_against_xsd(self, xml_file, verbose=False):
        """根据 XSD 架构验证单个 XML 文件，与原始文件比较。

        参数:
            xml_file: 要验证的 XML 文件路径
            verbose: 启用详细输出

        返回:
            tuple: (is_valid, new_errors_set) 其中 is_valid 为 True/False/None（跳过）
        """
        # 解析两个路径以处理符号链接
        xml_file = Path(xml_file).resolve()
        unpacked_dir = self.unpacked_dir.resolve()

        # 验证当前文件
        is_valid, current_errors = self._validate_single_file_xsd(
            xml_file, unpacked_dir
        )

        if is_valid is None:
            return None, set()  # 跳过
        elif is_valid:
            return True, set()  # 有效，无错误

        # 获取此特定文件的原始文件错误
        original_errors = self._get_original_file_errors(xml_file)

        # 与原始文件比较（两者都保证是集合）
        assert current_errors is not None
        new_errors = current_errors - original_errors

        if new_errors:
            if verbose:
                relative_path = xml_file.relative_to(unpacked_dir)
                print(f"失败 - {relative_path}: {len(new_errors)} 个新错误")
                for error in list(new_errors)[:3]:
                    truncated = error[:250] + "..." if len(error) > 250 else error
                    print(f"  - {truncated}")
            return False, new_errors
        else:
            # 所有错误在原始文件中已存在
            if verbose:
                print(
                    f"通过 - 无新错误（原始文件有 {len(current_errors)} 个错误）"
                )
            return True, set()

    def validate_against_xsd(self):
        """根据 XSD 架构验证 XML 文件，仅显示与原始文件相比的新错误。"""
        new_errors = []
        original_error_count = 0
        valid_count = 0
        skipped_count = 0

        for xml_file in self.xml_files:
            relative_path = str(xml_file.relative_to(self.unpacked_dir))
            is_valid, new_file_errors = self.validate_file_against_xsd(
                xml_file, verbose=False
            )

            if is_valid is None:
                skipped_count += 1
                continue
            elif is_valid and not new_file_errors:
                valid_count += 1
                continue
            elif is_valid:
                # 有错误但全部在原始文件中存在
                original_error_count += 1
                valid_count += 1
                continue

            # 有新错误
            new_errors.append(f"  {relative_path}: {len(new_file_errors)} 个新错误")
            for error in list(new_file_errors)[:3]:  # 显示前 3 个错误
                new_errors.append(
                    f"    - {error[:250]}..." if len(error) > 250 else f"    - {error}"
                )

        # 打印摘要
        if self.verbose:
            print(f"已验证 {len(self.xml_files)} 个文件:")
            print(f"  - 有效: {valid_count}")
            print(f"  - 跳过（无架构）: {skipped_count}")
            if original_error_count:
                print(f"  - 有原始错误（已忽略）: {original_error_count}")
            print(
                f"  - 有新错误: {len(new_errors) > 0 and len([e for e in new_errors if not e.startswith('    ')]) or 0}"
            )

        if new_errors:
            print("\n失败 - 发现新的验证错误:")
            for error in new_errors:
                print(error)
            return False
        else:
            if self.verbose:
                print("\n通过 - 未引入新的 XSD 验证错误")
            return True

    def _get_schema_path(self, xml_file):
        """确定 XML 文件的适当架构路径。"""
        # 检查精确文件名匹配
        if xml_file.name in self.SCHEMA_MAPPINGS:
            return self.schemas_dir / self.SCHEMA_MAPPINGS[xml_file.name]

        # 检查 .rels 文件
        if xml_file.suffix == ".rels":
            return self.schemas_dir / self.SCHEMA_MAPPINGS[".rels"]

        # 检查图表文件
        if "charts/" in str(xml_file) and xml_file.name.startswith("chart"):
            return self.schemas_dir / self.SCHEMA_MAPPINGS["chart"]

        # 检查主题文件
        if "theme/" in str(xml_file) and xml_file.name.startswith("theme"):
            return self.schemas_dir / self.SCHEMA_MAPPINGS["theme"]

        # 检查文件是否在主内容文件夹中并使用适当的架构
        if xml_file.parent.name in self.MAIN_CONTENT_FOLDERS:
            return self.schemas_dir / self.SCHEMA_MAPPINGS[xml_file.parent.name]

        return None

    def _clean_ignorable_namespaces(self, xml_doc):
        """移除不在允许命名空间中的属性和元素。"""
        # 创建干净的副本
        xml_string = lxml.etree.tostring(xml_doc, encoding="unicode")
        xml_copy = lxml.etree.fromstring(xml_string)

        # 移除不在允许命名空间中的属性
        for elem in xml_copy.iter():
            attrs_to_remove = []

            for attr in elem.attrib:
                # 检查属性是否来自允许的命名空间之外的命名空间
                if "{" in attr:
                    ns = attr.split("}")[0][1:]
                    if ns not in self.OOXML_NAMESPACES:
                        attrs_to_remove.append(attr)

            # 移除收集的属性
            for attr in attrs_to_remove:
                del elem.attrib[attr]

        # 移除不在允许命名空间中的元素
        self._remove_ignorable_elements(xml_copy)

        return lxml.etree.ElementTree(xml_copy)

    def _remove_ignorable_elements(self, root):
        """递归移除所有不在允许命名空间中的元素。"""
        elements_to_remove = []

        # 查找要移除的元素
        for elem in list(root):
            # 跳过非元素节点（注释、处理指令等）
            if not hasattr(elem, "tag") or callable(elem.tag):
                continue

            tag_str = str(elem.tag)
            if tag_str.startswith("{"):
                ns = tag_str.split("}")[0][1:]
                if ns not in self.OOXML_NAMESPACES:
                    elements_to_remove.append(elem)
                    continue

            # 递归清理子元素
            self._remove_ignorable_elements(elem)

        # 移除收集的元素
        for elem in elements_to_remove:
            root.remove(elem)

    def _preprocess_for_mc_ignorable(self, xml_doc):
        """预处理 XML 以正确处理 mc:Ignorable 属性。"""
        # 验证前从根元素移除 mc:Ignorable 属性
        root = xml_doc.getroot()

        # 从根元素移除 mc:Ignorable 属性
        if f"{{{self.MC_NAMESPACE}}}Ignorable" in root.attrib:
            del root.attrib[f"{{{self.MC_NAMESPACE}}}Ignorable"]

        return xml_doc

    def _validate_single_file_xsd(self, xml_file, base_path):
        """根据 XSD 架构验证单个 XML 文件。返回 (is_valid, errors_set)。"""
        schema_path = self._get_schema_path(xml_file)
        if not schema_path:
            return None, None  # 跳过文件

        try:
            # 加载架构
            with open(schema_path, "rb") as xsd_file:
                parser = lxml.etree.XMLParser()
                xsd_doc = lxml.etree.parse(
                    xsd_file, parser=parser, base_url=str(schema_path)
                )
                schema = lxml.etree.XMLSchema(xsd_doc)

            # 加载和预处理 XML
            with open(xml_file, "r") as f:
                xml_doc = lxml.etree.parse(f)

            xml_doc, _ = self._remove_template_tags_from_text_nodes(xml_doc)
            xml_doc = self._preprocess_for_mc_ignorable(xml_doc)

            # 如果需要则清理可忽略的命名空间
            relative_path = xml_file.relative_to(base_path)
            if (
                relative_path.parts
                and relative_path.parts[0] in self.MAIN_CONTENT_FOLDERS
            ):
                xml_doc = self._clean_ignorable_namespaces(xml_doc)

            # 验证
            if schema.validate(xml_doc):
                return True, set()
            else:
                errors = set()
                for error in schema.error_log:
                    # 存储规范化的错误消息（不带行号以便比较）
                    errors.add(error.message)
                return False, errors

        except Exception as e:
            return False, {str(e)}

    def _get_original_file_errors(self, xml_file):
        """获取原始文档中单个文件的 XSD 验证错误。

        参数:
            xml_file: unpacked_dir 中要检查的 XML 文件路径

        返回:
            set: 原始文件的错误消息集合
        """
        import tempfile
        import zipfile

        # 解析两个路径以处理符号链接（例如，macOS 上的 /var vs /private/var）
        xml_file = Path(xml_file).resolve()
        unpacked_dir = self.unpacked_dir.resolve()
        relative_path = xml_file.relative_to(unpacked_dir)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 解压原始文件
            with zipfile.ZipFile(self.original_file, "r") as zip_ref:
                zip_ref.extractall(temp_path)

            # 在原始文件中查找对应文件
            original_xml_file = temp_path / relative_path

            if not original_xml_file.exists():
                # 文件在原始文件中不存在，所以没有原始错误
                return set()

            # 验证原始文件中的特定文件
            is_valid, errors = self._validate_single_file_xsd(
                original_xml_file, temp_path
            )
            return errors if errors else set()

    def _remove_template_tags_from_text_nodes(self, xml_doc):
        """从 XML 文本节点中移除模板标签并收集警告。

        模板标签遵循 {{ ... }} 模式，用作内容替换的占位符。
        在 XSD 验证之前应从文本内容中移除它们，同时保留 XML 结构。

        返回:
            tuple: (cleaned_xml_doc, warnings_list)
        """
        warnings = []
        template_pattern = re.compile(r"\{\{[^}]*\}\}")

        # 创建文档副本以避免修改原始文档
        xml_string = lxml.etree.tostring(xml_doc, encoding="unicode")
        xml_copy = lxml.etree.fromstring(xml_string)

        def process_text_content(text, content_type):
            if not text:
                return text
            matches = list(template_pattern.finditer(text))
            if matches:
                for match in matches:
                    warnings.append(
                        f"在 {content_type} 中发现模板标签: {match.group()}"
                    )
                return template_pattern.sub("", text)
            return text

        # 处理文档中的所有文本节点
        for elem in xml_copy.iter():
            # 如果是 w:t 元素则跳过处理
            if not hasattr(elem, "tag") or callable(elem.tag):
                continue
            tag_str = str(elem.tag)
            if tag_str.endswith("}t") or tag_str == "t":
                continue

            elem.text = process_text_content(elem.text, "文本内容")
            elem.tail = process_text_content(elem.tail, "尾部内容")

        return lxml.etree.ElementTree(xml_copy), warnings


if __name__ == "__main__":
    raise RuntimeError("此模块不应直接运行。")
