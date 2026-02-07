import os
import time
import sys
from contextlib import asynccontextmanager

# 设置系统时区为东八区 (北京时间)
os.environ['TZ'] = 'Asia/Shanghai'
if sys.platform != 'win32':
    time.tzset()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.logger import logger
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("=" * 60)
    logger.info(f"应用启动: {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 60)
    
    try:
        logger.info("初始化数据库连接...")
        await init_db()
        logger.info("数据库连接初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise
    
    # 注册MCP工具
    try:
        from app.mcp.server import mcp_server
        from app.mcp.tools import WeatherTool, OrderQueryTool, OrderStatisticsTool
        
        logger.info("注册MCP工具...")
        mcp_server.register_tool(WeatherTool())
        mcp_server.register_tool(OrderQueryTool())
        mcp_server.register_tool(OrderStatisticsTool())
        logger.info("MCP工具注册完成")
    except Exception as e:
        logger.warning(f"MCP工具注册失败: {str(e)}")
    
    logger.info(f"应用启动完成, API前缀: {settings.API_V1_PREFIX}")
    
    yield
    
    # 关闭时
    logger.info("应用关闭中...")
    await close_db()
    logger.info("应用已关闭")


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="多智能体协作平台 API",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan
    )
    
    # 配置CORS - 支持多个前端端口
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "*"  # 开发环境允许所有源
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]
    )
    
    # 添加请求日志中间件
    @app.middleware("http")
    async def log_requests(request, call_next):
        from app.core.logger import logger
        import time
        
        start_time = time.time()
        logger.info(f"[请求] {request.method} {request.url.path} - 来自: {request.client.host}")
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            logger.info(f"[响应] {request.method} {request.url.path} - 状态: {response.status_code} - 耗时: {process_time:.3f}s")
            return response
        except Exception as e:
            logger.error(f"[请求异常] {request.method} {request.url.path} - 错误: {str(e)}")
            raise
    
    # 注册路由
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    
    # 注册MCP路由
    from app.mcp.server import mcp_server
    app.include_router(mcp_server.get_router())
    
    # 健康检查
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": settings.APP_VERSION}
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,  # 本地开发使用8080端口，与Docker环境8000端口区分
        reload=settings.DEBUG
    )
