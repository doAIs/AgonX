from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
import traceback

from backend.app.api.deps import get_db
from backend.app.core.security import create_access_token, get_current_active_user
from backend.app.core.logger import logger
from backend.app.services.user_service import UserService
from backend.app.schemas import UserCreate, UserLogin, UserResponse, Token, ApiResponse
from backend.app.models import User

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=ApiResponse[Token])
async def login(
    login_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    try:
        logger.info(f"[登录请求] 用户名: {login_data.username}, IP: {request.client.host}")
        
        # 验证用户
        user_service = UserService(db)
        logger.debug(f"[登录] 开始验证用户: {login_data.username}")
        
        user = await user_service.authenticate(login_data.username, login_data.password)
        
        if not user:
            logger.warning(f"[登录失败] 用户名或密码错误: {login_data.username}, IP: {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 检查用户是否激活
        if not user.is_active:
            logger.warning(f"[登录失败] 用户未激活: {login_data.username}, IP: {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户账号已被禁用"
            )
        
        # 生成Token
        logger.debug(f"[登录] 生成访问令牌: 用户ID={user.id}")
        access_token = create_access_token(data={"sub": str(user.id)})
        
        logger.info(f"[登录成功] 用户: {user.username}, ID: {user.id}, IP: {request.client.host}")
        
        return ApiResponse(
            data=Token(access_token=access_token, token_type="bearer")
        )
    
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 捕获所有未预期的异常
        logger.error(f"[登录异常] 用户名: {login_data.username}, 错误: {str(e)}")
        logger.error(f"[登录异常] 堆栈跟踪:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@router.post("/register", response_model=ApiResponse[UserResponse])
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """用户注册"""
    try:
        logger.info(f"[注册请求] 用户名: {user_data.username}, 邮箱: {user_data.email}, IP: {request.client.host}")
        
        user_service = UserService(db)
        
        # 检查用户名是否已存在
        logger.debug(f"[注册] 检查用户名: {user_data.username}")
        existing_user = await user_service.get_by_username(user_data.username)
        if existing_user:
            logger.warning(f"[注册失败] 用户名已存在: {user_data.username}, IP: {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        logger.debug(f"[注册] 检查邮箱: {user_data.email}")
        existing_email = await user_service.get_by_email(user_data.email)
        if existing_email:
            logger.warning(f"[注册失败] 邮箱已被注册: {user_data.email}, IP: {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
        
        # 创建用户
        logger.debug(f"[注册] 创建用户: {user_data.username}")
        user = await user_service.create(user_data)
        
        logger.info(f"[注册成功] 用户: {user.username}, ID: {user.id}, 邮箱: {user.email}, IP: {request.client.host}")
        
        return ApiResponse(
            message="注册成功",
            data=UserResponse.model_validate(user)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[注册异常] 用户名: {user_data.username}, 错误: {str(e)}")
        logger.error(f"[注册异常] 堆栈跟踪:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    try:
        logger.info(f"[获取用户信息] 用户: {current_user.username}, ID: {current_user.id}")
        return ApiResponse(
            data=UserResponse.model_validate(current_user)
        )
    except Exception as e:
        logger.error(f"[获取用户信息异常] 用户ID: {current_user.id}, 错误: {str(e)}")
        logger.error(f"[获取用户信息异常] 堆栈跟踪:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )


@router.post("/refresh", response_model=ApiResponse[Token])
async def refresh_token(
    current_user: User = Depends(get_current_active_user)
):
    """刷新Token"""
    try:
        logger.info(f"[刷新Token] 用户: {current_user.username}, ID: {current_user.id}")
        access_token = create_access_token(data={"sub": str(current_user.id)})
        
        return ApiResponse(
            data=Token(access_token=access_token, token_type="bearer")
        )
    except Exception as e:
        logger.error(f"[刷新Token异常] 用户ID: {current_user.id}, 错误: {str(e)}")
        logger.error(f"[刷新Token异常] 堆栈跟踪:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刷新Token失败"
        )


@router.post("/logout", response_model=ApiResponse)
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """退出登录"""
    try:
        logger.info(f"[退出登录] 用户: {current_user.username}, ID: {current_user.id}")
        # JWT无状态，客户端删除token即可
        return ApiResponse(message="退出成功")
    except Exception as e:
        logger.error(f"[退出登录异常] 用户ID: {current_user.id}, 错误: {str(e)}")
        logger.error(f"[退出登录异常] 堆栈跟踪:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="退出登录失败"
        )
