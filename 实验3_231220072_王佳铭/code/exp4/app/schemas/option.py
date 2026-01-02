"""口味选项 DTO"""
from decimal import Decimal
from typing import List
from pydantic import BaseModel


class OptionItemResponse(BaseModel):
    """选项项响应"""
    item_id: int
    name: str
    price_delta: Decimal
    available: bool
    
    class Config:
        """Pydantic 配置"""
        from_attributes = True


class OptionGroupResponse(BaseModel):
    """选项组响应"""
    group_id: int
    name: str
    type: str
    required: bool
    max_select: int
    items: List[OptionItemResponse]
    
    class Config:
        """Pydantic 配置"""
        from_attributes = True

