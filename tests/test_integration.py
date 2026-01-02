"""
集成测试
测试方法：自底向上集成测试
- 先测试底层服务（库存服务）
- 再测试依赖底层服务的高层服务（订单服务）
- 最后测试完整的业务流程
"""
import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models.user import User
from app.models.dish import Category, Dish, OptionGroup, OptionItem
from app.models.enums import DishStatus, OrderStatus, OptionType
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService
from app.schemas.order import OrderCreate, OrderItemCreate


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def integration_db():
    """创建集成测试数据库"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def setup_test_data(integration_db):
    """设置测试数据"""
    # 创建用户
    user = User(username="integration_test_user", is_admin=False)
    admin = User(username="admin", is_admin=True)
    integration_db.add_all([user, admin])
    integration_db.flush()
    
    # 创建分类
    category = Category(name="测试分类", sort_order=1)
    integration_db.add(category)
    integration_db.flush()
    
    # 创建菜品
    dishes = []
    for i, (name, price, stock) in enumerate([
        ("宫保鸡丁", Decimal("38"), 20),
        ("红烧肉", Decimal("58"), 15),
        ("清炒时蔬", Decimal("28"), 30),
    ]):
        dish = Dish(
            category_id=category.category_id,
            name=name,
            price=price,
            stock=stock,
            status=DishStatus.ON_SHELF
        )
        integration_db.add(dish)
        dishes.append(dish)
    integration_db.flush()
    
    # 为第一个菜品添加口味选项
    option_group = OptionGroup(
        dish_id=dishes[0].dish_id,
        name="辣度",
        type=OptionType.SINGLE,
        required=True,
        max_select=1
    )
    integration_db.add(option_group)
    integration_db.flush()
    
    options = []
    for name, delta in [("不辣", Decimal("0")), ("微辣", Decimal("0")), ("特辣", Decimal("5"))]:
        opt = OptionItem(
            group_id=option_group.group_id,
            name=name,
            price_delta=delta,
            available=True
        )
        integration_db.add(opt)
        options.append(opt)
    
    integration_db.commit()
    
    return {
        "user": user,
        "admin": admin,
        "category": category,
        "dishes": dishes,
        "option_group": option_group,
        "options": options
    }


# ============================================================================
# 集成测试组1：完整下单流程（库存服务 + 订单服务 + 状态变更）
# ============================================================================

class TestOrderFlowIntegration:
    """
    集成测试组1：完整下单流程
    测试目的：验证从下单到完成的完整业务流程
    测试方法：自底向上集成
    涉及模块：InventoryService -> OrderService -> 状态变更
    """
    
    def test_complete_order_flow_single_dish(self, integration_db, setup_test_data):
        """
        测试场景1.1：单菜品下单完整流程
        流程：检查库存 -> 创建订单 -> 扣减库存 -> 完成订单
        """
        data = setup_test_data
        inventory_service = InventoryService(integration_db)
        order_service = OrderService(integration_db)
        
        dish = data["dishes"][0]  # 宫保鸡丁，库存20
        
        # Step 1: 检查库存
        assert inventory_service.check_stock(dish.dish_id, 5) is True
        initial_stock = inventory_service.get_stock(dish.dish_id)
        assert initial_stock == 20
        
        # Step 2: 创建订单
        order_dto = OrderCreate(
            user_id=data["user"].user_id,
            remark="测试订单",
            items=[OrderItemCreate(dish_id=dish.dish_id, qty=5, option_item_ids=[])]
        )
        order = order_service.create_order(order_dto)
        
        # Step 3: 验证订单创建成功
        assert order.order_id > 0
        assert order.status == OrderStatus.SUBMITTED.value
        assert order.total_price == Decimal("190")  # 38 * 5
        
        # Step 4: 验证库存已扣减
        current_stock = inventory_service.get_stock(dish.dish_id)
        assert current_stock == 15  # 20 - 5
        
        # Step 5: 完成订单
        order_service.complete_order(order.order_id)
        
        # Step 6: 验证订单状态
        completed_order = order_service.get_order_by_id(order.order_id)
        assert completed_order.status == OrderStatus.COMPLETED.value
    
    def test_complete_order_flow_multiple_dishes(self, integration_db, setup_test_data):
        """
        测试场景1.2：多菜品下单完整流程
        流程：多菜品库存检查 -> 创建订单 -> 批量扣减库存 -> 验证总价
        """
        data = setup_test_data
        inventory_service = InventoryService(integration_db)
        order_service = OrderService(integration_db)
        
        # Step 1: 检查所有菜品库存
        for dish in data["dishes"]:
            assert inventory_service.check_stock(dish.dish_id, 2) is True
        
        # Step 2: 创建包含多个菜品的订单
        order_dto = OrderCreate(
            user_id=data["user"].user_id,
            remark="多菜品订单",
            items=[
                OrderItemCreate(dish_id=data["dishes"][0].dish_id, qty=2, option_item_ids=[]),  # 宫保鸡丁 38*2
                OrderItemCreate(dish_id=data["dishes"][1].dish_id, qty=1, option_item_ids=[]),  # 红烧肉 58*1
                OrderItemCreate(dish_id=data["dishes"][2].dish_id, qty=3, option_item_ids=[]),  # 清炒时蔬 28*3
            ]
        )
        order = order_service.create_order(order_dto)
        
        # Step 3: 验证总价
        expected_total = Decimal("38") * 2 + Decimal("58") * 1 + Decimal("28") * 3
        assert order.total_price == expected_total  # 76 + 58 + 84 = 218
        
        # Step 4: 验证各菜品库存
        assert inventory_service.get_stock(data["dishes"][0].dish_id) == 18  # 20 - 2
        assert inventory_service.get_stock(data["dishes"][1].dish_id) == 14  # 15 - 1
        assert inventory_service.get_stock(data["dishes"][2].dish_id) == 27  # 30 - 3
    
    def test_complete_order_flow_with_options(self, integration_db, setup_test_data):
        """
        测试场景1.3：带口味选项的下单流程
        流程：选择口味选项 -> 创建订单 -> 验证加价计算
        """
        data = setup_test_data
        order_service = OrderService(integration_db)
        
        # 选择"特辣"选项（加价5元）
        spicy_option = data["options"][2]  # 特辣
        
        order_dto = OrderCreate(
            user_id=data["user"].user_id,
            remark="特辣订单",
            items=[
                OrderItemCreate(
                    dish_id=data["dishes"][0].dish_id,
                    qty=2,
                    option_item_ids=[spicy_option.item_id]
                )
            ]
        )
        order = order_service.create_order(order_dto)
        
        # 验证价格包含选项加价：(38 + 5) * 2 = 86
        assert order.total_price == Decimal("86")
    
    def test_order_cancellation_flow(self, integration_db, setup_test_data):
        """
        测试场景1.4：订单取消流程
        流程：创建订单 -> 取消订单 -> 验证状态（库存不退回）
        """
        data = setup_test_data
        inventory_service = InventoryService(integration_db)
        order_service = OrderService(integration_db)
        
        dish = data["dishes"][0]
        initial_stock = inventory_service.get_stock(dish.dish_id)
        
        # 创建订单
        order_dto = OrderCreate(
            user_id=data["user"].user_id,
            remark="待取消订单",
            items=[OrderItemCreate(dish_id=dish.dish_id, qty=3, option_item_ids=[])]
        )
        order = order_service.create_order(order_dto)
        
        # 取消订单
        order_service.cancel_order(order.order_id)
        
        # 验证订单状态
        cancelled_order = order_service.get_order_by_id(order.order_id)
        assert cancelled_order.status == OrderStatus.CANCELLED.value
        
        # 验证库存未退回（业务规则：取消不退库存）
        current_stock = inventory_service.get_stock(dish.dish_id)
        assert current_stock == initial_stock - 3


# ============================================================================
# 集成测试组2：库存与订单联动（边界条件与异常处理）
# ============================================================================

class TestInventoryOrderIntegration:
    """
    集成测试组2：库存与订单联动
    测试目的：验证库存边界条件下的订单行为
    测试方法：自底向上集成
    涉及模块：InventoryService <-> OrderService
    """
    
    def test_order_exhausts_stock(self, integration_db, setup_test_data):
        """
        测试场景2.1：订单耗尽库存
        流程：下单数量等于库存 -> 库存归零 -> 后续订单失败
        """
        data = setup_test_data
        inventory_service = InventoryService(integration_db)
        order_service = OrderService(integration_db)
        
        dish = data["dishes"][1]  # 红烧肉，库存15
        
        # 第一个订单：消耗全部库存
        order1_dto = OrderCreate(
            user_id=data["user"].user_id,
            remark="",
            items=[OrderItemCreate(dish_id=dish.dish_id, qty=15, option_item_ids=[])]
        )
        order1 = order_service.create_order(order1_dto)
        assert order1.order_id > 0
        
        # 验证库存归零
        assert inventory_service.get_stock(dish.dish_id) == 0
        assert inventory_service.check_stock(dish.dish_id, 1) is False
        
        # 第二个订单：应该失败
        order2_dto = OrderCreate(
            user_id=data["user"].user_id,
            remark="",
            items=[OrderItemCreate(dish_id=dish.dish_id, qty=1, option_item_ids=[])]
        )
        
        with pytest.raises(ValueError, match="库存不足"):
            order_service.create_order(order2_dto)
    
    def test_admin_restocks_then_order(self, integration_db, setup_test_data):
        """
        测试场景2.2：管理员补货后下单
        流程：库存不足 -> 管理员补货 -> 下单成功
        """
        data = setup_test_data
        inventory_service = InventoryService(integration_db)
        order_service = OrderService(integration_db)
        
        dish = data["dishes"][2]  # 清炒时蔬，库存30
        
        # 消耗大部分库存
        order1_dto = OrderCreate(
            user_id=data["user"].user_id,
            remark="",
            items=[OrderItemCreate(dish_id=dish.dish_id, qty=28, option_item_ids=[])]
        )
        order_service.create_order(order1_dto)
        
        # 验证库存不足以下单5份
        assert inventory_service.get_stock(dish.dish_id) == 2
        assert inventory_service.check_stock(dish.dish_id, 5) is False
        
        # 管理员补货
        inventory_service.adjust_stock(dish.dish_id, 10)
        
        # 验证补货后可以下单
        assert inventory_service.get_stock(dish.dish_id) == 12
        assert inventory_service.check_stock(dish.dish_id, 5) is True
        
        # 下单成功
        order2_dto = OrderCreate(
            user_id=data["user"].user_id,
            remark="",
            items=[OrderItemCreate(dish_id=dish.dish_id, qty=5, option_item_ids=[])]
        )
        order2 = order_service.create_order(order2_dto)
        assert order2.order_id > 0
    
    def test_partial_order_rollback(self, integration_db, setup_test_data):
        """
        测试场景2.3：部分订单失败时的事务回滚
        流程：多菜品订单，其中一个库存不足 -> 整个订单回滚
        """
        data = setup_test_data
        inventory_service = InventoryService(integration_db)
        order_service = OrderService(integration_db)
        
        # 记录初始库存
        initial_stocks = {
            dish.dish_id: inventory_service.get_stock(dish.dish_id)
            for dish in data["dishes"]
        }
        
        # 尝试创建订单，第二个菜品数量超过库存
        order_dto = OrderCreate(
            user_id=data["user"].user_id,
            remark="",
            items=[
                OrderItemCreate(dish_id=data["dishes"][0].dish_id, qty=2, option_item_ids=[]),
                OrderItemCreate(dish_id=data["dishes"][1].dish_id, qty=100, option_item_ids=[]),  # 超过库存
            ]
        )
        
        with pytest.raises(ValueError, match="库存不足"):
            order_service.create_order(order_dto)
        
        # 验证所有库存都未变化（事务回滚）
        for dish in data["dishes"]:
            current_stock = inventory_service.get_stock(dish.dish_id)
            assert current_stock == initial_stocks[dish.dish_id]
    
    def test_dish_off_shelf_during_order(self, integration_db, setup_test_data):
        """
        测试场景2.4：下架菜品无法下单
        流程：菜品下架 -> 下单失败
        """
        data = setup_test_data
        order_service = OrderService(integration_db)
        
        dish = data["dishes"][0]
        
        # 下架菜品
        dish.status = DishStatus.OFF_SHELF
        integration_db.commit()
        
        # 尝试下单
        order_dto = OrderCreate(
            user_id=data["user"].user_id,
            remark="",
            items=[OrderItemCreate(dish_id=dish.dish_id, qty=1, option_item_ids=[])]
        )
        
        with pytest.raises(ValueError, match="菜品不可用"):
            order_service.create_order(order_dto)


# ============================================================================
# 集成测试组3：多用户订单场景
# ============================================================================

class TestMultiUserIntegration:
    """
    集成测试组3：多用户订单场景
    测试目的：验证多用户同时操作的业务逻辑正确性
    测试方法：自底向上集成
    涉及模块：User -> Order -> Inventory
    """
    
    def test_multiple_users_order_same_dish(self, integration_db, setup_test_data):
        """
        测试场景3.1：多用户下单同一菜品
        流程：用户A下单 -> 用户B下单 -> 验证库存正确扣减
        """
        data = setup_test_data
        inventory_service = InventoryService(integration_db)
        order_service = OrderService(integration_db)
        
        # 创建第二个用户
        user2 = User(username="user2", is_admin=False)
        integration_db.add(user2)
        integration_db.commit()
        
        dish = data["dishes"][0]  # 库存20
        
        # 用户1下单5份
        order1_dto = OrderCreate(
            user_id=data["user"].user_id,
            remark="用户1订单",
            items=[OrderItemCreate(dish_id=dish.dish_id, qty=5, option_item_ids=[])]
        )
        order1 = order_service.create_order(order1_dto)
        assert order1.order_id > 0
        
        # 用户2下单3份
        order2_dto = OrderCreate(
            user_id=user2.user_id,
            remark="用户2订单",
            items=[OrderItemCreate(dish_id=dish.dish_id, qty=3, option_item_ids=[])]
        )
        order2 = order_service.create_order(order2_dto)
        assert order2.order_id > 0
        
        # 验证库存：20 - 5 - 3 = 12
        assert inventory_service.get_stock(dish.dish_id) == 12
        
        # 验证订单列表
        all_orders = order_service.list_orders()
        assert len(all_orders) == 2
    
    def test_user_order_history(self, integration_db, setup_test_data):
        """
        测试场景3.2：用户订单历史
        流程：用户创建多个订单 -> 查询用户订单列表
        """
        data = setup_test_data
        order_service = OrderService(integration_db)
        
        # 创建3个订单
        for i in range(3):
            order_dto = OrderCreate(
                user_id=data["user"].user_id,
                remark=f"订单{i+1}",
                items=[OrderItemCreate(dish_id=data["dishes"][i % 3].dish_id, qty=1, option_item_ids=[])]
            )
            order_service.create_order(order_dto)
        
        # 查询用户订单
        user_orders = order_service.list_orders(user_id=data["user"].user_id)
        assert len(user_orders) == 3
        
        # 完成第一个订单
        order_service.complete_order(user_orders[0].order_id)
        
        # 取消第二个订单
        order_service.cancel_order(user_orders[1].order_id)
        
        # 按状态查询
        submitted = order_service.list_orders(
            user_id=data["user"].user_id,
            status=OrderStatus.SUBMITTED.value
        )
        assert len(submitted) == 1
        
        completed = order_service.list_orders(
            user_id=data["user"].user_id,
            status=OrderStatus.COMPLETED.value
        )
        assert len(completed) == 1

