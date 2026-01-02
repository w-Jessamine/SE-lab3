"""模糊测试"""
import pytest
from decimal import Decimal
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models.user import User
from app.models.dish import Category, Dish
from app.models.enums import DishStatus
from app.services.inventory_service import InventoryService

# 导入包含隐藏 bug 的模块
from app.services.fuzz_target import (
    calculate_discount,
    parse_quantity,
    calculate_total_price,
    validate_stock_adjustment,
    format_price,
    batch_process_orders,
    calculate_inventory_hash,
)


# ============================================================================
# 崩溃复现测试：验证模糊测试发现的崩溃
# ============================================================================

class TestCrashReproduction:
    """
    崩溃复现测试
    这些测试用于复现模糊测试发现的崩溃，证明 bug 的存在
    """
    
    def test_crash_1_division_by_zero(self):
        """
        崩溃1：除零错误
        触发条件：discount_percent = 42
        错误类型：decimal.DivisionByZero
        """
        with pytest.raises(Exception) as exc_info:
            calculate_discount(Decimal("100"), 42)
        
        # 验证是除零错误
        assert "DivisionByZero" in str(type(exc_info.value))
        print(f"✅ 崩溃1复现成功: {type(exc_info.value).__name__}")
    
    def test_crash_2_invalid_literal(self):
        """
        崩溃2：无效字符串转整数
        触发条件：qty_str 包含非数字字符（如 ':'）
        错误类型：ValueError
        """
        with pytest.raises(ValueError) as exc_info:
            parse_quantity(":")
        
        assert "invalid literal" in str(exc_info.value)
        print(f"✅ 崩溃2复现成功: {exc_info.value}")
    
    def test_crash_3_index_error_crash_keyword(self):
        """
        崩溃3：IndexError（crash 关键字）
        触发条件：qty_str 包含 "crash"
        错误类型：IndexError
        """
        with pytest.raises(IndexError):
            parse_quantity("crash")
        
        print("✅ 崩溃3复现成功: IndexError")
    
    def test_crash_4_assertion_error(self):
        """
        崩溃4：断言错误
        触发条件：第7个订单项（索引6）的 qty = 13
        错误类型：AssertionError
        """
        items = [
            {"price": Decimal("100"), "qty": 1},
            {"price": Decimal("100"), "qty": 1},
            {"price": Decimal("100"), "qty": 1},
            {"price": Decimal("100"), "qty": 1},
            {"price": Decimal("100"), "qty": 1},
            {"price": Decimal("100"), "qty": 1},
            {"price": Decimal("100"), "qty": 13},  # 第7项，qty=13
        ]
        
        with pytest.raises(AssertionError) as exc_info:
            calculate_total_price(items)
        
        assert "Unlucky number" in str(exc_info.value)
        print(f"✅ 崩溃4复现成功: {exc_info.value}")
    
    def test_crash_5_runtime_error_666(self):
        """
        崩溃5：运行时错误（邪恶数字666）
        触发条件：current_stock + delta = 666
        错误类型：RuntimeError
        """
        with pytest.raises(RuntimeError) as exc_info:
            validate_stock_adjustment(166, 500)  # 166 + 500 = 666
        
        assert "Evil stock number" in str(exc_info.value)
        print(f"✅ 崩溃5复现成功: {exc_info.value}")
    
    def test_crash_6_type_error_none_return(self):
        """
        崩溃6：返回 None 而非 int
        触发条件：delta = -1, current_stock = 1
        错误类型：返回值为 None（类型错误）
        """
        result = validate_stock_adjustment(1, -1)
        
        # 验证返回了 None 而非 int
        assert result is None
        print(f"✅ 崩溃6复现成功: 返回 None 而非 int")
    
    def test_crash_7_index_error_currency(self):
        """
        崩溃7：索引越界（货币代码长度）
        触发条件：currency 长度不为 3
        错误类型：IndexError
        """
        with pytest.raises(IndexError):
            format_price(Decimal("100"), "A")  # 长度为 1，不是 3
        
        print("✅ 崩溃7复现成功: IndexError (currency)")
    
    def test_crash_8_zero_division_order_id(self):
        """
        崩溃8：除零错误（订单ID为0）
        触发条件：order_id = 0
        错误类型：ZeroDivisionError
        """
        with pytest.raises(ZeroDivisionError):
            batch_process_orders([0])
        
        print("✅ 崩溃8复现成功: ZeroDivisionError")
    
    def test_crash_9_type_error_none_stock(self):
        """
        崩溃9：类型错误（库存为None）
        触发条件：stock_levels 中包含 None 值
        错误类型：TypeError
        """
        with pytest.raises(TypeError) as exc_info:
            calculate_inventory_hash({1: None})
        
        assert "unsupported operand type" in str(exc_info.value)
        print(f"✅ 崩溃9复现成功: {exc_info.value}")


