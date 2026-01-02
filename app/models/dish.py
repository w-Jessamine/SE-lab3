"""菜品相关模型"""
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, Enum as SQLEnum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base
from app.models.enums import DishStatus, OptionType


class Category(Base):
    """
    菜品分类
    示例：特色、肉类、素菜、酒水、主食
    """
    __tablename__ = "categories"
    
    category_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    sort_order = Column(Integer, default=0)  # 排序权重
    
    # 关系：一个分类包含多个菜品
    dishes = relationship("Dish", back_populates="category")
    
    def get_dishes(self):
        """获取该分类下所有菜品"""
        return self.dishes


class Dish(Base):
    """
    菜品实体
    包含库存管理与上下架状态
    """
    __tablename__ = "dishes"
    
    dish_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    name = Column(String(100), nullable=False, index=True)
    price = Column(Numeric(10, 2), nullable=False)  # 价格（精确到分）
    image_url = Column(String(500), default="")
    stock = Column(Integer, default=0)  # 库存数量
    status = Column(SQLEnum(DishStatus), default=DishStatus.ON_SHELF, nullable=False)
    
    # 关系
    category = relationship("Category", back_populates="dishes")
    option_groups = relationship("OptionGroup", back_populates="dish", cascade="all, delete-orphan")
    
    def is_available(self) -> bool:
        """
        判断菜品是否可下单
        契约：status == OnShelf AND stock > 0
        """
        return self.status == DishStatus.ON_SHELF and self.stock > 0
    
    def update_stock(self, delta: int) -> None:
        """
        调整库存
        参数：delta 可正可负
        前置条件：self.stock + delta >= 0
        异常：若调整后 < 0 则抛出 ValueError
        """
        new_stock = self.stock + delta
        if new_stock < 0:
            raise ValueError(f"库存不足：当前 {self.stock}，尝试调整 {delta}")
        self.stock = new_stock


class OptionGroup(Base):
    """
    口味/加料选项组
    示例：辣度（单选）、加料（多选）
    """
    __tablename__ = "option_groups"
    
    group_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dish_id = Column(Integer, ForeignKey("dishes.dish_id"), nullable=False)
    name = Column(String(50), nullable=False)  # 口味组名：辣度/甜度/分量
    type = Column(SQLEnum(OptionType), default=OptionType.SINGLE, nullable=False)
    required = Column(Boolean, default=False)  # 是否必选
    max_select = Column(Integer, default=1)    # 多选时最多选几项（单选=1）
    
    # 关系
    dish = relationship("Dish", back_populates="option_groups")
    items = relationship("OptionItem", back_populates="group", cascade="all, delete-orphan")


class OptionItem(Base):
    """
    具体的口味选项
    示例：微辣、中辣、特辣
    """
    __tablename__ = "option_items"
    
    item_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("option_groups.group_id"), nullable=False)
    name = Column(String(50), nullable=False)          # 选项名
    price_delta = Column(Numeric(10, 2), default=0)   # 加价（可为0）
    available = Column(Boolean, default=True)          # 是否可选
    
    # 关系
    group = relationship("OptionGroup", back_populates="items")

