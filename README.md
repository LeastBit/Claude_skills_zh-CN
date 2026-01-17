# Claude Skills 中文版

[English](https://github.com/anthropics/skills) | [中文](./README.md)

这是一个经过整理和中文化的 [Anthropic Skills](https://github.com/anthropics/skills) 仓库。无论你是想快速了解 Claude 技能体系的最佳实践，还是需要直接上手 Word/PDF/PPTX/XLSX 处理脚本，这份中文版都能帮你省去大量摸索时间。

本仓库保留了原始目录结构，并对说明文档进行了全面的汉化，旨在帮助中文开发者更好地利用 Claude 的强大能力。

## 📖 项目目录结构

```text
.
├── README.md               项目说明文档
├── skills/                 技能集合目录
│   ├── algorithmic-art/    算法艺术生成
│   ├── brand-guidelines/   品牌指南助手
│   ├── canvas-design/      Canvas 平面设计
│   ├── doc-coauthoring/    文档共创引导
│   ├── docx/               Word 文档处理
│   ├── frontend-design/    前端界面设计
│   ├── internal-comms/     内部沟通文案
│   ├── mcp-builder/        MCP 服务器构建
│   ├── pdf/                PDF 处理工具箱
│   ├── pptx/               PPT 演示文稿处理
│   ├── skill-creator/      技能创建指南
│   ├── slack-gif-creator/  Slack GIF 生成
│   ├── theme-factory/      主题样式工厂
│   ├── web-artifacts-builder/ Web 制品构建器
│   ├── webapp-testing/     Web 应用测试
│   └── xlsx/               Excel 表格处理
├── spec/                   规范文档
│   └── agent-skills-spec.md 代理技能规范
└── template/               模板文件
    ├── SKILL_zh-CN.md      中文技能模板
    └── SKILL.md            英文技能模板
```

## 技能库详解

技能（Skills）是由说明、脚本和资源组成的文件夹，Claude 会按需加载它们以完成特定任务。以下是本仓库包含的所有技能及其作用：

### 🎨 创意与设计
*   **algorithmic-art (算法艺术)**: 使用 p5.js 创建带有种子随机性和交互式参数探索的算法艺术，注重生成过程与美学哲学的结合。
*   **canvas-design (平面设计)**: 基于设计哲学创作精美的 .png 与 .pdf 视觉作品，适用于海报、艺术品或极简主义设计。
*   **frontend-design (前端设计)**: 创建独特、生产级别的高质量前端界面，避免千篇一律的 AI 审美，注重排版、色彩与动效。
*   **slack-gif-creator (Slack GIF)**: 生成符合 Slack 尺寸和文件大小限制的优化动图，包含动画原理与优化工具。
*   **theme-factory (主题工厂)**: 提供预设的专业主题（颜色/字体配置）或即时生成新主题，可一键应用于幻灯片、文档等产出物。

### 🛠️ 开发与构建
*   **mcp-builder (MCP 构建器)**: 指导如何构建高质量的 MCP（模型上下文协议）服务器，帮助 Claude 通过工具与外部 API 或数据源交互。
*   **web-artifacts-builder (Web 制品构建)**: 使用 React、Tailwind CSS 和 shadcn/ui 构建复杂的多组件 HTML 成品，支持状态管理与现代前端实践。
*   **webapp-testing (Web 测试)**: 借助 Playwright 对本地网页应用执行 UI 验证、调试、截图及日志捕获。

### 企业与沟通
*   **brand-guidelines (品牌指南)**: 自动应用 Anthropic 官方品牌色与字体（或其他自定义品牌）到各类文档与设计中，确保品牌一致性。
*   **doc-coauthoring (文档共创)**: 引导用户通过结构化的工作流程（上下文收集 -> 优化结构 -> 读者测试）来协作撰写高质量文档。
*   **internal-comms (内部沟通)**: 提供撰写各类内部沟通文档（如状态报告、3P 更新、公司简报）的模板与最佳实践。

### 文档处理
*   **docx (Word 处理)**: 创建、编辑与分析 Word 文档，支持修订追踪、批注管理、格式保留和文本提取。
*   **pdf (PDF 处理)**: 全面的 PDF 工具箱，支持提取文本与表格、创建新 PDF、合并/拆分文档、填写表单及 OCR 识别。
*   **pptx (PPT 处理)**: 创建、编辑与分析 PowerPoint 演示文稿，支持基于 HTML 的幻灯片生成、版式调整与模板应用。
*   **xlsx (Excel 处理)**: 创建、编辑与分析 Excel 表格，支持公式计算（需 LibreOffice）、格式化、数据分析与可视化。

###  元技能
*   **skill-creator (技能创建)**: 指导如何设计、初始化并打包一个新的高效技能，扩展 Claude 的专业能力。

## 如何使用

1.  **浏览与学习**: 阅读 `skills/` 目录下各个技能的 `SKILL.md` 文件，了解其工作原理和提示词设计模式。
2.  **直接调用**: 如果你在支持 MCP 或插件的环境中（如 Claude Code），可以直接安装并调用这些技能。
3.  **参考开发**: 使用这些代码作为蓝本，开发你自己的企业级 Agent 技能。

## 免责声明

这些技能仅用于演示与教育目的。虽然 Claude 中可能提供部分类似能力，但你实际获得的实现方式和行为，可能与这些示例存在差异。在关键任务中依赖技能之前，请务必在你的环境中充分测试。

本项目是 Anthropic Skills 的中文衍生版本，旨在促进中文社区的交流与学习。