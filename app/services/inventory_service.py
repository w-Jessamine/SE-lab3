"""库存服务"""
from sqlalchemy.orm import Session
from app.models.dish import Dish


class InventoryService:
    """库存管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_stock(self, dish_id: int, qty: int) -> bool:
        """
        检查库存是否充足
        前置条件：dish_id 存在
        契约：return dish.is_available() and dish.stock >= qty
        """
        dish = self.db.query(Dish).filter(Dish.dish_id == dish_id).first()
        if not dish:
            return False
        return dish.is_available() and dish.stock >= qty
    
    def deduct_stock(self, dish_id: int, qty: int) -> None:
        """
        扣减库存（需在事务中调用）
        前置条件：
          - 调用方已开启事务
          - 已通过 check_stock 校验
        后置条件：dish.stock -= qty
        异常：若库存不足抛出 ValueError
        """
        dish = self.db.query(Dish).filter(Dish.dish_id == dish_id).first()
        if not dish:
            raise ValueError(f"菜品不存在：dish_id={dish_id}")
        
        if not dish.is_available():
            raise ValueError(f"菜品不可用：{dish.name}（状态={dish.status.value}，库存={dish.stock}）")
        
        if dish.stock < qty:
            raise ValueError(f"库存不足：{dish.name} 当前库存 {dish.stock}，需要 {qty}")
        
        dish.update_stock(-qty)
        # 确保其他会话可见，且 refresh 能读取到
        self.db.flush()
    
    def adjust_stock(self, dish_id: int, delta: int) -> None:
        """
        管理员手动调整库存
        参数：delta 可正可负
        前置条件：调整后库存 >= 0
        后置条件：提交事务
        异常：若调整后 < 0 抛出 ValueError
        """
        dish = self.db.query(Dish).filter(Dish.dish_id == dish_id).first()
        if not dish:
            raise ValueError(f"菜品不存在：dish_id={dish_id}")
        
        dish.update_stock(delta)
        self.db.commit()
    
    def adjust_stock_batch(self, updates: list[tuple[int, int]]) -> None:
        """
        批量调整库存
        参数：updates = [(dish_id, delta), ...]
        事务性：任一失败则整体回滚
        """
        try:
            for dish_id, delta in updates:
                dish = self.db.query(Dish).filter(Dish.dish_id == dish_id).first()
                if not dish:
                    raise ValueError(f"菜品不存在：dish_id={dish_id}")
                dish.update_stock(delta)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
    
    def get_stock(self, dish_id: int) -> int:
        """
        查询实时库存
        契约：直接返回 dish.stock
        """
        dish = self.db.query(Dish).filter(Dish.dish_id == dish_id).first()
        if not dish:
            raise ValueError(f"菜品不存在：dish_id={dish_id}")
        return dish.stock

