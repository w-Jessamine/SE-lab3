"""用户认证路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.user import User
from app.schemas.user import UserLogin, UserResponse

router = APIRouter(prefix="/api", tags=["认证"])


@router.post("/login", response_model=UserResponse)
def login(dto: UserLogin, db: Session = Depends(get_db)):
    """
    假登录接口
    逻辑：
      - 若 username 存在则返回用户信息
      - 若不存在则创建新用户（is_admin=False）
    返回：UserResponse
    """
    # 查询用户
    user = db.query(User).filter(User.username == dto.username).first()
    
    # 若不存在则创建
    if not user:
        user = User(username=dto.username, is_admin=False)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return UserResponse.model_validate(user)

