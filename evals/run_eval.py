from langchain_core.tools import tool, StructuredTool
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage, AIMessageChunk
from langchain_anthropic import ChatAnthropic
from functools import partial
import asyncio
import json
from pathlib import Path
from datetime import datetime
from main import build_app, get_prompts
from typing import Any
from prompt import SYSTEM_PROMPT
from contextlib import contextmanager

SERVERS = ['ha']
SNAPSHOT_DIR = (
    Path(__file__).resolve().parent.parent
    / "data" / "snapshots"
)

EVALS_DIR = (
    Path(__file__).resolve().parent
)

EVAL_RUNS_DIR = (
    Path(__file__).resolve().parent.parent
    / "data" / "eval_runs"
)
DIRS = [SNAPSHOT_DIR, EVAL_RUNS_DIR]
for d in DIRS:
    d.mkdir(parents=True, exist_ok=True)

FAKE_FUNC_RETURN_VALUE = {
    # 真实格式：用 name=餐厅灯 过滤后的 GetLiveContext 返回内容
    "homeassistant__GetLiveContext": (
        '{"result": "Live Context: An overview of the areas and the devices in this smart home:\\n'
        "- names: Dining Room Light, 餐厅灯\\n"
        "  domain: light\\n"
        "  state: 'on'\\n"
        "  areas: Dining Room\\n"
        "  attributes:\\n"
        "    brightness: '255'\\n"
        "    brightness_pct: '100'\\n\"}"
    ),
    # 真实格式，日期和时间写死，这样每次跑 eval 的结果都一样
    "llm__GetDateTime": '{"date": "2026-11-12", "time": "16:40:59", "timezone": "PST", "weekday": "Thursday"}',
}

def get_snap_shots() -> dict[str, Any]:
    snapshots = {}
    for name in SERVERS:
        path = SNAPSHOT_DIR / f"{name}.json"
        with path.open(encoding="utf-8") as f:
            snapshots[name] = json.load(f)
            
    return snapshots

def get_cases() -> dict[str, Any]:
    cases = {}
    cases_path = EVALS_DIR / "cases.json"
    with cases_path.open(encoding="utf-8") as f:
        cases = json.load(f)

    return cases

def make_fake_func(tool):
    value = FAKE_FUNC_RETURN_VALUE.get(tool, "operation success")
    async def func(**kwargs):
        # raise RuntimeError("Unknown error")
        return value
    return func
    
def generate_from_snapshots(snapshots) -> tuple[list[StructuredTool], str, dict[str, dict]]:
    tools = []
    prompts = SYSTEM_PROMPT
    servers = {}
    for name in SERVERS:
        tools += [StructuredTool(
            name=tool["name"],
            description=tool["description"],
            args_schema=tool["args_schema"],
            coroutine=make_fake_func(tool["name"]),
        ) for tool in snapshots[name]["tools"]]
        prompt = snapshots[name].get('prompt')
        if prompt:
            prompts += "\n\n" + prompt
        servers[name] = {
            "server": snapshots[name].get('server'),
            "created_at": snapshots[name].get('created_at')
        }
    return tools, prompts, servers
    
async def main():
    tools, prompts, servers = generate_from_snapshots(get_snap_shots())
    cases = get_cases()
    model_name="claude-haiku-5-5"
    model = ChatAnthropic(model=model_name)
    app = build_app(tools, prompts, model, None)
    record = {
        "run": {
            "started_at": datetime.now().strftime("%Y-%m-%dT%H-%M-%S"),
            "model": model_name,
            "snapshots": servers,
        },
        "summary": {
            "passed": 0,
            "total": 0
        },
        "results": []
    }
    for key, value in cases.items():
        input_messages = value.get("inputs")
        expected_tools = value.get("expected_tools")
        for input_message in input_messages:
            response = await app.ainvoke(MessagesState(messages=input_message))
            record['summary']['total'] += 1
            fail_reasons = []
            ai_messages = [message for message in response["messages"] if isinstance(message, AIMessage)]
            tool_calls = [
                tool_call
                for message in ai_messages
                for tool_call in message.tool_calls
            ]
            tool_messages = [message for message in response["messages"] if isinstance(message, ToolMessage)]
            tool_set = {tool['name'] for tool in tool_calls}

            if expected_tools and tool_calls and not all(tool in tool_set for tool in expected_tools):
                fail_reasons += ['调用工具和期望工具不符']
                
            if not expected_tools and tool_calls:
                fail_reasons += ['不应该调用工具']
                
            if expected_tools and not tool_calls:
                fail_reasons += ['没有调用工具']  

            if not all(tool.status == "success" for tool in tool_messages):
                fail_reasons += ['工具调用出错']
            
            if not fail_reasons:
                record['summary']['passed'] += 1
                print(f"\033[32mPASS {key} | {input_message}\033[0m")
            else:
                print(f"\033[31mFAIL {key} | {input_message}\033[0m")
                print(f"     REASON: {fail_reasons}")
                print(f"     期望: {expected_tools}")
                print(f"     实际: {tool_set}")
                
            test_result = {
                "case_id": key,
                "passed": not fail_reasons,
                "input": input_message,
                "expected_tools": expected_tools,
                "actual_tool_calls": [{ "name": tool['name'], "args": tool['args']} for tool in tool_calls],
                "final_reply": response["messages"][-1].text,
                "fail_reasons": fail_reasons
            }
            record["results"] += [test_result]

                        
    print(f"得分: {record['summary']['passed']}/{record['summary']['total']} ({record['summary']['passed']/record['summary']['total']:.2%})")
    save_file_path = EVAL_RUNS_DIR / f"{record['run']['started_at']}.json"
    with open(save_file_path, 'w', encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    print(f"结果已保存: {save_file_path}")

if __name__ == "__main__":
    asyncio.run(main())