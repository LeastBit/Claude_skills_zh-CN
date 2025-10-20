# 中文版本说明

亲爱的开发者们，我刚刚完成了 [Anthropic Skills](https://github.com/anthropics/skills) 仓库的全量中文化整理，欢迎前往我的译文仓库（保留原始目录结构，并采用“英文名称_中文名称”的命名方式）免费下载使用。无论你想快速了解 Claude 技能体系的最佳实践，还是需要直接上手 Word/PDF/PPTX/XLSX 处理脚本，这份中文版都能帮你省去大量摸索时间。

亮点速览：
- 🧩 **原汁原味的官方示例**：完整保留算法艺术、品牌规范、Slack GIF、MCP 服务器等全部技能。  
- 📄 **文档技能全译本**：OOXML、docx-js、HTML 转 PPT 流程、PDF 表单填写等高级指南均已翻译补充。  
- 📦 **即取即用**：学习后即可在 Claude Code、Claude.ai 或 API 中运用，快速体验技能生态。  

如果你正在搭建企业内部 Copilot、需要示例脚本做二次开发，或者想学习 Anthropic 的技能设计模式，这份中文版资料会是绝佳起点。欢迎点赞、转发或 PR，一起把更多高质量的中文 AI 开发资料带给社区！
# 技能库

技能是由说明、脚本和资源组成的文件夹，Claude 会按需加载它们，以在特定任务上提升表现。无论是根据你公司的品牌规范生成文档，遵循你组织特定流程进行数据分析，还是自动化个人事务，技能都能教会 Claude 以可复用的方式完成任务。

想进一步了解，请参阅：
- [什么是技能？](https://support.claude.com/en/articles/12512176-what-are-skills)
- [在 Claude 中使用技能](https://support.claude.com/en/articles/12512180-using-skills-in-claude)
- [如何创建自定义技能](https://support.claude.com/en/articles/12512198-creating-custom-skills)
- [通过 Agent Skills 让智能体走向真实世界](https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

# 关于此代码库

该代码库收录了 Claude 技能体系的示例技能，展示了技能能够实现的可能性。这些示例覆盖多个方向：从创意类应用（艺术、音乐、设计），到技术任务（网页应用测试、MCP 服务器生成），再到企业场景流程（内部沟通、品牌等）。

每个技能都以独立文件夹的形式存在，包含一份 `SKILL.md` 文件，记录 Claude 所需的指令与元数据。欢迎浏览这些示例，为你的自定义技能汲取灵感，或了解不同的技能设计模式与思路。

本仓库中的示例技能采用开源许可（Apache 2.0）。我们还在 [`document-skills/`](./document-skills/) 文件夹中附带了支撑 [Claude 文档能力](https://www.anthropic.com/news/create-files) 的文档生成与编辑技能。这些技能虽然是源代码开放，但并非开源；我们希望将其作为参考提供给开发者，以展示在真实生产环境中运行的复杂技能是如何设计的。

**注意：** 这些技能仅用于参考与学习，主要演示通用能力，而非特定组织的工作流或敏感内容。

此外，推荐阅读《学习笔记》，获取一条可执行的学习路径与“超大型应用开发项目”的实战蓝图：`./docs/study-notes_学习笔记.md`

## 免责声明

**这些技能仅用于演示与教育目的。** 虽然 Claude 中可能提供部分类似能力，但你实际获得的实现方式和行为，可能与这些示例存在差异。这些示例旨在展示可能性与设计模式。在关键任务中依赖技能之前，请务必在你的环境中充分测试。

# 示例技能

该仓库囊括了展示多元能力的示例技能：

## 创意设计
- **algorithmic-art** —— 使用带种子随机性的 p5.js，通过流场和粒子系统生成算法艺术
- **canvas-design** —— 基于设计哲学生成精美的 .png 与 .pdf 视觉作品
- **slack-gif-creator** —— 生成满足 Slack 尺寸约束的动图

## 开发与技术
- **artifacts-builder** —— 使用 React、Tailwind CSS 与 shadcn/ui 组件构建复杂的 claude.ai HTML 成品
- **mcp-server** —— 指导如何创建高质量的 MCP 服务器，以整合外部 API 与服务
- **webapp-testing** —— 借助 Playwright 对本地网页应用执行 UI 验证与调试

## 企业与沟通
- **brand-guidelines** —— 应用 Anthropic 官方品牌色与字体到各类产出物
- **internal-comms** —— 撰写内部沟通材料，如状态更新、内部刊物与常见问题
- **theme-factory** —— 使用 10 套专业预设主题，或即时生成自定义主题以美化产出物

## 元技能
- **skill-creator** —— 指导如何设计扩展 Claude 能力的高效技能
- **template-skill** —— 创建新技能时可用作起点的基础模板

# 文档技能

`document-skills/` 子目录收录的是 Anthropic 为帮助 Claude 生成各类文档格式而设计的技能，展示了处理复杂文件格式与二进制数据的高级范式：

- **docx** —— 创建、编辑与分析 Word 文档，支持修订、批注、格式保持与文本抽取
- **pdf** —— 全面的 PDF 工具箱，可提取文本与表格、创建新 PDF、合并/拆分文档并处理表单
- **pptx** —— 创建、编辑与分析 PowerPoint 演示文稿，支持版式、模板、图表与自动化幻灯片生成
- **xlsx** —— 创建、编辑与分析 Excel 表格，支持公式、格式、数据分析与可视化

**重要声明：** 这些文档技能是按时间点截取的版本，当前并未持续维护或更新。Claude 已预置包含这些技能的版本。我们提供它们主要用于参考，帮助开发者了解 Anthropic 如何设计能够处理二进制文件格式与文档结构的复杂技能。

# 在 Claude Code、Claude.ai 与 API 中体验

## Claude Code
你可以在 Claude Code 中运行以下命令，将本仓库注册为 Claude Code Plugin 市场源：
```
/plugin marketplace add anthropics/skills
```

接着安装特定技能集：
1. 选择 `Browse and install plugins`
2. 选择 `anthropic-agent-skills`
3. 选择 `document-skills` 或 `example-skills`
4. 点击 `Install now`

或者直接安装以下任一插件：
```
/plugin install document-skills@anthropic-agent-skills
/plugin install example-skills@anthropic-agent-skills
```

安装插件后，只需提及技能名称即可调用。例如，若你从市场安装了 `document-skills` 插件，可以在 Claude Code 中请求：“使用 PDF 技能提取 path/to/some-file.pdf 中的表单字段。”

## Claude.ai

这些示例技能在 Claude.ai 的付费方案中已默认提供。

如需使用本仓库中的任意技能或上传自定义技能，请参阅[在 Claude 中使用技能](https://support.claude.com/en/articles/12512180-using-skills-in-claude#h_a4222fa77b)。

## Claude API

你可以通过 Claude API 使用 Anthropic 预构建的技能，并上传自定义技能。详见 [Skills API 快速入门](https://docs.claude.com/en/api/skills-guide#creating-a-skill)。

# 创建基础技能

技能的结构非常简单：一个文件夹，内含包含 YAML 前言区与指令的 `SKILL.md` 文件。本仓库中的 **template-skill** 可作为起点：

```markdown
---
name: my-skill-name
description: A clear description of what this skill does and when to use it
---

# My Skill Name

[Add your instructions here that Claude will follow when this skill is active]

## Examples
- Example usage 1
- Example usage 2

## Guidelines
- Guideline 1
- Guideline 2
```

前言区只需要两个字段：
- `name` —— 技能的唯一标识（使用小写字母，空格请用连字符）
- `description` —— 对技能功能与适用场景的完整描述

正文部分包含 Claude 在技能激活时会遵循的指令、示例与指南。更多细节请参阅[如何创建自定义技能](https://support.claude.com/en/articles/12512198-creating-custom-skills)。

# 合作伙伴技能

技能非常适合用于提升 Claude 使用特定软件的能力。随着我们看到越来越多来自合作伙伴的优秀技能案例，可能会在此精选展示：

- **Notion** —— [Notion 面向 Claude 的技能集](https://www.notion.so/notiondevs/Notion-Skills-for-Claude-28da4445d27180c7af1df7d8615723d0)
