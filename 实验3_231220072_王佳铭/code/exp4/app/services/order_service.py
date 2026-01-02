"""订单服务"""
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, update as sa_update
from app.models.order import Order, OrderItem
from app.models.dish import Dish, OptionItem
from app.models.enums import OrderStatus
from app.schemas.order import OrderCreate, OrderResponse, OrderDetailResponse, OrderItemResponse
from app.services.inventory_service import InventoryService


class OrderService:
    """订单业务逻辑"""
    
    def __init__(self, db: Session):
        self.db = db
        self.inventory_service = InventoryService(db)
    
    def create_order(self, dto: OrderCreate) -> OrderResponse:
        """
        创建订单（核心逻辑）
        
        事务边界：
          1. 开启事务
          2. 对所有涉及的 Dish 行加锁（SELECT ... FOR UPDATE）
          3. 校验：status==OnShelf AND stock >= qty
          4. 计算总价（dish.price + sum(option.price_delta)）* qty
          5. 扣减库存
          6. 插入 orders、order_items、order_item_options
          7. 提交事务
        
        并发安全：
          - MySQL: 使用 with_for_update()
          - SQLite: serializable 事务级别
        """
        # 开启事务（隐式，因为 db 会话默认开启）
        try:
            # 创建订单实例
            order = Order(
                user_id=dto.user_id,
                remark=dto.remark or "",
                status=OrderStatus.CREATED
            )
            self.db.add(order)
            self.db.flush()  # 获取 order_id
            
            total_price = Decimal(0)
            
            # 处理每个订单项
            for item_dto in dto.items:
                # 查询菜品（用于价格与名称快照）；并发校验在条件更新时完成
                dish = self.db.query(Dish).filter(Dish.dish_id == item_dto.dish_id).first()
                if not dish:
                    raise ValueError(f"菜品不存在：dish_id={item_dto.dish_id}")

                # 查询选中的口味选项
                selected_options = []
                if item_dto.option_item_ids:
                    selected_options = self.db.query(OptionItem).filter(
                        OptionItem.item_id.in_(item_dto.option_item_ids)
                    ).all()
                    
                    # 校验选项可用性
                    for opt in selected_options:
                        if not opt.available:
                            raise ValueError(f"选项不可用：{opt.name}")
                
                # 计算单项价格
                option_price = sum((opt.price_delta for opt in selected_options), Decimal(0))
                item_total = (dish.price + option_price) * item_dto.qty
                total_price += item_total
                
                # 并发安全的条件扣减库存（SQLite 兼容）
                result = self.db.execute(
                    sa_update(Dish)
                    .where(
                        Dish.dish_id == item_dto.dish_id,
                        Dish.status == dish.status.__class__.ON_SHELF,
                        Dish.stock >= item_dto.qty,
                    )
                    .values(stock=Dish.stock - item_dto.qty)
                )
                if result.rowcount == 0:
                    raise ValueError(f"库存不足：{dish.name} 当前库存 {dish.stock}，需要 {item_dto.qty}")
                
                # 创建订单项
                order_item = OrderItem(
                    order_id=order.order_id,
                    dish_id=dish.dish_id,
                    qty=item_dto.qty,
                    unit_price=dish.price,
                    selected_options=selected_options
                )
                self.db.add(order_item)
            
            # 提交订单状态
            order.status = OrderStatus.SUBMITTED
            
            # 提交事务
            self.db.commit()
            self.db.refresh(order)
            
            return OrderResponse(
                order_id=order.order_id,
                user_id=order.user_id,
                status=order.status.value,
                total_price=total_price,
                remark=order.remark,
                created_at=order.created_at
            )
        
        except Exception as e:
            self.db.rollback()
            raise e
    
    def cancel_order(self, order_id: int) -> None:
        """
        取消订单
        前置条件：order.status in [CREATED, SUBMITTED]
        后置条件：order.status = CANCELLED（不退库存）
        """
        order = self.db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise ValueError(f"订单不存在：order_id={order_id}")
        
        order.cancel()
        self.db.commit()
    
    def complete_order(self, order_id: int) -> None:
        """
        完成订单
        前置条件：order.status == SUBMITTED
        后置条件：order.status = COMPLETED
        """
        order = self.db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise ValueError(f"订单不存在：order_id={order_id}")
        
        order.complete()
        self.db.commit()
    
    def get_order_by_id(self, order_id: int) -> Optional[OrderDetailResponse]:
        """
        查询订单详情
        契约：包含订单项明细与总价
        """
        order = self.db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            return None
        
        # 构建订单项响应
        items_response = []
        for item in order.items:
            items_response.append(OrderItemResponse(
                id=item.id,
                dish_id=item.dish_id,
                dish_name=item.dish.name,
                qty=item.qty,
                unit_price=item.unit_price,
                subtotal=item.subtotal()
            ))
        
        return OrderDetailResponse(
            order_id=order.order_id,
            user_id=order.user_id,
            status=order.status.value,
            total_price=order.total_price(),
            remark=order.remark,
            created_at=order.created_at,
            items=items_response
        )
    
    def list_orders(
        self,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 20
    ) -> List[OrderResponse]:
        """
        订单列表（后台管理/用户查询）
        参数：可选筛选 user_id、status
        """
        query = self.db.query(Order)
        
        # 按用户筛选
        if user_id is not None:
            query = query.filter(Order.user_id == user_id)
        
        # 按状态筛选
        if status is not None:
            query = query.filter(Order.status == OrderStatus(status))
        
        # 分页
        offset = (page - 1) * size
        orders = query.order_by(Order.created_at.desc()).offset(offset).limit(size).all()
        
        return [
            OrderResponse(
                order_id=order.order_id,
                user_id=order.user_id,
                status=order.status.value,
                total_price=order.total_price(),
                remark=order.remark,
                created_at=order.created_at
            )
            for order in orders
        ]

