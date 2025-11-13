"""订单模型"""
from decimal import Decimal
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum as SQLEnum, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db import Base
from app.models.enums import OrderStatus


# 中间表：order_items <-> option_items 多对多关系
order_item_options = Table(
    "order_item_options",
    Base.metadata,
    Column("order_item_id", Integer, ForeignKey("order_items.id"), primary_key=True),
    Column("option_item_id", Integer, ForeignKey("option_items.item_id"), primary_key=True),
)


class Order(Base):
    """
    订单实体
    状态流转：Created → Submitted → Completed/Cancelled
    """
    __tablename__ = "orders"
    
    order_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.CREATED, nullable=False)
    remark = Column(String(500), default="")  # 备注
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def total_price(self) -> Decimal:
        """
        计算订单总价
        契约：sum(item.subtotal() for item in self.items)
        """
        return sum((item.subtotal() for item in self.items), Decimal(0))
    
    def submit(self) -> None:
        """
        提交订单
        前置条件：self.status == OrderStatus.CREATED
        """
        if self.status != OrderStatus.CREATED:
            raise ValueError(f"订单状态错误：当前为 {self.status.value}，无法提交")
        self.status = OrderStatus.SUBMITTED
    
    def cancel(self) -> None:
        """
        取消订单
        前置条件：self.status in [CREATED, SUBMITTED]
        """
        if self.status not in [OrderStatus.CREATED, OrderStatus.SUBMITTED]:
            raise ValueError(f"订单状态错误：当前为 {self.status.value}，无法取消")
        self.status = OrderStatus.CANCELLED
    
    def complete(self) -> None:
        """
        完成订单
        前置条件：self.status == OrderStatus.SUBMITTED
        """
        if self.status != OrderStatus.SUBMITTED:
            raise ValueError(f"订单状态错误：当前为 {self.status.value}，无法完成")
        self.status = OrderStatus.COMPLETED


class OrderItem(Base):
    """
    订单明细项
    记录下单时的价格快照与数量
    """
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    dish_id = Column(Integer, ForeignKey("dishes.dish_id"), nullable=False)
    qty = Column(Integer, nullable=False)                    # 数量
    unit_price = Column(Numeric(10, 2), nullable=False)      # 下单时菜品单价快照
    
    # 关系
    order = relationship("Order", back_populates="items")
    dish = relationship("Dish")
    selected_options = relationship(
        "OptionItem",
        secondary=order_item_options,
        backref="order_items"
    )
    
    def subtotal(self) -> Decimal:
        """
        计算小计
        契约：(unit_price + sum(option.price_delta)) * qty
        """
        option_price = sum((opt.price_delta for opt in self.selected_options), Decimal(0))
        return (self.unit_price + option_price) * self.qty

