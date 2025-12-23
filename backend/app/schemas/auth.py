"""
认证相关 Pydantic 模型
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """Token 响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token 数据模型"""
    user_id: Optional[str] = None
    username: Optional[str] = None


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名或邮箱")
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class RegisterRequest(BaseModel):
    """注册请求模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    confirm_password: str = Field(..., min_length=6, max_length=100, description="确认密码")


class RefreshTokenRequest(BaseModel):
    """刷新 token 请求模型"""
    refresh_token: str = Field(..., description="刷新令牌")

