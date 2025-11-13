"""应用配置"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """配置类"""
    DATABASE_URL: str = "sqlite:///./order_system.db"
    
    # 如果使用MySQL，格式如下：
    # DATABASE_URL: str = "mysql+pymysql://user:pass@localhost/order_db"
    GEMINI_BASE_URL: str | None = None  # 例如: http://14.103.68.46
    GEMINI_API_KEY: str | None = None   # 在 .env 中填写
    
    class Config:
        """配置元类"""
        env_file = ".env"
        case_sensitive = False


settings = Settings()

