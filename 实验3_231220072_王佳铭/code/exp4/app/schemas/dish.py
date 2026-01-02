"""菜品相关 DTO"""
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class CategoryResponse(BaseModel):
    """分类响应"""
    category_id: int
    name: str
    sort_order: int
    
    class Config:
        """Pydantic 配置"""
        from_attributes = True


class DishResponse(BaseModel):
    """菜品响应"""
    dish_id: int
    name: str
    price: Decimal
    image_url: str
    stock: int
    status: str
    
    class Config:
        """Pydantic 配置"""
        from_attributes = True


class DishCreate(BaseModel):
    """创建/编辑菜品（管理员）"""
    category_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=100)
    price: Decimal = Field(..., gt=0)
    image_url: str = ""
    stock: int = Field(default=0, ge=0)
    status: str = Field(default="OnShelf", pattern="^(OnShelf|OffShelf)$")


class DishUpdate(BaseModel):
    """更新菜品"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[Decimal] = Field(None, gt=0)
    image_url: Optional[str] = None
    stock: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern="^(OnShelf|OffShelf)$")

