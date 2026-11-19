from langgraph.prebuilt import ToolNode, tool_node
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage, AIMessageChunk
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.runtime import Runtime
from langgraph.types import Command, interrupt
from memory import get_user_memory

import logging

logger = logging.getLogger('bg')

async def _tool_call_wrap(request: tool_node.ToolCallRequest, execute) -> ToolMessage | Command:
    # if request.tool_call.name == 
    # 调用前：request.tool_call 里有 name / args / id
    result = await execute(request)   # 真正执行工具
    # 调用后：result 就是那条 ToolMessage
    logger.info(f"[工具结果]: {result.status} {result.name} {result.text} {result.tool_call_id}")
    return result

def _route(state: MessagesState) -> str:
    if state["messages"][-1].tool_calls:
        return "tools_node"
    return END
    
def _generate_agent(tools, prompts, model):
    model_with_tools = model.bind_tools(tools)
    async def agent(state: MessagesState, runtime: Runtime) -> dict:
        memory = await get_user_memory(runtime)
        ans = await model_with_tools.ainvoke([SystemMessage(content=prompts), *memory] + [*state["messages"]])    
        for call in ans.tool_calls:
            # print(f"[调用工具] {call}")
            logger.info(f"[调用工具]: {call['name']} [参数]: {call['args']} [id]: {call['id']}")
        if ans.text:
            logger.info(f"Agent: {ans.text}")
        return { "messages": [ans] } 
    return agent

def _on_tool_error(e: Exception) -> str:
    logger.error(f"[工具执行失败]: {e}", exc_info=e)
    return f"工具执行失败: {e}"

def build_app(tools, prompts, model, checkpointer, store=None):
    agent_node = _generate_agent(tools, prompts, model)
    graph = StateGraph(MessagesState)
    graph.add_node("agent_node", agent_node)
    graph.add_node('tools_node', ToolNode(tools, handle_tool_errors=_on_tool_error, awrap_tool_call=_tool_call_wrap))

    graph.set_entry_point("agent_node")
    graph.add_conditional_edges("agent_node", _route, {
        "tools_node": "tools_node",
        END: END
    })
    graph.add_edge('tools_node', 'agent_node')

    return graph.compile(checkpointer=checkpointer, store=store)


