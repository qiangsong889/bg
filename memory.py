from langchain_core.tools import tool
from langgraph.prebuilt import InjectedStore
from typing import Annotated
from langgraph.store.base import BaseStore
from langgraph.runtime import Runtime
from langchain_core.messages import SystemMessage
import logging

logger = logging.getLogger('bg')
MEMORY_NS = ("shayne", "memories")

@tool
async def remember(title: str, content: str, store: Annotated[BaseStore, InjectedStore()]) -> str:
    """记录或更新用户的长期信息，供后续对话使用。

    当用户明确要求记住某件事，或明确表达了值得长期保留的
    个人信息、偏好、习惯、目标时调用。

    只记录用户明确提供的信息，不根据猜测建立用户画像。
    不记录临时指令、一次性任务、密码、令牌等认证信息。
    同一类信息使用相同的 key；用户更正信息时更新原记录。

    补充同一类信息时，把已有内容和新内容合并成完整的一句再保存
    
    Args:
        title: 简短、稳定的信息类别，例如 preferred_language、occupation。
        content: 准确、简洁的用户信息，例如“用户偏好用中文交流”。
    """

    await store.aput(MEMORY_NS, title, {"content": content})
    return f"记忆已保存: {title}"
    
async def get_user_memory(runtime: Runtime) -> list[SystemMessage]:
    try:
        if runtime.store is None:
            return []
        result = await runtime.store.asearch(MEMORY_NS, limit=100)
        if not result:
            return []
        content = "记忆:\n" + "\n".join(
            f"{item.key}: {value}"
            for item in result
            for key, value in item.value.items()
        )
        return [SystemMessage(content=content)]
    except Exception as e:
        logger.exception(f"用户记忆获取失败: {e}")
        print(f"用户记忆获取失败: {e}")
        return []
