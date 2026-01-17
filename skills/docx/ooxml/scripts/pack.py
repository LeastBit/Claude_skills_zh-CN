#!/usr/bin/env python3
"""
将目录打包为 .docx、.pptx 或 .xlsx 文件的工具，同时移除 XML 格式化。

使用示例：
    python pack.py <input_directory> <office_file> [--force]
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
import defusedxml.minidom
import zipfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="将目录打包为 Office 文件")
    parser.add_argument("input_directory", help="解压后的 Office 文档目录")
    parser.add_argument("output_file", help="输出的 Office 文件（.docx/.pptx/.xlsx）")
    parser.add_argument("--force", action="store_true", help="跳过验证")
    args = parser.parse_args()

    try:
        success = pack_document(
            args.input_directory, args.output_file, validate=not args.force
        )

        # 如果跳过验证则显示警告
        if args.force:
            print("警告：已跳过验证，文件可能损坏", file=sys.stderr)
        # 如果验证失败则以错误退出
        elif not success:
            print("内容将产生损坏的文件。", file=sys.stderr)
            print("请在重新打包前验证 XML。", file=sys.stderr)
            print("使用 --force 跳过验证并强制打包。", file=sys.stderr)
            sys.exit(1)

    except ValueError as e:
        sys.exit(f"错误：{e}")


def pack_document(input_dir, output_file, validate=False):
    """将目录打包为 Office 文件（.docx/.pptx/.xlsx）。

    参数：
        input_dir: 解压后的 Office 文档目录路径
        output_file: 输出的 Office 文件路径
        validate: 如果为 True，使用 soffice 进行验证（默认：False）

    返回：
        bool: 成功返回 True，验证失败返回 False
    """
    input_dir = Path(input_dir)
    output_file = Path(output_file)

    if not input_dir.is_dir():
        raise ValueError(f"{input_dir} 不是目录")
    if output_file.suffix.lower() not in {".docx", ".pptx", ".xlsx"}:
        raise ValueError(f"{output_file} 必须是 .docx、.pptx 或 .xlsx 文件")

    # 在临时目录中工作，避免修改原始文件
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_content_dir = Path(temp_dir) / "content"
        shutil.copytree(input_dir, temp_content_dir)

        # 处理 XML 文件以移除格式化空白
        for pattern in ["*.xml", "*.rels"]:
            for xml_file in temp_content_dir.rglob(pattern):
                condense_xml(xml_file)

        # 创建最终的 Office 文件作为 zip 压缩包
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in temp_content_dir.rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(temp_content_dir))

        # 如果请求则进行验证
        if validate:
            if not validate_document(output_file):
                output_file.unlink()  # 删除损坏的文件
                return False

    return True


def validate_document(doc_path):
    """使用 soffice 转换为 HTML 来验证文档。"""
    # 根据文件扩展名确定正确的过滤器
    match doc_path.suffix.lower():
        case ".docx":
            filter_name = "html:HTML"
        case ".pptx":
            filter_name = "html:impress_html_Export"
        case ".xlsx":
            filter_name = "html:HTML (StarCalc)"

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            result = subprocess.run(
                [
                    "soffice",
                    "--headless",
                    "--convert-to",
                    filter_name,
                    "--outdir",
                    temp_dir,
                    str(doc_path),
                ],
                capture_output=True,
                timeout=10,
                text=True,
            )
            if not (Path(temp_dir) / f"{doc_path.stem}.html").exists():
                error_msg = result.stderr.strip() or "文档验证失败"
                print(f"验证错误：{error_msg}", file=sys.stderr)
                return False
            return True
        except FileNotFoundError:
            print("警告：未找到 soffice。跳过验证。", file=sys.stderr)
            return True
        except subprocess.TimeoutExpired:
            print("验证错误：转换超时", file=sys.stderr)
            return False
        except Exception as e:
            print(f"验证错误：{e}", file=sys.stderr)
            return False


def condense_xml(xml_file):
    """移除不必要的空白和注释。"""
    with open(xml_file, "r", encoding="utf-8") as f:
        dom = defusedxml.minidom.parse(f)

    # 处理每个元素以移除空白和注释
    for element in dom.getElementsByTagName("*"):
        # 跳过 w:t 元素及其处理
        if element.tagName.endswith(":t"):
            continue

        # 移除仅包含空白的文本节点和注释节点
        for child in list(element.childNodes):
            if (
                child.nodeType == child.TEXT_NODE
                and child.nodeValue
                and child.nodeValue.strip() == ""
            ) or child.nodeType == child.COMMENT_NODE:
                element.removeChild(child)

    # 写回压缩后的 XML
    with open(xml_file, "wb") as f:
        f.write(dom.toxml(encoding="UTF-8"))


if __name__ == "__main__":
    main()
