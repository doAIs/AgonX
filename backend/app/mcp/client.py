"""
MCP 客户端 - 用于智能体调用工具
"""
from typing import Dict, Any, List, Optional
import json
from app.mcp.base import tool_registry


class MCPClient:
    """MCP客户端"""
    
    def __init__(self):
        self.registry = tool_registry
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表 (OpenAI Function格式)"""
        return self.registry.get_openai_functions()
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具"""
        try:
            result = await self.registry.execute(tool_name, **arguments)
            return {
                "success": True,
                "tool": tool_name,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e)
            }
    
    async def parse_and_call(self, function_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析LLM的function_call并执行
        
        Args:
            function_call: {"name": "tool_name", "arguments": "{...}"}
        """
        tool_name = function_call.get("name")
        arguments_str = function_call.get("arguments", "{}")
        
        # 解析JSON参数
        try:
            arguments = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
        except json.JSONDecodeError:
            return {
                "success": False,
                "tool": tool_name,
                "error": "Invalid JSON arguments"
            }
        
        return await self.call_tool(tool_name, arguments)
    
    def format_tool_result(self, result: Dict[str, Any]) -> str:
        """格式化工具结果为文本"""
        if result["success"]:
            return f"工具 {result['tool']} 执行成功:\n{json.dumps(result['result'], ensure_ascii=False, indent=2)}"
        else:
            return f"工具 {result['tool']} 执行失败: {result['error']}"
