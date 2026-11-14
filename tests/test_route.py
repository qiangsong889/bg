from main import route
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage, AIMessageChunk
from tools import get_tools
import asyncio
from unittest.mock import AsyncMock, patch

def test_route_end():
    state = MessagesState({
        "messages": [AIMessage(content="Done")]
    })
    assert route(state) == END
    
def test_route_tools_node():
    state = MessagesState({
        "messages": [AIMessage(
            content="",
            tool_calls=[{ "name": "example_tool", "args": {}, "id": "123" }])]
    })
    assert route(state) == "tools_node"
    

def test_ha_failure_preserves_other_tools():
    ha_tool = object()

    with patch(
        "tools.ha_client.get_tools",
        new_callable=AsyncMock,
        return_value=[ha_tool],
    ):
        success_result = asyncio.run(get_tools())

    with patch(
        "tools.ha_client.get_tools",
        new_callable=AsyncMock,
        side_effect=RuntimeError("HA connection failed"),
    ):
        failure_result = asyncio.run(get_tools())

    assert ha_tool in success_result
    assert failure_result == [
        tool for tool in success_result if tool is not ha_tool
    ]
    
# def test_ha_get_tools_success():
#     ha_tools = [object()]
    
#     with patch(
#         "tools.ha_client.get_tools",
#         new_callable=AsyncMock,
#         return_value=ha_tools
#     ):
#         result = asyncio.run(get_tools())
#         for ha_tool in ha_tools:
#             assert ha_tool in result
            
# def test_ha_get_tool_failed():
#     with patch(
#         "tools.ha_client.get_tools",
#         new_callable=AsyncMock,
#         side_effect=RuntimeError("ha连接失败")
#     ):
#         result = asyncio.run(get_tools())
        
        