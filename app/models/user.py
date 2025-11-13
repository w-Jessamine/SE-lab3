"""用户模型"""
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.db import Base


class User(Base):
    """
    用户实体
    支持简单登录，区分普通用户与管理员
    """
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    
    # 关系：一个用户可以创建多个订单
    orders = relationship("Order", back_populates="user")
    
    def login(self) -> bool:
        """假登录逻辑（占位）"""
        return True
    
    def logout(self) -> None:
        """登出逻辑（占位）"""
        pass

