"""
MCP 服务端 - 管理和提供工具服务
"""
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.mcp.base import tool_registry, MCPTool


class ToolExecuteRequest(BaseModel):
    """工具执行请求"""
    tool_name: str
    arguments: Dict[str, Any]


class ToolExecuteResponse(BaseModel):
    """工具执行响应"""
    success: bool
    tool: str
    result: Any = None
    error: str = None


class MCPServer:
    """MCP服务端"""
    
    def __init__(self):
        self.registry = tool_registry
        self.router = APIRouter(prefix="/mcp", tags=["MCP工具"])
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.router.get("/tools")
        async def list_tools():
            """列出所有可用工具"""
            tools = self.registry.list_tools()
            return {
                "count": len(tools),
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "schema": tool.get_schema().dict()
                    }
                    for tool in tools
                ]
            }
        
        @self.router.get("/tools/{tool_name}")
        async def get_tool_schema(tool_name: str):
            """获取工具Schema"""
            tool = self.registry.get_tool(tool_name)
            if tool is None:
                raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
            return {
                "name": tool.name,
                "description": tool.description,
                "schema": tool.get_schema().dict(),
                "openai_function": tool.to_openai_function()
            }
        
        @self.router.post("/execute", response_model=ToolExecuteResponse)
        async def execute_tool(request: ToolExecuteRequest):
            """执行工具"""
            try:
                result = await self.registry.execute(request.tool_name, **request.arguments)
                return ToolExecuteResponse(
                    success=True,
                    tool=request.tool_name,
                    result=result
                )
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                return ToolExecuteResponse(
                    success=False,
                    tool=request.tool_name,
                    error=str(e)
                )
    
    def register_tool(self, tool: MCPTool) -> None:
        """注册工具"""
        self.registry.register(tool)
    
    def get_router(self) -> APIRouter:
        """获取路由器"""
        return self.router


# 全局MCP服务器实例
mcp_server = MCPServer()
