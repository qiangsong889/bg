from ha import create_ha_client    
from langchain_core.tools import tool
from datetime import datetime
import asyncio
from config import HA_CONN_TIMEOUT
import logging
# @tool
# def get_current_time() -> str:
#     """获取当前的本地日期和时间"""
#     # raise RuntimeError("时间无法获取")
#     return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

logger = logging.getLogger('bg')
async def get_tools() -> list:
    tools: list = []
    try:
        ha_tools = await get_ha_tools()
        
        tools += ha_tools
    except Exception as e:
        print(f"TOOLS LOADED FAILED: {e}")
        logger.exception(f"tools load FAILED: {e}")

    return tools

async def get_ha_tools() -> list:
    try:
        ha_client = create_ha_client()
        ha_tools = await asyncio.wait_for(ha_client.get_tools(), HA_CONN_TIMEOUT)
        logger.info('HA tools loaded SUCCESSFULLY')
        print(f"HA TOOLS LOADED SUCCESSFULLY")
        return ha_tools
    except Exception as e:
        print(f"get ha tools failed return [] {e!r}")
        logger.exception(f"get ha tools failed {e}")
        return []
    