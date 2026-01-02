"""订单相关 DTO"""
from decimal import Decimal
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    """创建订单项"""
    dish_id: int = Field(..., gt=0)
    qty: int = Field(..., gt=0)
    option_item_ids: List[int] = Field(default_factory=list)


class OrderCreate(BaseModel):
    """创建订单请求"""
    user_id: int = Field(..., gt=0)
    remark: Optional[str] = Field(None, max_length=500)
    items: List[OrderItemCreate] = Field(..., min_length=1)


class OrderItemResponse(BaseModel):
    """订单项响应"""
    id: int
    dish_id: int
    dish_name: str
    qty: int
    unit_price: Decimal
    subtotal: Decimal
    
    class Config:
        """Pydantic 配置"""
        from_attributes = True


class OrderResponse(BaseModel):
    """订单响应"""
    order_id: int
    user_id: int
    status: str
    total_price: Decimal
    remark: Optional[str]
    created_at: datetime
    
    class Config:
        """Pydantic 配置"""
        from_attributes = True


class OrderDetailResponse(OrderResponse):
    """订单详情响应（包含订单项）"""
    items: List[OrderItemResponse] = []

