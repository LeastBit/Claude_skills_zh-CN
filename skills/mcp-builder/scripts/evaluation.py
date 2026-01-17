"""MCP 服务器评估工具

此脚本通过使用 Claude 运行测试问题来评估 MCP 服务器。
"""

import argparse
import asyncio
import json
import re
import sys
import time
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from anthropic import Anthropic

from connections import create_connection

EVALUATION_PROMPT = """你是一个可以使用工具的 AI 助手。

当收到任务时，你必须：
1. 使用可用的工具来完成任务
2. 提供你方法中每个步骤的摘要，用 <summary> 标签包裹
3. 提供对所提供工具的反馈，用 <feedback> 标签包裹
4. 提供你的最终响应，用 <response> 标签包裹

摘要要求：
- 在你的 <summary> 标签中，你必须解释：
  - 你完成任务所采取的步骤
  - 你使用了哪些工具，按什么顺序，以及为什么
  - 你为每个工具提供的输入
  - 你从每个工具收到的输出
  - 你如何得出响应的摘要

反馈要求：
- 在你的 <feedback> 标签中，提供对工具的建设性反馈：
  - 评论工具名称：它们是否清晰且具有描述性？
  - 评论输入参数：它们是否有良好的文档？必需参数和可选参数是否清晰？
  - 评论描述：它们是否准确描述了工具的功能？
  - 评论工具使用过程中遇到的任何错误：工具是否执行失败？工具是否返回了太多 token？
  - 确定具体的改进领域并解释为什么这些改进会有帮助
  - 提供具体且可操作的建议

响应要求：
- 你的响应应该简洁并直接回答所问的问题
- 始终用 <response> 标签包裹你的最终响应
- 如果你无法解决任务，返回 <response>NOT_FOUND</response>
- 对于数字响应，只提供数字
- 对于 ID，只提供 ID
- 对于名称或文本，提供所请求的确切文本
- 你的响应应该放在最后"""


def parse_evaluation_file(file_path: Path) -> list[dict[str, Any]]:
    """解析包含 qa_pair 元素的 XML 评估文件。"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        evaluations = []

        for qa_pair in root.findall(".//qa_pair"):
            question_elem = qa_pair.find("question")
            answer_elem = qa_pair.find("answer")

            if question_elem is not None and answer_elem is not None:
                evaluations.append({
                    "question": (question_elem.text or "").strip(),
                    "answer": (answer_elem.text or "").strip(),
                })

        return evaluations
    except Exception as e:
        print(f"解析评估文件 {file_path} 时出错: {e}")
        return []


def extract_xml_content(text: str, tag: str) -> str | None:
    """从 XML 标签中提取内容。"""
    pattern = rf"<{tag}>(.*?)</{tag}>"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches[-1].strip() if matches else None


async def agent_loop(
    client: Anthropic,
    model: str,
    question: str,
    tools: list[dict[str, Any]],
    connection: Any,
) -> tuple[str, dict[str, Any]]:
    """使用 MCP 工具运行代理循环。"""
    messages = [{"role": "user", "content": question}]

    response = await asyncio.to_thread(
        client.messages.create,
        model=model,
        max_tokens=4096,
        system=EVALUATION_PROMPT,
        messages=messages,
        tools=tools,
    )

    messages.append({"role": "assistant", "content": response.content})

    tool_metrics = {}

    while response.stop_reason == "tool_use":
        tool_use = next(block for block in response.content if block.type == "tool_use")
        tool_name = tool_use.name
        tool_input = tool_use.input

        tool_start_ts = time.time()
        try:
            tool_result = await connection.call_tool(tool_name, tool_input)
            tool_response = json.dumps(tool_result) if isinstance(tool_result, (dict, list)) else str(tool_result)
        except Exception as e:
            tool_response = f"执行工具 {tool_name} 时出错: {str(e)}\n"
            tool_response += traceback.format_exc()
        tool_duration = time.time() - tool_start_ts

        if tool_name not in tool_metrics:
            tool_metrics[tool_name] = {"count": 0, "durations": []}
        tool_metrics[tool_name]["count"] += 1
        tool_metrics[tool_name]["durations"].append(tool_duration)

        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": tool_response,
            }]
        })

        response = await asyncio.to_thread(
            client.messages.create,
            model=model,
            max_tokens=4096,
            system=EVALUATION_PROMPT,
            messages=messages,
            tools=tools,
        )
        messages.append({"role": "assistant", "content": response.content})

    response_text = next(
        (block.text for block in response.content if hasattr(block, "text")),
        None,
    )
    return response_text, tool_metrics


async def evaluate_single_task(
    client: Anthropic,
    model: str,
    qa_pair: dict[str, Any],
    tools: list[dict[str, Any]],
    connection: Any,
    task_index: int,
) -> dict[str, Any]:
    """使用给定的工具评估单个问答对。"""
    start_time = time.time()

    print(f"任务 {task_index + 1}: 正在运行任务，问题: {qa_pair['question']}")
    response, tool_metrics = await agent_loop(client, model, qa_pair["question"], tools, connection)

    response_value = extract_xml_content(response, "response")
    summary = extract_xml_content(response, "summary")
    feedback = extract_xml_content(response, "feedback")

    duration_seconds = time.time() - start_time

    return {
        "question": qa_pair["question"],
        "expected": qa_pair["answer"],
        "actual": response_value,
        "score": int(response_value == qa_pair["answer"]) if response_value else 0,
        "total_duration": duration_seconds,
        "tool_calls": tool_metrics,
        "num_tool_calls": sum(len(metrics["durations"]) for metrics in tool_metrics.values()),
        "summary": summary,
        "feedback": feedback,
    }


REPORT_HEADER = """
# 评估报告

