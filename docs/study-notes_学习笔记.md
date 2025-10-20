# 学习笔记（基于 Anthropic Skills 中文版）

这份学习笔记帮助你系统掌握本仓库的技能体系，并提供可直接落地的实用场景扩展，尤其覆盖“超大型应用开发项目”的端到端落地蓝图。目标是：在最短时间内把技能用到真实工作之中，形成标准化、可复用的工作流。

—

## 1. 学习路径总览（建议 2–5 天）

- 第 0 天：快速浏览与安装
  - 阅读仓库根目录 README，了解技能分类与能力边界
  - 在 Claude Code 中安装 example-skills 或 document-skills 插件，尝试调用 1–2 个技能
- 第 1 天：文档技能（DOCX/PDF/PPTX/XLSX）
  - 重点阅读：document-skills_文档技能/docx_Word文档、pptx_演示文稿、pdf_PDF文档、xlsx_电子表格 中的 SKILL.md
  - 跑通典型流程：将 DOCX 转为 Markdown、对 OOXML 做最小化修改、重新打包回 DOCX
- 第 2 天：工程与自动化
  - 阅读 artifacts-builder_制品构建器 与 webapp-testing_网页应用测试，掌握前端制品的初始化与一键打包
  - 阅读 mcp-builder_MCP构建器，理解如何把外部系统/服务以 MCP Server 的方式接入
- 第 3–5 天：实践与扩展
  - 选 1 个实用场景（如周报自动化/招投标资料/前端小工具）做端到端实操
  - 对输出进行回顾：是否可复用？是否可一键化？是否具备审计/回溯能力？

—

## 2. 技能地图与典型组合

- 文档类
  - docx + pdf + pptx + xlsx：打造“PRD+评审+发布+签署+归档”的全流程
- 工程类
  - artifacts-builder：React/TS/Tailwind/shadcn 前端产物一键生成与打包
  - webapp-testing：基于 Playwright 的 UI 自动化验证
  - mcp-builder：面向企业外部系统的集成（API/数据库/内部平台）
- 传播与品牌
  - internal-comms + brand-guidelines + theme-factory + canvas-design + slack-gif-creator

常见“套餐”示例：
- 交付资料全家桶：docx + pptx + pdf + theme-factory + brand-guidelines
- 需求到上线（轻量）：docx（PRD/ADR）+ artifacts-builder（前端）+ webapp-testing（回归）+ internal-comms（通告）
- 企业系统集成：mcp-builder（接口/工具）+ document-skills（报告/归档）

—

## 3. 实用场景扩展

### 3.1 超大型应用开发项目（端到端蓝图）

适用对象：10–100+ 人规模、跨多团队、多仓或 Monorepo、多环境（Dev/QA/Staging/Prod）、对文档与合规有严格要求的组织。

A. 能力蓝图（按职责域拆分）
- 需求与方案
  - PRD/BRD：docx（修订与批注为核心）、pdf（归档）、pptx（评审）
  - 架构与 ADR：docx（记录决策）、pptx（评审演讲稿）、canvas-design（架构图/系统视图）
- 研发与质量
  - 前端工程：artifacts-builder 初始化 + 一键 bundle.html 输出（便于分享/演示）
  - UI 回归：webapp-testing 生成与运行基本场景脚本
  - 接口/外部系统：mcp-builder 将 CI、工单、监控、制品库等接成工具（后续可做自动化流程）
- 运维与发布
  - 发布说明/变更日志/回滚预案：docx + pdf
  - 合规签署（安全/隐私/法务）：docx（修订模式）+ pdf（盖章归档）
- 沟通与变更管理
  - 内部沟通：internal-comms（周报、里程碑通告、功能上线公告）
  - 品牌一致性：brand-guidelines + theme-factory（对外材料风格统一）

B. 典型目录结构（Monorepo 示例）
```
apps/
  web/                 # 前端（artifacts-builder 初始化）
  admin/               # 管理端（同上）
services/
  user-service/        # 微服务（示例：Node/TS 或 Python）
  order-service/
packages/
  ui/                  # 共享组件库（shadcn/ui 扩展）
  config/              # 工具链与规范配置
ops/
  runbooks/            # 运维手册与 SOP（docx + pdf）
  release/             # 版本说明、回滚预案、签署材料
docs/
  prd/                 # 需求文档（docx 修订/批注）
  adr/                 # 架构决策记录（docx）
  reviews/             # 评审材料（pptx）
```

C. 端到端实施流程（可复制）
1) 需求与评审
- 使用 docx 技能创建 PRD 模版，开启修订模式收集评论与变更
- 生成 pptx 评审稿，嵌入关键架构图（canvas-design）与流程图
- 使用 pdf 技能产出评审纪要与会签文件

2) 架构与 ADR
- 为每个关键决策创建 ADR（docx）：背景、方案、取舍、影响、状态
- 重要架构在 pptx 中以“问题 -> 备选方案 -> 评估矩阵 -> 结论”的形式讲清楚

3) 脚手架与代码组织
- 前端：
  - 初始化：bash artifacts-builder_制品构建器/scripts/init-artifact.sh <project-name>
  - 开发完成后：bash artifacts-builder_制品构建器/scripts/bundle-artifact.sh 生成 bundle.html 便于评审/传播
- 服务端：
  - 依据 mcp-builder 设计工具接口（如 issue 查询、流水线状态、制品查询、告警检索等）
  - 使用 TypeScript/Python SDK 为关键外部系统抽象“工作流级工具”（而非简单端点透传）

