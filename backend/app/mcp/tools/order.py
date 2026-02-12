"""
MCP 工具集合 - 订单查询
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random

from backend.app.mcp.base import MCPTool, MCPToolParameter


class OrderQueryTool(MCPTool):
    """订单查询工具"""
    
    @property
    def name(self) -> str:
        return "query_order"
    
    @property
    def description(self) -> str:
        return "查询用户订单信息，支持按订单号、状态、时间范围等条件查询"
    
    @property
    def parameters(self) -> List[MCPToolParameter]:
        return [
            MCPToolParameter(
                name="order_id",
                type="string",
                description="订单号（可选）",
                required=False
            ),
            MCPToolParameter(
                name="user_id",
                type="string",
                description="用户ID（可选）",
                required=False
            ),
            MCPToolParameter(
                name="status",
                type="string",
                description="订单状态：pending(待支付)、paid(已支付)、shipped(已发货)、completed(已完成)、cancelled(已取消)",
                required=False
            ),
            MCPToolParameter(
                name="limit",
                type="number",
                description="返回结果数量限制",
                required=False,
                default=10
            )
        ]
    
    async def execute(
        self,
        order_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        执行订单查询
        
        注意：这是示例实现，使用模拟数据
        实际部署时应连接真实数据库
        """
        
        # 如果指定了订单号，返回单个订单详情
        if order_id:
            return self._get_order_detail(order_id)
        
        # 否则返回订单列表
        return self._get_order_list(user_id, status, limit)
    
    def _get_order_detail(self, order_id: str) -> Dict[str, Any]:
        """获取订单详情（模拟）"""
        # 模拟订单数据
        statuses = ["pending", "paid", "shipped", "completed", "cancelled"]
        products = [
            "AgonX Pro 智能体套装",
            "知识库扩展包",
            "API 调用额度包",
            "企业版授权"
        ]
        
        return {
            "order_id": order_id,
            "user_id": f"user_{random.randint(1000, 9999)}",
            "product": random.choice(products),
            "quantity": random.randint(1, 5),
            "total_amount": random.randint(100, 10000),
            "status": random.choice(statuses),
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "shipping_address": "广东省深圳市南山区科技园",
            "source": "模拟数据"
        }
    
    def _get_order_list(
        self,
        user_id: Optional[str],
        status: Optional[str],
        limit: int
    ) -> Dict[str, Any]:
        """获取订单列表（模拟）"""
        orders = []
        statuses = ["pending", "paid", "shipped", "completed", "cancelled"]
        products = [
            "AgonX Pro 智能体套装",
            "知识库扩展包",
            "API 调用额度包",
            "企业版授权"
        ]
        
        for i in range(min(limit, 20)):
            order_status = status if status else random.choice(statuses)
            orders.append({
                "order_id": f"ORD{random.randint(100000, 999999)}",
                "user_id": user_id if user_id else f"user_{random.randint(1000, 9999)}",
                "product": random.choice(products),
                "quantity": random.randint(1, 5),
                "total_amount": random.randint(100, 10000),
                "status": order_status,
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return {
            "total": len(orders),
            "orders": orders,
            "source": "模拟数据"
        }


class OrderStatisticsTool(MCPTool):
    """订单统计工具"""
    
    @property
    def name(self) -> str:
        return "order_statistics"
    
    @property
    def description(self) -> str:
        return "统计订单数据，包括总订单数、总金额、各状态订单数等"
    
    @property
    def parameters(self) -> List[MCPToolParameter]:
        return [
            MCPToolParameter(
                name="user_id",
                type="string",
                description="用户ID（可选，不指定则统计所有用户）",
                required=False
            ),
            MCPToolParameter(
                name="start_date",
                type="string",
                description="开始日期，格式：YYYY-MM-DD",
                required=False
            ),
            MCPToolParameter(
                name="end_date",
                type="string",
                description="结束日期，格式：YYYY-MM-DD",
                required=False
            )
        ]
    
    async def execute(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """执行订单统计（模拟）"""
        
        # 模拟统计数据
        total_orders = random.randint(100, 1000)
        
        return {
            "user_id": user_id or "all",
            "period": f"{start_date or '2024-01-01'} 至 {end_date or datetime.now().strftime('%Y-%m-%d')}",
            "total_orders": total_orders,
            "total_amount": random.randint(10000, 100000),
            "status_breakdown": {
                "pending": random.randint(0, total_orders // 5),
                "paid": random.randint(0, total_orders // 4),
                "shipped": random.randint(0, total_orders // 4),
                "completed": random.randint(total_orders // 2, total_orders),
                "cancelled": random.randint(0, total_orders // 10)
            },
            "average_order_value": random.randint(100, 1000),
            "source": "模拟数据"
        }
