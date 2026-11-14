from langchain_mcp_adapters.client import MultiServerMCPClient
import os
from dotenv import load_dotenv

load_dotenv()

ha_client = MultiServerMCPClient({
    "ha": {
        "transport": "streamable_http",
        "url": f"{os.environ['HA_URL']}/api/mcp",
        "headers": {
            "Authorization": f"Bearer {os.environ['HA_TOKEN']}"
        },
    }
})
