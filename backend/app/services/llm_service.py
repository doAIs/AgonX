"""
LLM 服务
支持多个模型提供商: OpenAI, Qwen, DeepSeek, GLM
"""
from typing import Optional, AsyncGenerator, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from app.core.config import settings


class LLMService:
    """LLM服务封装"""
    
    # 不同提供商的默认配置
    PROVIDER_CONFIGS = {
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "default_model": "gpt-4"
        },
        "qwen": {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "default_model": "qwen-max"
        },
        "deepseek": {
            "base_url": "https://api.deepseek.com",
            "default_model": "deepseek-chat"
        },
        "glm": {
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "default_model": "glm-4"
        }
    }
    
    def __init__(
        self,
        provider: str = None,
        model: str = None,
        api_key: str = None,
        base_url: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        self.provider = provider or settings.DEFAULT_LLM_PROVIDER
        self.model = model or settings.DEFAULT_LLM_MODEL
        self.api_key = api_key or settings.DEFAULT_LLM_API_KEY
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # 获取base_url
        if base_url:
            self.base_url = base_url
        elif self.provider in self.PROVIDER_CONFIGS:
            self.base_url = self.PROVIDER_CONFIGS[self.provider]["base_url"]
        else:
            self.base_url = settings.DEFAULT_LLM_BASE_URL
        
        # 初始化LLM客户端
        self.llm = self._create_llm()
    
    def _create_llm(self) -> ChatOpenAI:
        """创建LLM客户端"""
        return ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
    
    async def chat(
        self,
        message: str,
        system_prompt: str = None,
        history: list = None
    ) -> str:
        """
        聊天接口
        
        Args:
            message: 用户消息
            system_prompt: 系统提示词
            history: 对话历史
        
        Returns:
            AI回复内容
        """
        messages = []
        
        # 添加系统提示
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        # 添加历史消息
        if history:
            for msg in history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # 添加当前消息
        messages.append(HumanMessage(content=message))
        
        # 调用LLM
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def chat_stream(
        self,
        message: str,
        system_prompt: str = None,
        history: list = None
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天接口
        
        Args:
            message: 用户消息
            system_prompt: 系统提示词
            history: 对话历史
        
        Yields:
            AI回复内容片段
        """
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        if history:
            for msg in history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=message))
        
        # 流式调用
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                yield chunk.content
    
    async def analyze(
        self,
        query: str,
        context: list,
        system_prompt: str = None
    ) -> str:
        """
        分析接口 - 用于智能体分析任务
        
        Args:
            query: 用户问题
            context: 检索到的上下文
            system_prompt: 系统提示词
        
        Returns:
            分析结果
        """
        default_prompt = """你是一个专业的信息分析专家。请根据提供的上下文信息，对用户问题进行深入分析。

要求：
1. 理解用户问题的核心意图
2. 从上下文中提取关键信息
3. 进行逻辑推理和综合分析
4. 给出清晰、结构化的分析结果

请用中文回答。"""
        
        prompt = system_prompt or default_prompt
        
        context_text = "\n\n".join([f"[来源{i+1}] {c}" for i, c in enumerate(context)])
        
        message = f"""用户问题: {query}

参考上下文:
{context_text}

请进行分析:"""
        
        return await self.chat(message, system_prompt=prompt)
    
    async def generate_response(
        self,
        query: str,
        context: list,
        analysis: str,
        system_prompt: str = None
    ) -> str:
        """
        生成最终回答
        
        Args:
            query: 用户问题
            context: 检索到的上下文
            analysis: 分析结果
            system_prompt: 系统提示词
        
        Returns:
            最终回答
        """
        default_prompt = """你是AgonX多智能体协作平台的响应专家。请根据分析结果，生成一个高质量、用户友好的回答。

要求：
1. 回答要准确、完整
2. 使用清晰的结构和格式
3. 适当使用Markdown格式
4. 语气友好专业

请用中文回答。"""
        
        prompt = system_prompt or default_prompt
        
        message = f"""用户问题: {query}

分析结果:
{analysis}

请生成最终回答:"""
        
        return await self.chat(message, system_prompt=prompt)
    
    @staticmethod
    async def test_connection(
        provider: str,
        api_key: str,
        base_url: str = None,
        model: str = None
    ) -> Dict[str, Any]:
        """
        测试模型连接
        
        Returns:
            {"success": bool, "message": str}
        """
        try:
            service = LLMService(
                provider=provider,
                api_key=api_key,
                base_url=base_url,
                model=model or LLMService.PROVIDER_CONFIGS.get(provider, {}).get("default_model", "gpt-3.5-turbo")
            )
            
            response = await service.chat("Say 'Connection successful!' in one sentence.")
            
            return {
                "success": True,
                "message": f"连接成功: {response[:50]}..."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"连接失败: {str(e)}"
            }
