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
    
