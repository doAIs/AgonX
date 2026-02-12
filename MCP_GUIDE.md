# MCP (Model Context Protocol) 工具使用指南

## 概述

AgonX 已经集成了完整的 MCP 工具系统，允许智能体调用外部工具来获取实时数据和执行特定任务。

## 架构设计

```
┌─────────────────┐
│   前端界面      │  - 工具管理页面
│   (Tools.vue)   │  - 测试工具功能
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   MCP Server    │  - 提供REST API
│   (FastAPI)     │  - 工具注册管理
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Tool Registry  │  - 工具注册器
│  (单例模式)     │  - 工具调度
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  具体工具实现                        │
│  - WeatherTool (天气查询)           │
│  - OrderQueryTool (订单查询)        │
│  - OrderStatisticsTool (订单统计)   │
└─────────────────────────────────────┘
```

## 已实现的工具

### 1. 天气查询工具 (get_weather)

**功能**: 查询指定城市的实时天气信息

**参数**:
- `city` (string, 必需): 城市名称，如"北京"、"上海"
- `unit` (string, 可选): 温度单位，`celsius` 或 `fahrenheit`，默认 `celsius`

**示例调用**:
```python
from backend.app.mcp.client import MCPClient

client = MCPClient()
result = await client.call_tool("get_weather", {
    "city": "北京",
    "unit": "celsius"
})
```

**返回示例**:
```json
{
  "success": true,
  "tool": "get_weather",
  "result": {
    "city": "北京",
    "temperature": "15.0°C",
    "humidity": "45%",
    "wind_speed": "12 km/h",
    "condition": "晴",
    "update_time": "2026-02-03 10:30:00",
    "source": "模拟数据"
  }
}
```

### 2. 订单查询工具 (query_order)

**功能**: 查询用户订单信息

**参数**:
- `order_id` (string, 可选): 订单号
- `user_id` (string, 可选): 用户ID
- `status` (string, 可选): 订单状态 (pending/paid/shipped/completed/cancelled)
- `limit` (number, 可选): 返回结果数量，默认10

**示例调用**:
```python
result = await client.call_tool("query_order", {
    "user_id": "user_1234",
    "status": "paid",
    "limit": 5
})
```

### 3. 订单统计工具 (order_statistics)

**功能**: 统计订单数据

**参数**:
- `user_id` (string, 可选): 用户ID
- `start_date` (string, 可选): 开始日期 (YYYY-MM-DD)
- `end_date` (string, 可选): 结束日期 (YYYY-MM-DD)

## 如何添加新工具

### 步骤1: 创建工具类

在 `backend/app/mcp/tools/` 目录下创建新文件，继承 `MCPTool` 基类：

```python
from backend.app.mcp.base import MCPTool, MCPToolParameter
from typing import Dict, Any, List

class MyCustomTool(MCPTool):
    """自定义工具"""
    
    @property
    def name(self) -> str:
        return "my_custom_tool"
    
    @property
    def description(self) -> str:
        return "这是一个自定义工具的描述"
    
    @property
    def parameters(self) -> List[MCPToolParameter]:
        return [
            MCPToolParameter(
                name="param1",
                type="string",
                description="参数1的描述",
                required=True
            )
        ]
    
    async def execute(self, param1: str) -> Dict[str, Any]:
        """执行工具逻辑"""
        # 实现你的业务逻辑
        return {
            "result": f"处理了参数: {param1}"
        }
```

### 步骤2: 注册工具

在 `backend/main.py` 的 `lifespan` 函数中注册：

```python
from backend.app.mcp.tools.my_custom import MyCustomTool

mcp_server.register_tool(MyCustomTool())
```

### 步骤3: 在智能体中使用

工具会自动在 `researcher_node` 中通过关键词匹配调用，或者手动调用：

```python
from backend.app.mcp.client import MCPClient

mcp_client = MCPClient()
result = await mcp_client.call_tool("my_custom_tool", {"param1": "tests"})
```

## API 端点

### 1. 列出所有工具
```
GET /mcp/tools
```

### 2. 获取工具详情
```
GET /mcp/tools/{tool_name}
```

### 3. 执行工具
```
POST /mcp/execute
Content-Type: application/json

{
  "tool_name": "get_weather",
  "arguments": {
    "city": "北京"
  }
}
```

## 前端使用

访问 **工具管理** 页面（`/tools`）可以：
- 查看所有可用工具
- 查看工具参数和描述
- 在线测试工具执行

## 与智能体的集成

在 `app/agents/orchestrator.py` 中，`researcher_node` 会自动检测用户查询中的关键词并调用相应工具：

- 包含"天气"、"温度" → 调用 `get_weather`
- 包含"订单" → 调用 `query_order`

工具执行结果会自动添加到上下文中，供后续智能体使用。

## 生产环境部署建议

1. **真实API接入**: 将模拟数据替换为真实API调用（如高德天气API）
2. **权限控制**: 添加工具调用的权限验证
3. **调用限流**: 防止恶意调用和资源滥用
4. **错误处理**: 完善异常捕获和重试机制
5. **日志记录**: 记录所有工具调用以便审计

## 扩展方向

- 数据库查询工具
- 邮件发送工具
- 文件操作工具
- 第三方API集成（支付、物流等）
- 自定义计算工具
