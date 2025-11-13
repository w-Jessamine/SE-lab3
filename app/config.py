"""应用配置"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """配置类"""
    DATABASE_URL: str = "sqlite:///./order_system.db"
    
    # 如果使用MySQL，格式如下：
    # DATABASE_URL: str = "mysql+pymysql://user:pass@localhost/order_db"
    
    class Config:
        """配置元类"""
        env_file = ".env"
        case_sensitive = False


settings = Settings()

