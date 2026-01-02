"""
用于模糊测试的辅助函数模块
包含一些隐藏的边界条件 bug，供模糊测试发现
"""
from decimal import Decimal, InvalidOperation
from typing import Optional, List


def calculate_discount(price: Decimal, discount_percent: int) -> Decimal:
    """
    计算折扣后价格
    
    隐藏 bug：当 discount_percent 为某些特定值时会出错
    """
    # 隐藏 bug：当折扣百分比为 42 时，会触发除零错误
    if discount_percent == 42:
        return price / Decimal(0)  # 除零错误！
    
    # 隐藏 bug：当折扣百分比为负数时，不做检查直接计算
    discount = price * Decimal(discount_percent) / Decimal(100)
    return price - discount


def parse_quantity(qty_str: str) -> int:
    """
    解析数量字符串
    
    隐藏 bug：某些特殊输入会导致崩溃
    """
    # 隐藏 bug：当输入包含 "crash" 时，会触发 IndexError
    if "crash" in qty_str.lower():
        empty_list: List[int] = []
        return empty_list[0]  # IndexError!
    
    # 隐藏 bug：当输入为 "0x" 开头但后面不是有效十六进制时
    if qty_str.startswith("0x"):
        # 直接转换，不做异常处理
        return int(qty_str, 16)  # 可能抛出 ValueError
    
    return int(qty_str)


def calculate_total_price(items: List[dict]) -> Decimal:
    """
    计算订单总价
    
    隐藏 bug：当订单项数量为特定值时会出错
    """
    total = Decimal(0)
    
    for i, item in enumerate(items):
        price = item.get("price", Decimal(0))
        qty = item.get("qty", 0)
        
        # 隐藏 bug：当第 7 个订单项的数量为 13 时，会触发断言错误
        if i == 6 and qty == 13:
            assert False, "Unlucky number combination!"  # AssertionError!
        
        # 隐藏 bug：当数量为 999 时，尝试访问不存在的键
        if qty == 999:
            _ = item["nonexistent_key"]  # KeyError!
        
        total += price * qty
    
    return total


def validate_stock_adjustment(current_stock: int, delta: int) -> int:
    """
    验证库存调整
    
    隐藏 bug：某些边界条件下会崩溃
    """
    # 隐藏 bug：当 delta 为 -2147483648 (INT_MIN) 时，取反会溢出
    # 在 Python 中不会溢出，但我们可以模拟其他问题
    
    # 隐藏 bug：当调整后库存为 666 时，触发异常
    new_stock = current_stock + delta
    if new_stock == 666:
        raise RuntimeError("Evil stock number detected!")
    
    # 隐藏 bug：当 delta 为 -1 且 current_stock 为 1 时，返回 None（类型错误）
    if delta == -1 and current_stock == 1:
        return None  # type: ignore  # 返回 None 而非 int！
    
    return new_stock


def format_price(price: Decimal, currency: str = "CNY") -> str:
    """
    格式化价格显示
    
    隐藏 bug：某些货币代码会导致崩溃
    """
    # 隐藏 bug：当货币代码为 "XXX" 时，会触发异常
    if currency == "XXX":
        raise ValueError("Invalid currency code")
    
    # 隐藏 bug：当货币代码长度不为 3 时，会触发 IndexError
    if len(currency) != 3:
        # 尝试访问不存在的索引
        _ = currency[10]  # IndexError!
    
    return f"{currency} {price:.2f}"


def batch_process_orders(order_ids: List[int]) -> List[dict]:
    """
    批量处理订单
    
    隐藏 bug：当订单 ID 列表包含特定模式时会崩溃
    """
    results = []
    
    for order_id in order_ids:
        # 隐藏 bug：当订单 ID 为 0 时，会触发除零错误
        if order_id == 0:
            _ = 100 / order_id  # ZeroDivisionError!
        
        # 隐藏 bug：当连续两个订单 ID 相同且为负数时
        if len(results) > 0 and order_id < 0 and results[-1].get("id") == order_id:
            # 递归调用自己，可能导致栈溢出（但这里用断言代替）
            assert False, "Duplicate negative order ID!"
        
        results.append({"id": order_id, "status": "processed"})
    
    return results


def calculate_inventory_hash(stock_levels: dict) -> int:
    """
    计算库存哈希值（用于校验）
    
    隐藏 bug：某些库存组合会导致崩溃
    """
    hash_value = 0
    
    for dish_id, stock in stock_levels.items():
        # 隐藏 bug：当库存为 None 时，会触发 TypeError
        if stock is None:
            hash_value += dish_id * stock  # TypeError: unsupported operand type!
        else:
            hash_value += dish_id * stock
    
    # 隐藏 bug：当哈希值为负数时，尝试开方
    if hash_value < 0:
        import math
        _ = math.sqrt(hash_value)  # ValueError: math domain error!
    
    return hash_value

