"""
短期记忆服务
基于 Redis 实现会话级别的上下文记忆
"""
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import redis.asyncio as redis

from app.core.config import settings


class ShortTermMemory:
    """短期记忆 - 基于Redis"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.ttl = settings.SHORT_TERM_MEMORY_TTL
        self.max_messages = settings.SHORT_TERM_MEMORY_MAX_MESSAGES
    
    async def connect(self):
        """连接Redis"""
        if not self.redis_client:
            self.redis_client = redis.from_url(settings.REDIS_URL)
    
    async def close(self):
        """关闭连接"""
        if self.redis_client:
            await self.redis_client.close()
    
    def _get_key(self, session_id: str) -> str:
        """获取Redis键"""
        return f"agonx:memory:short:{session_id}"
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Dict[str, Any] = None
    ):
        """
        添加消息到短期记忆
        
        Args:
            session_id: 会话ID
            role: 消息角色 (user/assistant)
            content: 消息内容
            metadata: 额外元数据
        """
        await self.connect()
        
        key = self._get_key(session_id)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        # 添加到列表末尾
        await self.redis_client.rpush(key, json.dumps(message, ensure_ascii=False))
        
        # 保持最近N条消息
        await self.redis_client.ltrim(key, -self.max_messages, -1)
        
        # 设置过期时间
        await self.redis_client.expire(key, self.ttl)
    
    async def get_context(
        self,
        session_id: str,
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """
        获取会话上下文
        
        Args:
            session_id: 会话ID
            limit: 返回消息数量限制
        
        Returns:
            消息列表
        """
        await self.connect()
        
        key = self._get_key(session_id)
        limit = limit or self.max_messages
        
        # 获取最近的消息
        messages = await self.redis_client.lrange(key, -limit, -1)
        
        return [json.loads(msg) for msg in messages]
    
    async def clear(self, session_id: str):
        """清除会话记忆"""
        await self.connect()
        key = self._get_key(session_id)
        await self.redis_client.delete(key)
    
    async def get_all_sessions(self, user_id: int) -> List[str]:
        """获取用户的所有会话ID"""
        await self.connect()
        
        pattern = f"agonx:memory:short:*"
        keys = await self.redis_client.keys(pattern)
        
        return [key.decode().split(":")[-1] for key in keys]


class LongTermMemory:
    """长期记忆 - 基于Milvus向量检索"""
    
    def __init__(self):
        self.collection_name = "agonx_long_term_memory"
    
    async def store(
        self,
        user_id: int,
        content: str,
        importance: float = 0.5,
        category: str = None
    ) -> str:
        """
        存储长期记忆
        
        Args:
            user_id: 用户ID
            content: 记忆内容
            importance: 重要度 (0-1)
            category: 分类
        
        Returns:
            记忆ID
        """
        # TODO: 实现Milvus存储
        # 1. 向量化内容
        # 2. 存储到Milvus
        # 3. 存储元数据到MySQL
        
        import uuid
        return str(uuid.uuid4())
    
    async def search(
        self,
        query: str,
        user_id: int,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        搜索相关记忆
        
        Args:
            query: 查询内容
            user_id: 用户ID
            top_k: 返回数量
            threshold: 相似度阈值
        
        Returns:
            相关记忆列表
        """
        # TODO: 实现Milvus检索
        # 1. 向量化查询
        # 2. 在Milvus中搜索
        # 3. 按相似度排序返回
        
        return []
    
    async def update(
        self,
        memory_id: str,
        content: str = None,
        importance: float = None
    ):
        """更新记忆"""
        # TODO: 实现更新逻辑
        pass
    
    async def delete(self, memory_id: str):
        """删除记忆"""
        # TODO: 实现删除逻辑
        pass


class MemoryManager:
    """记忆管理器 - 统一管理短期和长期记忆"""
    
    def __init__(self):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()
    
    async def recall(
        self,
        query: str,
        session_id: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        召回相关记忆
        
        Args:
            query: 查询内容
            session_id: 会话ID
            user_id: 用户ID
        
        Returns:
            {
                "short_term": [...],  # 短期记忆(会话上下文)
                "long_term": [...]    # 长期记忆(相关历史)
            }
        """
        # 获取短期记忆
        short_term_context = await self.short_term.get_context(session_id)
        
        # 搜索长期记忆
        long_term_memories = await self.long_term.search(query, user_id)
        
        return {
            "short_term": short_term_context,
            "long_term": long_term_memories
        }
    
    async def memorize(
        self,
        session_id: str,
        user_id: int,
        role: str,
        content: str,
        importance: float = 0.5
    ):
        """
        记忆信息
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            role: 角色
            content: 内容
            importance: 重要度
        """
        # 添加到短期记忆
        await self.short_term.add_message(session_id, role, content)
        
        # 如果重要度高，同时存储到长期记忆
        if importance >= 0.8:
            await self.long_term.store(user_id, content, importance)
    
    async def evaluate_importance(self, content: str) -> float:
        """
        评估内容的重要度
        
        Args:
            content: 内容
        
        Returns:
            重要度 (0-1)
        """
        # TODO: 使用LLM或规则评估重要度
        # 简单实现：基于长度和关键词
        
        importance = 0.5
        
        # 长内容可能更重要
        if len(content) > 500:
            importance += 0.1
        
        # 包含特定关键词
        important_keywords = ["重要", "记住", "注意", "请记住", "一定要"]
        for keyword in important_keywords:
            if keyword in content:
                importance += 0.2
                break
        
        return min(importance, 1.0)


# 全局实例
memory_manager = MemoryManager()
