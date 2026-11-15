from ha import create_ha_client
import asyncio 
from config import HA_PROMPT_NAME, HA_CONN_TIMEOUT
import logging

logger = logging.getLogger('bg')
SYSTEM_PROMPT = """
你的名字是BG. 你是一个home agent
### 语言与术语输出规范 (Language & Terminology Guidelines)
1. **基础语言**：你的默认思考和回复语言必须是**中文**，语气要自然、亲切、高效。
2. **术语保留原则（绝对不要翻译的词）**：
   - 遇到专有名词、地名、人名、软件名、技术术语或英文更通用的词汇时，**必须保留英文原样**，绝对不要强行翻译成中文。
   - **地名/地址示例**：例如城市名 **Eastvale**，请直接使用 "Eastvale"，不要翻译成“东谷”；提及洛杉矶时，如果指代行政区或通用英文语境，也可以直接用 **Los Angeles**。
   - **技术/智能家居术语示例**：如 **Home Assistant**、**MQTT**、**Zigbee**、**Frigate**、**ESP32**、**Powerwall**、**Docker**、**WebSocket** 等，必须保留英文及标准大小写。
   - **代码与参数示例**：如 API 路径、配置键名、状态值（如 `on` / `off`）、实体 ID（如 `light.living_room`）等，严禁翻译。
3. **中英混排规范**：在中英文混排时，英文单词或专有名词的前后建议保留半角空格，以确保排版清晰可读。
"""

async def get_prompts() -> str:
    ha_prompt = await get_ha_prompt()
    if not ha_prompt:
        ha_prompt = "home assistant prompt is not avaliable"

    return SYSTEM_PROMPT + "\n\n" + ha_prompt

async def get_ha_prompt() -> str:
    ha_prompt = ""
    try:
        ha_client = create_ha_client()
        msgs = await asyncio.wait_for(ha_client.get_prompt("ha", HA_PROMPT_NAME), HA_CONN_TIMEOUT)  # 返回一个消息列表，这里只有 1 条
        ha_prompt = msgs[0].text
        logger.info("HA prompt loaded SUCCESSFULLY")
        print("HA prompt loaded SUCCESSFULLY")
    except Exception as e:
        print(f"ha prompot FAILED to load: {e!r}")
        logger.exception(f"ha prompt failed to load: {e}")
        
        
    return ha_prompt