## 摘要

- **准确率**: {correct}/{total} ({accuracy:.1f}%)
- **平均任务耗时**: {average_duration_s:.2f}秒
- **每个任务平均工具调用次数**: {average_tool_calls:.2f}
- **工具调用总次数**: {total_tool_calls}

---
"""

TASK_TEMPLATE = """
### 任务 {task_num}

**问题**: {question}
**标准答案**: `{expected_answer}`
**实际答案**: `{actual_answer}`
**正确**: {correct_indicator}
**耗时**: {total_duration:.2f}秒
**工具调用**: {tool_calls}

**摘要**
{summary}

**反馈**
{feedback}

---
"""


async def run_evaluation(
    eval_path: Path,
    connection: Any,
    model: str = "claude-3-7-sonnet-20250219",
) -> str:
    """使用 MCP 服务器工具运行评估。"""
    print("🚀 开始评估")

    client = Anthropic()

    tools = await connection.list_tools()
    print(f"📋 从 MCP 服务器加载了 {len(tools)} 个工具")

    qa_pairs = parse_evaluation_file(eval_path)
    print(f"📋 加载了 {len(qa_pairs)} 个评估任务")

    results = []
    for i, qa_pair in enumerate(qa_pairs):
        print(f"正在处理任务 {i + 1}/{len(qa_pairs)}")
        result = await evaluate_single_task(client, model, qa_pair, tools, connection, i)
        results.append(result)

    correct = sum(r["score"] for r in results)
    accuracy = (correct / len(results)) * 100 if results else 0
    average_duration_s = sum(r["total_duration"] for r in results) / len(results) if results else 0
    average_tool_calls = sum(r["num_tool_calls"] for r in results) / len(results) if results else 0
    total_tool_calls = sum(r["num_tool_calls"] for r in results)

    report = REPORT_HEADER.format(
        correct=correct,
        total=len(results),
        accuracy=accuracy,
        average_duration_s=average_duration_s,
        average_tool_calls=average_tool_calls,
        total_tool_calls=total_tool_calls,
    )

    report += "".join([
        TASK_TEMPLATE.format(
            task_num=i + 1,
            question=qa_pair["question"],
            expected_answer=qa_pair["answer"],
            actual_answer=result["actual"] or "N/A",
            correct_indicator="✅" if result["score"] else "❌",
            total_duration=result["total_duration"],
            tool_calls=json.dumps(result["tool_calls"], indent=2),
            summary=result["summary"] or "N/A",
            feedback=result["feedback"] or "N/A",
        )
        for i, (qa_pair, result) in enumerate(zip(qa_pairs, results))
    ])

    return report


def parse_headers(header_list: list[str]) -> dict[str, str]:
    """将 'Key: Value' 格式的头字符串解析为字典。"""
    headers = {}
    if not header_list:
        return headers

    for header in header_list:
        if ":" in header:
            key, value = header.split(":", 1)
            headers[key.strip()] = value.strip()
        else:
            print(f"警告: 忽略格式错误的头: {header}")
    return headers


def parse_env_vars(env_list: list[str]) -> dict[str, str]:
    """将 'KEY=VALUE' 格式的环境变量字符串解析为字典。"""
    env = {}
    if not env_list:
        return env

    for env_var in env_list:
        if "=" in env_var:
            key, value = env_var.split("=", 1)
            env[key.strip()] = value.strip()
        else:
            print(f"警告: 忽略格式错误的环境变量: {env_var}")
    return env


async def main():
    parser = argparse.ArgumentParser(
        description="使用测试问题评估 MCP 服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 评估本地 stdio MCP 服务器
  python evaluation.py -t stdio -c python -a my_server.py eval.xml

  # 评估 SSE MCP 服务器
  python evaluation.py -t sse -u https://example.com/mcp -H "Authorization: Bearer token" eval.xml

  # 使用自定义模型评估 HTTP MCP 服务器
  python evaluation.py -t http -u https://example.com/mcp -m claude-3-5-sonnet-20241022 eval.xml
        """,
    )

    parser.add_argument("eval_file", type=Path, help="评估 XML 文件的路径")
    parser.add_argument("-t", "--transport", choices=["stdio", "sse", "http"], default="stdio", help="传输类型 (默认: stdio)")
    parser.add_argument("-m", "--model", default="claude-3-7-sonnet-20250219", help="使用的 Claude 模型 (默认: claude-3-7-sonnet-20250219)")

    stdio_group = parser.add_argument_group("stdio 选项")
    stdio_group.add_argument("-c", "--command", help="运行 MCP 服务器的命令 (仅限 stdio)")
    stdio_group.add_argument("-a", "--args", nargs="+", help="命令的参数 (仅限 stdio)")
    stdio_group.add_argument("-e", "--env", nargs="+", help="KEY=VALUE 格式的环境变量 (仅限 stdio)")

    remote_group = parser.add_argument_group("sse/http 选项")
    remote_group.add_argument("-u", "--url", help="MCP 服务器 URL (仅限 sse/http)")
    remote_group.add_argument("-H", "--header", nargs="+", dest="headers", help="'Key: Value' 格式的 HTTP 头 (仅限 sse/http)")

    parser.add_argument("-o", "--output", type=Path, help="评估报告的输出文件 (默认: stdout)")

    args = parser.parse_args()

    if not args.eval_file.exists():
        print(f"错误: 评估文件未找到: {args.eval_file}")
        sys.exit(1)

    headers = parse_headers(args.headers) if args.headers else None
    env_vars = parse_env_vars(args.env) if args.env else None

    try:
        connection = create_connection(
            transport=args.transport,
            command=args.command,
            args=args.args,
            env=env_vars,
            url=args.url,
            headers=headers,
        )
    except ValueError as e:
        print(f"错误: {e}")
        sys.exit(1)

    print(f"🔗 正在通过 {args.transport} 连接到 MCP 服务器...")

    async with connection:
        print("✅ 连接成功")
        report = await run_evaluation(args.eval_file, connection, args.model)

        if args.output:
            args.output.write_text(report)
            print(f"\n✅ 报告已保存到 {args.output}")
        else:
            print("\n" + report)


if __name__ == "__main__":
    asyncio.run(main())
