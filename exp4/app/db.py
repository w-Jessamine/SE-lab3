"""SQLAlchemy 数据库会话管理"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings

# 创建引擎
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=False  # 设为 True 可查看 SQL 日志
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM 基类
Base = declarative_base()


def get_db() -> Session:
    """
    FastAPI 依赖注入：提供数据库会话
    自动管理会话生命周期（yield 后关闭）
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    创建所有表（开发环境使用）
    生产环境应使用 Alembic 迁移
    """
    from app.models import (
        User, Category, Dish, OptionGroup, OptionItem,
        Order, OrderItem, order_item_options
    )
    Base.metadata.create_all(bind=engine)

