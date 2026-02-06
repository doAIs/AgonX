"""
MCP 工具基础类和注册器
"""
from typing import Dict, Any, List, Callable, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field


class MCPToolParameter(BaseModel):
    """工具参数定义"""
    name: str
    type: str  # string, number, boolean, object, array
    description: str
    required: bool = True
    default: Optional[Any] = None


class MCPToolSchema(BaseModel):
    """工具Schema定义"""
    name: str
    description: str
    parameters: List[MCPToolParameter]
    
    def to_openai_function(self) -> Dict[str, Any]:
        """转换为OpenAI Function Calling格式"""
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description
            }
            if param.default is not None:
                properties[param.name]["default"] = param.default
            if param.required:
                required.append(param.name)
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }


class MCPTool(ABC):
    """MCP工具基类"""
    
    def __init__(self):
        self._schema: Optional[MCPToolSchema] = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> List[MCPToolParameter]:
        """工具参数定义"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具"""
        pass
    
    def get_schema(self) -> MCPToolSchema:
        """获取工具Schema"""
        if self._schema is None:
            self._schema = MCPToolSchema(
                name=self.name,
                description=self.description,
                parameters=self.parameters
            )
        return self._schema
    
    def to_openai_function(self) -> Dict[str, Any]:
        """转换为OpenAI Function格式"""
        return self.get_schema().to_openai_function()


class MCPToolRegistry:
    """MCP工具注册器"""
    
    _instance = None
    _tools: Dict[str, MCPTool] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, tool: MCPTool) -> None:
        """注册工具"""
        self._tools[tool.name] = tool
    
    def unregister(self, tool_name: str) -> None:
        """注销工具"""
        if tool_name in self._tools:
            del self._tools[tool_name]
    
    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """获取工具"""
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[MCPTool]:
        """列出所有工具"""
        return list(self._tools.values())
    
    def get_openai_functions(self) -> List[Dict[str, Any]]:
        """获取所有工具的OpenAI Function格式"""
        return [tool.to_openai_function() for tool in self._tools.values()]
    
    async def execute(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """执行工具"""
        tool = self.get_tool(tool_name)
        if tool is None:
            raise ValueError(f"Tool {tool_name} not found")
        return await tool.execute(**kwargs)


# 全局工具注册器实例
tool_registry = MCPToolRegistry()