# ============================================================================
# 模糊测试：用于发现崩溃的测试（预期失败）
# 这些测试用于演示模糊测试如何发现 bug
# ============================================================================

class TestFuzzDiscoveryCrash:
    """
    模糊测试发现崩溃
    这些测试展示了 Hypothesis 如何自动发现崩溃
    注意：这些测试预期会失败，因为它们会触发 bug
    运行命令：python3 -m pytest tests/test_fuzz.py::TestFuzzDiscoveryCrash -v --tb=short
    """
    
    @given(
        price=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("1000"), places=2),
        discount_percent=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=500, database=None)  # 增加样例数确保覆盖 42
    def test_fuzz_calculate_discount_crash(self, price, discount_percent):
        """模糊测试：折扣计算 - 会发现 discount_percent=42 的崩溃"""
        result = calculate_discount(price, discount_percent)
        assert result >= 0
    
    @given(order_ids=st.lists(st.integers(min_value=-10, max_value=10), min_size=1, max_size=5))
    @settings(max_examples=200, database=None)
    def test_fuzz_batch_orders_crash(self, order_ids):
        """模糊测试：批量订单处理 - 会发现 order_id=0 的崩溃"""
        result = batch_process_orders(order_ids)
        assert len(result) == len(order_ids)


# ============================================================================
# 服务层模糊测试（健壮性验证 - 这些应该通过）
# ============================================================================

def create_test_db():
    """创建测试数据库"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def setup_test_data(db):
    """设置测试数据"""
    user = User(username="fuzz_user", is_admin=False)
    db.add(user)
    db.flush()
    
    category = Category(name="模糊测试分类", sort_order=1)
    db.add(category)
    db.flush()
    
    dish = Dish(
        category_id=category.category_id,
        name="模糊测试菜品",
        price=Decimal("50"),
        stock=1000,
        status=DishStatus.ON_SHELF
    )
    db.add(dish)
    db.commit()
    
    return {"user": user, "dish": dish, "db": db}


class TestServiceFuzzRobust:
    """服务层模糊测试（健壮性验证 - 应该通过）"""
    
    @given(qty=st.integers(min_value=1, max_value=100))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_inventory_check_stock_robust(self, qty):
        """模糊测试：库存检查（健壮的实现）"""
        db = create_test_db()
        data = setup_test_data(db)
        service = InventoryService(db)
        dish = data["dish"]
        
        try:
            result = service.check_stock(dish.dish_id, qty)
            assert isinstance(result, bool)
            if qty <= dish.stock:
                assert result is True
        finally:
            db.close()
    
    @given(delta=st.integers(min_value=-500, max_value=500))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_inventory_adjust_stock_robust(self, delta):
        """模糊测试：库存调整（健壮的实现）"""
        db = create_test_db()
        data = setup_test_data(db)
        service = InventoryService(db)
        dish = data["dish"]
        
        try:
            initial_stock = service.get_stock(dish.dish_id)
            
            if initial_stock + delta < 0:
                with pytest.raises(ValueError):
                    service.adjust_stock(dish.dish_id, delta)
            else:
                service.adjust_stock(dish.dish_id, delta)
                new_stock = service.get_stock(dish.dish_id)
                assert new_stock == initial_stock + delta
                assert new_stock >= 0
        finally:
            db.close()


# ============================================================================
# 状态机测试
# ============================================================================

class InventoryStateMachine(RuleBasedStateMachine):
    """库存状态机测试"""
    
    def __init__(self):
        super().__init__()
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = SessionLocal()
        
        category = Category(name="状态机测试", sort_order=1)
        self.db.add(category)
        self.db.flush()
        
        self.dish = Dish(
            category_id=category.category_id,
            name="状态机菜品",
            price=Decimal("100"),
            stock=500,
            status=DishStatus.ON_SHELF
        )
        self.db.add(self.dish)
        self.db.commit()
        
        self.service = InventoryService(self.db)
        self.expected_stock = 500
    
    @rule(delta=st.integers(min_value=-50, max_value=50))
    def adjust_stock(self, delta):
        if self.expected_stock + delta < 0:
            with pytest.raises(ValueError):
                self.service.adjust_stock(self.dish.dish_id, delta)
        else:
            self.service.adjust_stock(self.dish.dish_id, delta)
            self.expected_stock += delta
    
    @rule(qty=st.integers(min_value=1, max_value=20))
    def check_stock(self, qty):
        result = self.service.check_stock(self.dish.dish_id, qty)
        expected = qty <= self.expected_stock
        assert result == expected
    
    @invariant()
    def stock_is_consistent(self):
        actual_stock = self.service.get_stock(self.dish.dish_id)
        assert actual_stock == self.expected_stock
    
    @invariant()
    def stock_is_non_negative(self):
        actual_stock = self.service.get_stock(self.dish.dish_id)
        assert actual_stock >= 0
    
    def teardown(self):
        self.db.close()


TestInventoryStateMachine = InventoryStateMachine.TestCase
