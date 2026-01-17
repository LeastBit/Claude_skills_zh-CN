"""MCP 服务器轻量级连接处理模块。"""

from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client


class MCPConnection(ABC):
    """MCP 服务器连接的基类。"""

    def __init__(self):
        self.session = None
        self._stack = None

    @abstractmethod
    def _create_context(self):
        """根据连接类型创建连接上下文。"""

    async def __aenter__(self):
        """初始化 MCP 服务器连接。"""
        self._stack = AsyncExitStack()
        await self._stack.__aenter__()

        try:
            ctx = self._create_context()
            result = await self._stack.enter_async_context(ctx)

            if len(result) == 2:
                read, write = result
            elif len(result) == 3:
                read, write, _ = result
            else:
                raise ValueError(f"意外的上下文结果: {result}")

            session_ctx = ClientSession(read, write)
            self.session = await self._stack.enter_async_context(session_ctx)
            await self.session.initialize()
            return self
        except BaseException:
            await self._stack.__aexit__(None, None, None)
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """清理 MCP 服务器连接资源。"""
        if self._stack:
            await self._stack.__aexit__(exc_type, exc_val, exc_tb)
        self.session = None
        self._stack = None

    async def list_tools(self) -> list[dict[str, Any]]:
        """从 MCP 服务器获取可用工具列表。"""
        response = await self.session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in response.tools
        ]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """使用提供的参数调用 MCP 服务器上的工具。"""
        result = await self.session.call_tool(tool_name, arguments=arguments)
        return result.content


class MCPConnectionStdio(MCPConnection):
    """使用标准输入/输出的 MCP 连接。"""

    def __init__(self, command: str, args: list[str] = None, env: dict[str, str] = None):
        super().__init__()
        self.command = command
        self.args = args or []
        self.env = env

    def _create_context(self):
        return stdio_client(
            StdioServerParameters(command=self.command, args=self.args, env=self.env)
        )


class MCPConnectionSSE(MCPConnection):
    """使用服务器发送事件 (SSE) 的 MCP 连接。"""

    def __init__(self, url: str, headers: dict[str, str] = None):
        super().__init__()
        self.url = url
        self.headers = headers or {}

    def _create_context(self):
        return sse_client(url=self.url, headers=self.headers)


class MCPConnectionHTTP(MCPConnection):
    """使用流式 HTTP 的 MCP 连接。"""

    def __init__(self, url: str, headers: dict[str, str] = None):
        super().__init__()
        self.url = url
        self.headers = headers or {}

    def _create_context(self):
        return streamablehttp_client(url=self.url, headers=self.headers)


def create_connection(
    transport: str,
    command: str = None,
    args: list[str] = None,
    env: dict[str, str] = None,
    url: str = None,
    headers: dict[str, str] = None,
) -> MCPConnection:
    """创建适当的 MCP 连接的工厂函数。

    参数:
        transport: 连接类型 ("stdio"、"sse" 或 "http")
        command: 要运行的命令 (仅限 stdio)
        args: 命令参数 (仅限 stdio)
        env: 环境变量 (仅限 stdio)
        url: 服务器 URL (仅限 sse 和 http)
        headers: HTTP 头 (仅限 sse 和 http)

    返回:
        MCPConnection 实例
    """
    transport = transport.lower()

    if transport == "stdio":
        if not command:
            raise ValueError("stdio 传输需要提供命令")
        return MCPConnectionStdio(command=command, args=args, env=env)

    elif transport == "sse":
        if not url:
            raise ValueError("sse 传输需要提供 URL")
        return MCPConnectionSSE(url=url, headers=headers)

    elif transport in ["http", "streamable_http", "streamable-http"]:
        if not url:
            raise ValueError("http 传输需要提供 URL")
        return MCPConnectionHTTP(url=url, headers=headers)

    else:
        raise ValueError(f"不支持的传输类型: {transport}。请使用 'stdio'、'sse' 或 'http'")
