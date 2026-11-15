from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from langchain_anthropic import ChatAnthropic
from langchain.chat_models import init_chat_model
from typing import TypedDict, cast
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import sqlite3
from anthropic import APIConnectionError, APIStatusError

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage, AIMessageChunk
from langchain_core.tools import tool
from datetime import datetime
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.runnables import RunnableConfig

import os
import asyncio
from tools import get_tools
from prompt import get_prompts
from logger import register_agent_logger
from config import DB_PATH, MODEL_NAME, MODEL_TIMEOUT
import logging

DB_PATH.parent.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger('bg')

def route(state: MessagesState) -> str:
    if state["messages"][-1].tool_calls:
        return "tools_node"
    return END
    
def build_app(tools, prompts, model, checkpointer):
    model_with_tools = model.bind_tools(tools)

    def on_tool_error(e: Exception) -> str:
        logger.error(f"工具执行失败: {e}", exc_info=e)
        return f"工具执行失败: {e}"


                    
    async def agent(state: MessagesState) -> dict:
        ans = await model_with_tools.ainvoke([SystemMessage(content=prompts), *state["messages"]])    
        for call in ans.tool_calls:
            # print(f"[调用工具] {call['name']}")
            logger.info(f"[调用工具]: {call['name']} [参数]: {call['args']}")
        if ans.text:
            logger.info(f"{ans.text}")
        return { "messages": [ans] } 

    graph = StateGraph(MessagesState)
    graph.add_node("agent_node", agent)
    graph.add_node('tools_node', ToolNode(tools, handle_tool_errors=on_tool_error))

    graph.set_entry_point("agent_node")
    graph.add_conditional_edges("agent_node", route, {
        "tools_node": "tools_node",
        END: END
    })
    graph.add_edge('tools_node', 'agent_node')

    return graph.compile(checkpointer=checkpointer)




    
async def main():
    config: RunnableConfig = {"configurable": {"thread_id": "1"}} 
    try:
        logger.info("BG is starting...")
        print(f"BG is starting...")
        tools = await get_tools()
        prompts = await get_prompts()
        model = ChatAnthropic(model=MODEL_NAME, timeout=MODEL_TIMEOUT)

        async with AsyncSqliteSaver.from_conn_string(str(DB_PATH)) as saver:
            app = build_app(tools, prompts, model, saver)
            # path.write_bytes(app.get_graph().draw_mermaid_png())   
            print(f"BG 已启动")
            logger.info(f"bg 启动了")
            while True:
                user_input = input("你： ").strip()
                if not user_input:
                    continue
                if user_input == 'exit':
                    break
                if user_input.startswith("/thread "):
                    parts = user_input.split()
                    if len(parts) != 2:
                        print("用法： /thread 2")
                        continue
                    config["configurable"] = {"thread_id": parts[1]}
                    print(f"已经切换到对话 {parts[1]}")
                    continue
                logger.info(f"thread_id={config['configurable']['thread_id']} content={user_input}")
                try:
                    async for chunk, meta in app.astream({ "messages": [HumanMessage(content=user_input)]}, config, stream_mode="messages"):
                        if cast(dict, meta)["langgraph_node"] == "agent_node" and isinstance(chunk, AIMessage):
                            
                        # if meta['langgraph_node'] == "agent_node":
                            print(chunk.text, end="", flush=True)
                    print()
                except APIConnectionError as e:
                    print()
                    logger.exception(f"API 连接出问题了: {e}")
                    print(f'API 连接出问题了: {e}')
                except APIStatusError as e:
                    print()
                    if e.status_code == 429 or e.status_code >= 500:
                        print(f"api status错误 稍后请重试: {e}")
                        logger.exception(f"api status错误 稍后请重试: {e}")
                    elif e.status_code == 401:
                        print(f"API 认证失败，bg 即将退出 请检查 ANTHROPIC_API_KEY")
                        logger.exception(f"API 认证失败，bg 即将退出 请检查 ANTHROPIC_API_KEY")
                        break
                    elif e.status_code >= 400:
                        print(f"API Status问题 请检查配置: {e}")
                        logger.exception(f"API Status问题 请检查配置: {e}")
                except Exception as e:
                    print()
                    print(f"发现错误: {e}")
                    logger.exception(f"发现错误: {e}")
                    
    except sqlite3.Error as e: 
        logger.exception(f"数据库错误: {e}")
        print(f"数据库出错: {e}")
        raise

    except Exception as e:
        logger.exception(f"出错了: {e}")
        raise
    
    
    
if __name__ == "__main__":
    load_dotenv()
    register_agent_logger()
    asyncio.run(main())
        