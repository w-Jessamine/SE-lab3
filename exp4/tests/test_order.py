"""订单服务测试"""
import pytest
from decimal import Decimal
from app.models.user import User
from app.models.dish import Category, Dish, OptionGroup, OptionItem
from app.models.enums import DishStatus, OrderStatus, OptionType
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.order_service import OrderService


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    user = User(username="testuser", is_admin=False)
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_dishes(db_session):
    """创建测试菜品"""
    category = Category(name="测试分类", sort_order=1)
    db_session.add(category)
    db_session.flush()
    
    dish1 = Dish(
        category_id=category.category_id,
        name="菜品A",
        price=Decimal("30"),
        stock=10,
        status=DishStatus.ON_SHELF
    )
    dish2 = Dish(
        category_id=category.category_id,
        name="菜品B",
        price=Decimal("20"),
        stock=5,
        status=DishStatus.ON_SHELF
    )
    db_session.add_all([dish1, dish2])
    db_session.commit()
    return [dish1, dish2]


def test_create_order_success(db_session, test_user, test_dishes):
    """测试正常下单成功，返回 order_id 与 total_price"""
    service = OrderService(db_session)
    
    order_dto = OrderCreate(
        user_id=test_user.user_id,
        remark="测试订单",
        items=[
            OrderItemCreate(dish_id=test_dishes[0].dish_id, qty=2, option_item_ids=[]),
            OrderItemCreate(dish_id=test_dishes[1].dish_id, qty=1, option_item_ids=[])
        ]
    )
    
    result = service.create_order(order_dto)
    
    assert result.order_id > 0
    assert result.total_price == Decimal("80")  # 30*2 + 20*1
    assert result.status == OrderStatus.SUBMITTED.value
    
    # 验证库存扣减
    db_session.refresh(test_dishes[0])
    db_session.refresh(test_dishes[1])
    assert test_dishes[0].stock == 8  # 10 - 2
    assert test_dishes[1].stock == 4  # 5 - 1


def test_create_order_out_of_stock(db_session, test_user, test_dishes):
    """测试库存不足时抛出 ValueError"""
    service = OrderService(db_session)
    
    order_dto = OrderCreate(
        user_id=test_user.user_id,
        remark="",
        items=[
            OrderItemCreate(dish_id=test_dishes[1].dish_id, qty=10, option_item_ids=[])
        ]
    )
    
    with pytest.raises(ValueError, match="库存不足"):
        service.create_order(order_dto)
    
    # 验证库存未扣减（回滚）
    db_session.refresh(test_dishes[1])
    assert test_dishes[1].stock == 5


def test_create_order_dish_off_shelf(db_session, test_user, test_dishes):
    """测试菜品下架时抛出 ValueError"""
    # 下架菜品
    test_dishes[0].status = DishStatus.OFF_SHELF
    db_session.commit()
    
    service = OrderService(db_session)
    
    order_dto = OrderCreate(
        user_id=test_user.user_id,
        remark="",
        items=[
            OrderItemCreate(dish_id=test_dishes[0].dish_id, qty=1, option_item_ids=[])
        ]
    )
    
    with pytest.raises(ValueError, match="菜品不可用"):
        service.create_order(order_dto)


def test_cancel_order(db_session, test_user, test_dishes):
    """测试取消订单状态变更"""
    service = OrderService(db_session)
    
    # 先创建订单
    order_dto = OrderCreate(
        user_id=test_user.user_id,
        remark="",
        items=[
            OrderItemCreate(dish_id=test_dishes[0].dish_id, qty=1, option_item_ids=[])
        ]
    )
    order = service.create_order(order_dto)
    
    # 取消订单
    service.cancel_order(order.order_id)
    
    # 验证状态
    cancelled_order = service.get_order_by_id(order.order_id)
    assert cancelled_order.status == OrderStatus.CANCELLED.value


def test_complete_order(db_session, test_user, test_dishes):
    """测试完成订单状态变更"""
    service = OrderService(db_session)
    
    # 先创建订单
    order_dto = OrderCreate(
        user_id=test_user.user_id,
        remark="",
        items=[
            OrderItemCreate(dish_id=test_dishes[0].dish_id, qty=1, option_item_ids=[])
        ]
    )
    order = service.create_order(order_dto)
    
    # 完成订单
    service.complete_order(order.order_id)
    
    # 验证状态
    completed_order = service.get_order_by_id(order.order_id)
    assert completed_order.status == OrderStatus.COMPLETED.value


def test_create_order_with_options(db_session, test_user, test_dishes):
    """测试带选项的订单创建"""
    # 为菜品添加选项
    option_group = OptionGroup(
        dish_id=test_dishes[0].dish_id,
        name="辣度",
        type=OptionType.SINGLE,
        required=True,
        max_select=1
    )
    db_session.add(option_group)
    db_session.flush()
    
    option_item = OptionItem(
        group_id=option_group.group_id,
        name="特辣",
        price_delta=Decimal("5"),
        available=True
    )
    db_session.add(option_item)
    db_session.commit()
    
    service = OrderService(db_session)
    
    order_dto = OrderCreate(
        user_id=test_user.user_id,
        remark="",
        items=[
            OrderItemCreate(
                dish_id=test_dishes[0].dish_id, 
                qty=1, 
                option_item_ids=[option_item.item_id]
            )
        ]
    )
    
    result = service.create_order(order_dto)
    
    # 验证价格包含选项加价
    assert result.total_price == Decimal("35")  # 30 + 5

