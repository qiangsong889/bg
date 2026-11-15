from tools import get_ha_tools
from prompt import get_ha_prompt
import json
from datetime import datetime
from pathlib import Path
import asyncio
from config import SNAPSHOTS_PATH


def serialize_tool(tool):
    schema = tool.tool_call_schema
    if not isinstance(schema, dict):
        schema = schema.model_json_schema()
    return {
        "name": tool.name,
        "description": tool.description,
        "args_schema": schema
    }
    
async def save_ha_snapshot():
    tools = await get_ha_tools()
    if not tools:
        raise ValueError("no tools found")
    prompt = await get_ha_prompt()
    if not prompt:
        raise ValueError("no ha prompt found")
    
    snapshot = {
        "server": "Home Assistant MCP Server",
        "created_at": datetime.now().isoformat(),
        "prompt": prompt,
        "tools": [serialize_tool(tool) for tool in tools],
    }
    ha_snapshot_path = SNAPSHOTS_PATH / "ha.json"
    
    with open(ha_snapshot_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    print(f"file successfully saved, total tools {len(snapshot['tools'])} path: {ha_snapshot_path}")
    
async def main():
    await save_ha_snapshot()
    
if __name__ == "__main__":
    asyncio.run(main())