4) 测试与质量
- Web UI：参考 webapp-testing_网页应用测试 的 Playwright 用法，覆盖核心路径（登录、下单、退款、权限）
- 文档质量：docx 修订最小化原则，仅标记真实变更；最终用 pandoc 转 Markdown 双向验证

5) 发布与合规
- 生成发布说明（docx）、风险评估与回滚预案（docx->pdf），准备签署与归档
- 若涉及外部审计，打包“证据包”（变更单/评审纪要/测试报告/制品校验摘要）为 pdf

6) 沟通与沉淀
- 内部通告（internal-comms）：从“Why/What/How/Impact/Rollback/Contact”结构生成公告
- 外部材料（brand-guidelines + theme-factory）：确保视觉一致性，一键生成主题并套用到 pptx/海报

D. Prompt 配方（示例，可直接在 Claude 中使用）
- PRD 模版生成（docx）
  - “使用 document-skills/docx，创建一份适用于 BFF+微服务大型项目的 PRD 模版，包含：背景、范围、非功能性需求、接口草案、验收标准。要求：开启修订模式，给出示例占位内容。”
- 架构评审稿（pptx + canvas-design）
  - “生成 12 页以内的架构评审稿：1) 问题与目标，2) 方案候选，3) 评估矩阵，4) 选型结论，5) 迁移路线。需要 2 张系统组件图，请用 canvas-design 生成 PNG 并插入。”
- UI 回归（webapp-testing）
  - “为登录/下单/退款/权限四条路径生成 Playwright 测试脚本与运行说明，要求包含准备数据与清理步骤。”
- 外部系统集成（mcp-builder）
  - “为 Git 平台 + CI + 监控系统设计一组 MCP 工具，使得‘查找失败发布 -> 回溯相关 PR/Commit -> 检索告警与日志 -> 生成故障纪要’能在 5 次以内工具调用完成。”

E. 质量清单（落地前自检）
- 文档：
  - PRD/ADR 是否开启修订、最小化标注、可追溯？
  - pptx 是否结构清晰、页数克制、视觉统一？
- 代码与脚手架：
  - 前端产物能否一键打包成 bundle.html？
  - MCP 工具是否围绕工作流而非端点？是否有错误引导与分页策略？
- 测试：
  - Web 关键路径是否覆盖？是否具备稳定数据与隔离？
- 发布与合规：
  - 发布说明/回滚预案是否准备齐全？证据包是否可复核？

—

### 3.2 企业资料自动化套件（投标/尽调/招采）
- 通过 docx + pptx + pdf 生成：公司介绍、案例集、技术白皮书、报价清单、资质证明
- 使用 theme-factory 套用统一主题，brand-guidelines 统一色彩与字体
- 将签署版转为 pdf 归档并输出“打包清单”（变更摘要、页码索引）

### 3.3 合规与安全审计准备
- 依据 ISO/隐私/安全条线准备政策与流程文档（docx 修订 + 最小化变更）
- 生成矩阵型检查表（xlsx），并以 pdf 形成最终提交物

### 3.4 产品发布资料一键化
- 生成对内对外两套材料：
  - 内部：变更说明/风险评估/回滚预案（docx）+ 评审稿（pptx）
  - 外部：公告（internal-comms）+ 宣传页（canvas-design）+ 演示动图（slack-gif-creator）

### 3.5 数据分析周报/经营看板
- xlsx 汇总数据 + pptx 可视化，docx 写出“洞察与下一步”

—

## 4. 与本仓库技能的映射（快速导航）

- 文档技能（DOCX/PDF/PPTX/XLSX）：./document-skills_文档技能/
- 前端制品：./artifacts-builder_制品构建器/
- UI 测试：./webapp-testing_网页应用测试/
- MCP 集成：./mcp-builder_MCP构建器/
- 品牌与传播：./brand-guidelines_品牌指南、./theme-factory_主题工厂、./canvas-design_画布设计、./slack-gif-creator_SlackGIF生成器/
- 技能创建实践：./skill-creator_技能创建器、./template-skill_模板技能

—

## 5. 常用命令与工具备忘

- DOCX/OOXML
  - 解包：python document-skills_文档技能/docx_Word文档/ooxml/scripts/unpack.py <file.docx> <dir>
  - 打包：python document-skills_文档技能/docx_Word文档/ooxml/scripts/pack.py <dir> <file.docx>
  - 转 Markdown：pandoc --track-changes=all input.docx -o output.md
- PDF
  - DOCX 转 PDF：soffice --headless --convert-to pdf document.docx
  - PDF 转图片：pdftoppm -jpeg -r 150 document.pdf page
- 前端成品
  - 初始化：bash artifacts-builder_制品构建器/scripts/init-artifact.sh <project-name>
  - 打包：bash artifacts-builder_制品构建器/scripts/bundle-artifact.sh

—

## 6. 常见问题（FAQ）

- 我该选用哪种文档工作流？
  - 简易阅读/摘取：pandoc 转 Markdown
  - 严肃编辑：OOXML + 修订模式（最小化变更）
- 为什么强调“工作流级 MCP 工具”？
  - 因为端点透传会放大上下文成本；聚合/整合后的工具能减少调用轮次、降低误用概率
- 什么时候用 bundle.html？
  - 评审/演示/归档/交付的轻量场景，尤其适合在 Claude 里直接预览和分享

—

## 7. 下一步

- 挑一个你最迫切的业务场景，套用第 3 章的蓝图做一次端到端交付
- 将过程沉淀为“模版 + 脚本 + 清单”，推回到团队标准化资产库
- 若需接外部系统，优先设计“工作流级 MCP 工具”，再考虑单点功能
