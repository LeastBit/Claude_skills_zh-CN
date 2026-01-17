# MCP 服务器最佳实践

## 快速参考

### 服务器命名
- **Python**：`{service}_mcp`（例如 `slack_mcp`）
- **Node/TypeScript**：`{service}-mcp-server`（例如 `slack-mcp-server`）

### 工具命名
- 使用带服务前缀的 snake_case
- 格式：`{service}_{action}_{resource}`
- 示例：`slack_send_message`、`github_create_issue`

### 响应格式
- 支持 JSON 和 Markdown 格式
- JSON 用于程序化处理
- Markdown 用于人类可读性

### 分页
- 始终遵守 `limit` 参数
- 返回 `has_more`、`next_offset`、`total_count`
- 默认 20-50 条

### 传输
- **流式 HTTP**：用于远程服务器、多客户端场景
- **stdio**：用于本地集成、命令行工具
- 避免使用 SSE（已弃用，推荐使用流式 HTTP）

---

## 服务器命名约定

遵循这些标准化命名模式：

**Python**：使用格式 `{service}_mcp`（小写带下划线）
- 示例：`slack_mcp`、`github_mcp`、`jira_mcp`

**Node/TypeScript**：使用格式 `{service}-mcp-server`（小写带连字符）
- 示例：`slack-mcp-server`、`github-mcp-server`、`jira-mcp-server`

名称应该：
- 通用，描述被集成的服务
- 易于从任务描述推断
- 不包含版本号

---

## 工具命名与设计

### 工具命名

1. **使用 snake_case**：`search_users`、`create_project`、`get_channel_info`
2. **包含服务前缀**：预期您的 MCP 服务器可能与其他 MCP 服务器一起使用
   - 使用 `slack_send_message` 而不只是 `send_message`
   - 使用 `github_create_issue` 而不只是 `create_issue`
3. **面向动作**：以动词开头（get、list、search、create 等）
4. **具体明确**：避免可能与其他服务器冲突的通用名称

### 工具设计

- 工具描述必须狭窄且明确地描述功能
- 描述必须精确匹配实际功能
- 提供工具注解（readOnlyHint、destructiveHint、idempotentHint、openWorldHint）
- 保持工具操作聚焦和原子性

---

## 响应格式

所有返回数据的工具应支持多种格式：

### JSON 格式（`response_format="json"`）
- 机器可读的结构化数据
- 包含所有可用字段和元数据
- 一致的字段名称和类型
- 用于程序化处理

### Markdown 格式（`response_format="markdown"`，通常为默认）
- 人类可读的格式化文本
- 使用标题、列表和格式以增加清晰度
- 将时间戳转换为人类可读格式
- 显示带括号 ID 的显示名称
- 省略冗长的元数据

---

## 分页

对于列出资源的工具：

- **始终遵守 `limit` 参数**
- **实现分页**：使用 `offset` 或基于游标的分页
- **返回分页元数据**：包含 `has_more`、`next_offset`/`next_cursor`、`total_count`
- **永不将所有结果加载到内存**：对于大型数据集尤其重要
- **默认合理限制**：通常 20-50 条

分页响应示例：
```json
{
  "total": 150,
  "count": 20,
  "offset": 0,
  "items": [...],
  "has_more": true,
  "next_offset": 20
}
```

---

## 传输选项

### 流式 HTTP

**最适合**：远程服务器、Web 服务、多客户端场景

**特性**：
- 通过 HTTP 进行双向通信
- 支持多个同时客户端
- 可以部署为 Web 服务
- 启用服务器到客户端的通知

**使用场景**：
- 同时服务多个客户端
- 部署为云服务
- 与 Web 应用程序集成

### stdio

**最适合**：本地集成、命令行工具

**特性**：
- 标准输入/输出流通信
- 设置简单，无需网络配置
- 作为客户端的子进程运行

**使用场景**：
- 为本地开发环境构建工具
- 与桌面应用程序集成
- 单用户、单会话场景

**注意**：stdio 服务器不应记录到 stdout（使用 stderr 进行日志记录）

### 传输选择

| 标准 | stdio | 流式 HTTP |
|-----------|-------|-----------------|
| **部署** | 本地 | 远程 |
| **客户端** | 单个 | 多个 |
| **复杂度** | 低 | 中等 |
| **实时** | 否 | 是 |

---

## 安全最佳实践

### 认证和授权

**OAuth 2.1**：
- 使用来自认可机构证书的安全 OAuth 2.1
- 在处理请求之前验证访问令牌
- 仅接受专门用于您服务器的令牌

**API 密钥**：
- 将 API 密钥存储在环境变量中，永不放在代码中
- 在服务器启动时验证密钥
- 认证失败时提供清晰的错误消息

### 输入验证

- 清理文件路径以防止目录遍历
- 验证 URL 和外部标识符
- 检查参数大小和范围
- 防止系统调用中的命令注入
- 对所有输入使用模式验证（Pydantic/Zod）

### 错误处理

- 不要向客户端暴露内部错误
- 在服务器端记录安全相关错误
- 提供有帮助但不泄露信息的错误消息
- 错误后清理资源

### DNS 重绑定保护

对于本地运行的流式 HTTP 服务器：
- 启用 DNS 重绑定保护
- 验证所有传入连接的 `Origin` 头
- 绑定到 `127.0.0.1` 而不是 `0.0.0.0`

---

## 工具注解

提供注解以帮助客户端理解工具行为：

| 注解 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `readOnlyHint` | boolean | false | 工具不修改其环境 |
| `destructiveHint` | boolean | true | 工具可能执行破坏性更新 |
| `idempotentHint` | boolean | false | 使用相同参数重复调用没有额外效果 |
| `openWorldHint` | boolean | true | 工具与外部实体交互 |

**重要**：注解是提示，不是安全保证。客户端不应仅基于注解做出安全关键决策。

---

## 错误处理

- 使用标准 JSON-RPC 错误代码
- 在结果对象内报告工具错误（不是协议级错误）
- 提供有帮助、具体的错误消息，包含建议的下一步
- 不要暴露内部实现细节
- 错误时正确清理资源

错误处理示例：
```typescript
try {
  const result = performOperation();
  return { content: [{ type: "text", text: result }] };
} catch (error) {
  return {
    isError: true,
    content: [{
      type: "text",
      text: `错误：${error.message}。尝试使用 filter='active_only' 来减少结果。`
    }]
  };
}
```

---

## 测试要求

全面的测试应涵盖：

- **功能测试**：使用有效/无效输入验证正确执行
- **集成测试**：测试与外部系统的交互
- **安全测试**：验证认证、输入清理、速率限制
- **性能测试**：检查负载下的行为、超时
- **错误处理**：确保正确的错误报告和清理

---

## 文档要求

- 提供所有工具和功能的清晰文档
- 包含工作示例（每个主要功能至少 3 个）
- 记录安全注意事项
- 指定所需的权限和访问级别
- 记录速率限制和性能特性
