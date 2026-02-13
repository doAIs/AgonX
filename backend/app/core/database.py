from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# 异步引擎
async_engine = create_async_engine(
    settings.MYSQL_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={
        "init_command": "SET time_zone='+08:00'"
    }
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# 同步引擎 (用于Alembic迁移)
sync_engine = create_engine(
    settings.MYSQL_URL_SYNC,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    connect_args={
        "init_command": "SET time_zone='+08:00'"
    }
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类"""
    pass


async def get_async_session() -> AsyncSession:
    """获取异步数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库
    
    确保所有模型被加载后再创建表
    """
    # 导入所有模型确保它们被注册到Base.metadata
    from app.models import (
        User, ChatSession, ChatMessage,
        KnowledgeBase, Document, LongTermMemory, ModelConfig,
        DocumentPage, DocumentElement, DocumentChunk, OCRTask
    )
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接"""
    await async_engine.dispose()
