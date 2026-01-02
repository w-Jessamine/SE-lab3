"""订单与菜品状态枚举"""
import enum


class DishStatus(str, enum.Enum):
    """菜品状态"""
    ON_SHELF = "OnShelf"      # 上架
    OFF_SHELF = "OffShelf"    # 下架


class OrderStatus(str, enum.Enum):
    """订单状态流转：Created → Submitted → Completed/Cancelled"""
    CREATED = "Created"
    SUBMITTED = "Submitted"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"


class OptionType(str, enum.Enum):
    """口味选项类型"""
    SINGLE = "Single"      # 单选
    MULTIPLE = "Multiple"  # 多选

