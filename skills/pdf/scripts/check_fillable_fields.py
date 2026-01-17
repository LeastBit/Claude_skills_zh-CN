import sys
from pypdf import PdfReader


# 供 Claude 运行以确定 PDF 是否包含可填写表单字段的脚本。参见 forms.md。


reader = PdfReader(sys.argv[1])
if (reader.get_fields()):
    print("此 PDF 包含可填写的表单字段")
else:
    print("此 PDF 不包含可填写的表单字段；您需要通过视觉分析确定数据输入位置")
