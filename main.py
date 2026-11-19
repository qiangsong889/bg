import asyncio
import sqlite3
from langchain_anthropic import ChatAnthropic
from typing import cast
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from anthropic import APIConnectionError, APIStatusError
from dotenv import load_dotenv
from langgraph.store.sqlite.aio import AsyncSqliteStore

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from contextlib import AsyncExitStack

from config import DB_PATH, MODEL_NAME, MODEL_TIMEOUT
from tools import get_tools
from prompt import get_prompts
from logger import register_agent_logger
from graph import build_app
import logging

logger = logging.getLogger('bg')


class FatalError(Exception):
    """无法继续运行的错误，REPL 应该退出"""
    


async def run_turn(app, user_input, config):
    try:
        async for chunk, meta in app.astream(
                {"messages": [HumanMessage(content=user_input)]},
                config,
                stream_mode="messages",
            ):
                if cast(dict, meta)["langgraph_node"] == "agent_node" and isinstance(chunk, AIMessage):
                    if chunk.text:
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
            raise FatalError("API 认证失败") from e
        elif e.status_code >= 400:
            print(f"API Status问题 请检查配置: {e}")
            logger.exception(f"API Status问题 请检查配置: {e}")
    except Exception as e:
        print()
        print(f"发现错误: {e}")
        logger.exception(f"发现错误: {e}")
            

def handle_command(user_input, config):
    parts = user_input.split()
    if len(parts) != 2:
        print("用法： /thread 2")
        return
    config["configurable"] = {"thread_id": parts[1]}
    print(f"已经切换到对话 {parts[1]}")
    logger.info(f"已经切换到对话 {parts[1]}")

async def main():
    config: RunnableConfig = {"configurable": {"thread_id": "1"}} 
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        logger.info("BG is starting...")
        print(f"BG is starting...")
        tools = await get_tools()
        prompts = await get_prompts()
        model = ChatAnthropic(model=MODEL_NAME, timeout=MODEL_TIMEOUT)
        async with AsyncExitStack() as stack:
            saver = await stack.enter_async_context(AsyncSqliteSaver.from_conn_string(str(DB_PATH)))
            store = await stack.enter_async_context(AsyncSqliteStore.from_conn_string(str(DB_PATH)))
            
            app = build_app(tools, prompts, model, saver, store)
            
            print(f"BG is live")
            print(f"current thread_id = {config.get('configurable')}")
            logger.info(f"bg is live")
            logger.info(f"current thread_id = {config.get('configurable')}")
            
            while True:
                user_input = input("你： ").strip()
                if not user_input:
                    continue
                if user_input == 'exit':
                    break
                if user_input.startswith("/thread "):
                    handle_command(user_input, config)
                    continue
                
                logger.info(f"User: {user_input}")
                await run_turn(app, user_input, config)
 
    except FatalError as e:
        logger.exception(f"api key error: {e}")
        raise
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
        