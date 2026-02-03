from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security import create_access_token, get_current_active_user
from app.services.user_service import UserService
from app.schemas import UserCreate, UserResponse, Token, ApiResponse
from app.models import User

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=ApiResponse[Token])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    user_service = UserService(db)
    user = await user_service.authenticate(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return ApiResponse(
        data=Token(access_token=access_token, token_type="bearer")
    )


@router.post("/register", response_model=ApiResponse[UserResponse])
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """用户注册"""
    user_service = UserService(db)
    
    # 检查用户名是否已存在
    existing_user = await user_service.get_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    existing_email = await user_service.get_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    user = await user_service.create(user_data)
    
    return ApiResponse(
        message="注册成功",
        data=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    return ApiResponse(
        data=UserResponse.model_validate(current_user)
    )


@router.post("/refresh", response_model=ApiResponse[Token])
async def refresh_token(
    current_user: User = Depends(get_current_active_user)
):
    """刷新Token"""
    access_token = create_access_token(data={"sub": str(current_user.id)})
    
    return ApiResponse(
        data=Token(access_token=access_token, token_type="bearer")
    )


@router.post("/logout", response_model=ApiResponse)
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """退出登录"""
    # JWT无状态，客户端删除token即可
    return ApiResponse(message="退出成功")
