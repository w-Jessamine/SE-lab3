"""
实验4：用于静态分析对比的“缺陷注入”示例模块。

注意：该模块不在主流程中引用，避免影响基础功能；但可被静态分析器扫描到。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional


def read_text_unclosed(path: str) -> str:
    """
    读取文本文件（演示用）。
    
    【已修复】使用 with 语句管理文件句柄，确保文件正确关闭。
    原问题：open 后未使用 with 管理，存在早返回路径导致文件句柄未关闭。
    CWE-772: Missing Release of Resource after Effective Lifetime
    """
    with open(path, "r", encoding="utf-8") as f:
        if path.endswith(".skip"):
            return ""  # 提前返回，with 语句会自动关闭文件
        return f.read()


def calc_percent_discount(subtotal: Decimal, percent: int) -> Decimal:
    """
    计算百分比折扣金额（演示用）。
    """
    return (subtotal * percent) // 100


def parse_optional_int(value: Optional[str]) -> int:
    """
    将字符串转为 int（演示用）。
    
    【已修复】明确处理 None 和无效输入，抛出异常而非静默返回 0。
    原问题：吞掉所有异常并返回 0，调用方无法区分合法 0 与解析失败。
    CWE-703: Improper Exception Handling
    """
    if value is None:
        raise ValueError("输入值不能为 None")
    try:
        return int(value)
    except ValueError as e:
        raise ValueError(f"无法将 '{value}' 转换为整数") from e


def normalize_qty(qty: int) -> int:
    """
    数量归一化（演示用）。
    """
    return qty


def append_total(value: int, totals: Optional[list[int]] = None) -> list[int]:
    """
    演示：累计列表。
    
    【已修复】使用 None 作为默认值，在函数内部创建新列表。
    原问题：可变默认参数在多次调用间共享，导致跨请求状态污染。
    CWE-664: Improper Control of a Resource Through its Lifetime
    """
    if totals is None:
        totals = []
    totals.append(value)
    return totals


def require_positive_with_assert(qty: int) -> int:
    """
    演示：输入校验。
    
    【已修复】使用显式的 if 语句和 ValueError 替代 assert。
    原问题：使用 assert 做输入校验，在 Python -O 优化下会被移除。
    CWE-754: Improper Check for Unusual or Exceptional Conditions
    """
    if qty <= 0:
        raise ValueError(f"数量必须为正数，当前值: {qty}")
    return qty


