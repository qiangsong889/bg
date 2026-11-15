from langchain_mcp_adapters.client import MultiServerMCPClient
import os
import logging

logger = logging.getLogger('bg')
def create_ha_client() -> MultiServerMCPClient:
    try:
        ha_client = MultiServerMCPClient({
            "ha": {
                "transport": "streamable_http",
                "url": f"{os.environ['HA_URL']}/api/mcp",
                "headers": {
                    "Authorization": f"Bearer {os.environ['HA_TOKEN']}"
                },
            }
        })
    except Exception as e:
        logger.exception(f"create ha client error: {e}")
        print(f"create ha client error: {e}")
        raise
    return ha_client