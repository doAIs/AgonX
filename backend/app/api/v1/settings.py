"""
配置路由
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.api.deps import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.model_config import ModelConfig
from app.schemas.model_config import ModelConfigCreate, ModelConfigUpdate, ModelConfigResponse
from app.schemas.common import ApiResponse
from app.core.logger import logger

router = APIRouter(prefix="/settings", tags=["配置"])

class ModelTestRequest(BaseModel):
    """模型连接测试请求"""
    provider: str  # openai, anthropic, deepseek, qwen
    api_base: str
    api_key: str
    model: str

@router.get("/models", response_model=ApiResponse[List[ModelConfigResponse]])
async def get_model_configs(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取模型配置列表"""
    query = select(ModelConfig).where(ModelConfig.user_id == current_user.id)
    result = await db.execute(query)
    models = result.scalars().all()
    return ApiResponse(data=[ModelConfigResponse.model_validate(m) for m in models])

@router.post("/models", response_model=ApiResponse[ModelConfigResponse])
async def create_model_config(
    config: ModelConfigCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建模型配置"""
    # 如果设置为默认，先取消其他同类型的默认模型
    if hasattr(config, 'is_default') and config.is_default:
        await db.execute(
            update(ModelConfig)
            .where(ModelConfig.user_id == current_user.id)
            .where(ModelConfig.model_type == config.model_type)
            .values(is_default=False)
        )
    
    model = ModelConfig(
        user_id=current_user.id,
        name=config.name,
        provider=config.provider,
        model_type=config.model_type,
        api_key=config.api_key,
        base_url=config.base_url,
        temperature=config.temperature,
        top_p=config.top_p,
        max_tokens=config.max_tokens
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    
    logger.info(f"用户 {current_user.username} 创建模型配置: {config.name}")
    return ApiResponse(data=ModelConfigResponse.model_validate(model))

@router.put("/models/{model_id}", response_model=ApiResponse[ModelConfigResponse])
async def update_model_config(
    model_id: int,
    config: ModelConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新模型配置"""
    query = select(ModelConfig).where(
        ModelConfig.id == model_id,
        ModelConfig.user_id == current_user.id
    )
    result = await db.execute(query)
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model config not found")
    
    # 更新字段
    update_data = config.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)
    
    await db.commit()
    await db.refresh(model)
    
    logger.info(f"用户 {current_user.username} 更新模型配置: {model.name}")
    return ApiResponse(data=ModelConfigResponse.model_validate(model))

@router.delete("/models/{model_id}", response_model=ApiResponse[None])
async def delete_model_config(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除模型配置"""
    query = select(ModelConfig).where(
        ModelConfig.id == model_id,
        ModelConfig.user_id == current_user.id
    )
    result = await db.execute(query)
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model config not found")
    
    await db.delete(model)
    await db.commit()
    
    logger.info(f"用户 {current_user.username} 删除模型配置: {model.name}")
    return ApiResponse(message="删除成功")

@router.post("/models/{model_id}/default", response_model=ApiResponse[ModelConfigResponse])
async def set_default_model(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """设置默认模型"""
    query = select(ModelConfig).where(
        ModelConfig.id == model_id,
        ModelConfig.user_id == current_user.id
    )
    result = await db.execute(query)
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model config not found")
    
    # 取消同类型的其他默认模型
    await db.execute(
        update(ModelConfig)
        .where(ModelConfig.user_id == current_user.id)
        .where(ModelConfig.model_type == model.model_type)
        .values(is_default=False)
    )
    
    # 设置当前模型为默认
    model.is_default = True
    await db.commit()
    await db.refresh(model)
    
    logger.info(f"用户 {current_user.username} 设置默认模型: {model.name}")
    return ApiResponse(data=ModelConfigResponse.model_validate(model))

@router.post("/models/test", response_model=ApiResponse[dict])
async def test_model_connection(
    test_req: ModelTestRequest,
    current_user: User = Depends(get_current_active_user)
):
    """测试模型连接"""
    logger.info(f"用户 {current_user.username} 测试模型连接: {test_req.provider}/{test_req.model}")
    
    try:
        import time
        start_time = time.time()
        
        # 根据不同 provider 调用不同 API
        if test_req.provider == 'openai':
            from openai import OpenAI
            client = OpenAI(
                api_key=test_req.api_key,
                base_url=test_req.api_base if test_req.api_base else None
            )
            # 简单测试：获取模型列表或发送测试请求
            response = client.chat.completions.create(
                model=test_req.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
        elif test_req.provider == 'deepseek':
            from openai import OpenAI
            client = OpenAI(
                api_key=test_req.api_key,
                base_url=test_req.api_base or "https://api.deepseek.com"
            )
            response = client.chat.completions.create(
                model=test_req.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
        elif test_req.provider == 'qwen':
            from openai import OpenAI
            client = OpenAI(
                api_key=test_req.api_key,
                base_url=test_req.api_base or "https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            response = client.chat.completions.create(
                model=test_req.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
        elif test_req.provider in ['glm', 'zhipu']:
            from openai import OpenAI
            client = OpenAI(
                api_key=test_req.api_key,
                base_url=test_req.api_base or "https://open.bigmodel.cn/api/paas/v4/"
            )
            response = client.chat.completions.create(
                model=test_req.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {test_req.provider}")
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"模型连接测试成功: {test_req.model}, 延迟: {latency_ms}ms")
        return ApiResponse(data={
            "status": "success",
            "message": f"连接成功! 模型: {test_req.model}",
            "latency_ms": latency_ms,
            "provider": test_req.provider
        })
    except Exception as e:
        logger.error(f"模型连接测试失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"连接失败: {str(e)}")
