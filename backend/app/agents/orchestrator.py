"""
AgonX 多智能体编排器
基于 LangGraph 实现三智能体协作 + MCP工具调用
"""
from typing import TypedDict, List, Optional, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from backend.app.mcp.client import MCPClient


class AgentState(TypedDict):
    """智能体状态"""
    messages: List[Any]          # 消息历史
    query: str                   # 用户查询
    context: List[str]           # 检索到的上下文
    images: List[str]            # 相关图片URL
    research_result: str         # 研究员结果
    analysis_result: str         # 分析师结果
    final_answer: str            # 最终答案
    current_agent: str           # 当前智能体
    error: Optional[str]         # 错误信息
    tool_calls: List[Any]        # 工具调用记录
    tool_results: List[Any]      # 工具执行结果


async def researcher_node(state: AgentState) -> AgentState:
    """
    研究员智能体
    负责: 知识库检索、图片查找、MCP工具调用
    """
    state["current_agent"] = "researcher"
    
    query = state["query"]
    
    # 初始化MCP客户端
    mcp_client = MCPClient()
    
    # 检测是否需要调用工具（简单关键词匹配）
    tool_results = []
    if "天气" in query or "温度" in query:
        # 调用天气工具
        city = "北京"  # 实际应从查询中提取城市名
        result = await mcp_client.call_tool("get_weather", {"city": city})
        tool_results.append(result)
    
    if "订单" in query:
        # 调用订单查询工具
        result = await mcp_client.call_tool("query_order", {"limit": 5})
        tool_results.append(result)
    
    # TODO: 实际项目中调用知识库检索服务
    # from app.knowledge.retrieval import RetrievalService
    # retrieval_service = RetrievalService()
    # context = await retrieval_service.search(query)
    
    # 模拟检索结果
    context = [
        f"检索结果1: 关于'{query}'的相关信息...",
        f"检索结果2: 补充说明..."
    ]
    
    # 如果有工具结果，添加到上下文中
    for tool_result in tool_results:
        if tool_result["success"]:
            context.append(mcp_client.format_tool_result(tool_result))
    
    images = []  # 检索到的图片URL列表
    
    state["context"] = context
    state["images"] = images
    state["tool_results"] = tool_results
    state["research_result"] = f"已从知识库中检索到 {len(context)} 条相关信息，调用了 {len(tool_results)} 个工具"
    
    return state


async def analyzer_node(state: AgentState) -> AgentState:
    """
    分析师智能体
    负责: 信息整合、逻辑推理
    """
    state["current_agent"] = "analyzer"
    
    query = state["query"]
    context = state["context"]
    
    # TODO: 实际项目中调用LLM进行分析
    # from app.services.llm_service import LLMService
    # llm_service = LLMService()
    # analysis = await llm_service.analyze(query, context)
    
    # 模拟分析结果
    analysis = f"""
基于检索到的 {len(context)} 条信息，我对问题「{query}」进行了分析：

1. 问题理解：这是一个关于具体技术或业务的问题
2. 关键信息：从上下文中提取了关键要点
3. 逻辑推理：综合各方面信息得出结论
"""
    
    state["analysis_result"] = analysis
    
    return state


async def responder_node(state: AgentState) -> AgentState:
    """
    响应者智能体
    负责: 答案生成、格式化输出
    """
    state["current_agent"] = "responder"
    
    query = state["query"]
    context = state["context"]
    analysis = state["analysis_result"]
    images = state["images"]
    
    # TODO: 实际项目中调用LLM生成最终答案
    # from app.services.llm_service import LLMService
    # llm_service = LLMService()
    # answer = await llm_service.generate_response(query, context, analysis)
    
    # 模拟最终答案
    final_answer = f"""
## 回答

根据您的问题「{query}」，我为您整理了以下答案：

{analysis}

### 参考来源
- 知识库检索结果
- 系统分析推理

如果您需要更详细的信息，请随时告诉我。
"""
    
    state["final_answer"] = final_answer
    
    return state


def should_continue(state: AgentState) -> str:
    """判断是否继续执行"""
    if state.get("error"):
        return "error"
    return "continue"


def create_agent_workflow() -> StateGraph:
    """
    创建多智能体工作流
    
    工作流程:
    用户提问 → Researcher(检索) → Analyzer(分析) → Responder(响应) → 结束
    """
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("responder", responder_node)
    
    # 设置入口
    workflow.set_entry_point("researcher")
    
    # 添加边
    workflow.add_edge("researcher", "analyzer")
    workflow.add_edge("analyzer", "responder")
    workflow.add_edge("responder", END)
    
    return workflow.compile()


# 编译工作流
agent_workflow = create_agent_workflow()


async def run_agents(query: str, user_id: int = None) -> AgentState:
    """
    执行多智能体工作流
    
    Args:
        query: 用户查询
        user_id: 用户ID (可选，用于获取个性化记忆)
    
    Returns:
        AgentState: 包含最终答案的状态
    """
    initial_state: AgentState = {
        "messages": [],
        "query": query,
        "context": [],
        "images": [],
        "research_result": "",
        "analysis_result": "",
        "final_answer": "",
        "current_agent": "",
        "error": None
    }
    
    # 执行工作流
    final_state = await agent_workflow.ainvoke(initial_state)
    
    return final_state


async def run_agents_stream(query: str, user_id: int = None):
    """
    流式执行多智能体工作流
    
    Args:
        query: 用户查询
        user_id: 用户ID
    
    Yields:
        tuple: (agent_name, content) 每个智能体的输出
    """
    initial_state: AgentState = {
        "messages": [],
        "query": query,
        "context": [],
        "images": [],
        "research_result": "",
        "analysis_result": "",
        "final_answer": "",
        "current_agent": "",
        "error": None
    }
    
    # 流式执行
    async for event in agent_workflow.astream(initial_state):
        for node_name, state in event.items():
            if node_name == "researcher":
                yield ("researcher", state.get("research_result", ""))
            elif node_name == "analyzer":
                yield ("analyzer", state.get("analysis_result", ""))
            elif node_name == "responder":
                yield ("responder", state.get("final_answer", ""))
