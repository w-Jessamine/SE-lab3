"""用户相关 DTO"""
from pydantic import BaseModel


class UserLogin(BaseModel):
    """登录请求"""
    username: str


class UserResponse(BaseModel):
    """用户信息响应"""
    user_id: int
    username: str
    is_admin: bool
    
    class Config:
        """Pydantic 配置"""
        from_attributes = True

