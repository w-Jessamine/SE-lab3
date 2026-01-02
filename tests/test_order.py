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


def test_create_order_nonexistent_dish(db_session, test_user):
    """测试菜品不存在时抛出 ValueError"""
    service = OrderService(db_session)
    
    order_dto = OrderCreate(
        user_id=test_user.user_id,
        remark="",
        items=[
            OrderItemCreate(dish_id=9999, qty=1, option_item_ids=[])
        ]
    )
    
    with pytest.raises(ValueError, match="菜品不存在"):
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


def test_cancel_order_nonexistent(db_session):
    """测试取消不存在的订单抛出 ValueError"""
    service = OrderService(db_session)
    
    with pytest.raises(ValueError, match="订单不存在"):
        service.cancel_order(9999)


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


def test_complete_order_nonexistent(db_session):
    """测试完成不存在的订单抛出 ValueError"""
    service = OrderService(db_session)
    
    with pytest.raises(ValueError, match="订单不存在"):
        service.complete_order(9999)


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


def test_create_order_with_unavailable_option(db_session, test_user, test_dishes):
    """测试使用不可用选项时抛出 ValueError"""
    # 为菜品添加不可用选项
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
        available=False  # 不可用
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
    
    with pytest.raises(ValueError, match="选项不可用"):
        service.create_order(order_dto)


def test_get_order_by_id_success(db_session, test_user, test_dishes):
    """测试查询订单详情成功"""
    service = OrderService(db_session)
    
    # 先创建订单
    order_dto = OrderCreate(
        user_id=test_user.user_id,
        remark="测试备注",
        items=[
            OrderItemCreate(dish_id=test_dishes[0].dish_id, qty=2, option_item_ids=[])
        ]
    )
    created_order = service.create_order(order_dto)
    
    # 查询订单详情
    order_detail = service.get_order_by_id(created_order.order_id)
    
    assert order_detail is not None
    assert order_detail.order_id == created_order.order_id
    assert order_detail.remark == "测试备注"
    assert len(order_detail.items) == 1
    assert order_detail.items[0].qty == 2


def test_get_order_by_id_nonexistent(db_session):
    """测试查询不存在的订单返回 None"""
    service = OrderService(db_session)
    
    result = service.get_order_by_id(9999)
    assert result is None


def test_list_orders_all(db_session, test_user, test_dishes):
    """测试列出所有订单"""
    service = OrderService(db_session)
    
    # 创建多个订单
    for i in range(3):
        order_dto = OrderCreate(
            user_id=test_user.user_id,
            remark=f"订单{i+1}",
            items=[
                OrderItemCreate(dish_id=test_dishes[0].dish_id, qty=1, option_item_ids=[])
            ]
        )
        service.create_order(order_dto)
    
    # 列出所有订单
    orders = service.list_orders()
    assert len(orders) == 3


def test_list_orders_by_user(db_session, test_dishes):
    """测试按用户筛选订单"""
    # 创建两个用户
    user1 = User(username="user1", is_admin=False)
    user2 = User(username="user2", is_admin=False)
    db_session.add_all([user1, user2])
    db_session.commit()
    
    service = OrderService(db_session)
    
    # 为user1创建2个订单
    for _ in range(2):
        order_dto = OrderCreate(
            user_id=user1.user_id,
            remark="",
            items=[OrderItemCreate(dish_id=test_dishes[0].dish_id, qty=1, option_item_ids=[])]
        )
        service.create_order(order_dto)
    
    # 为user2创建1个订单
    order_dto = OrderCreate(
        user_id=user2.user_id,
        remark="",
        items=[OrderItemCreate(dish_id=test_dishes[0].dish_id, qty=1, option_item_ids=[])]
    )
    service.create_order(order_dto)
    
    # 按user1筛选
    user1_orders = service.list_orders(user_id=user1.user_id)
    assert len(user1_orders) == 2
    
    # 按user2筛选
    user2_orders = service.list_orders(user_id=user2.user_id)
    assert len(user2_orders) == 1


def test_list_orders_by_status(db_session, test_user, test_dishes):
    """测试按状态筛选订单"""
    service = OrderService(db_session)
    
    # 创建3个订单
    orders = []
    for i in range(3):
        order_dto = OrderCreate(
            user_id=test_user.user_id,
            remark="",
            items=[OrderItemCreate(dish_id=test_dishes[0].dish_id, qty=1, option_item_ids=[])]
        )
        orders.append(service.create_order(order_dto))
    
    # 完成第一个订单
    service.complete_order(orders[0].order_id)
    
    # 取消第二个订单
    service.cancel_order(orders[1].order_id)
    
    # 按状态筛选
    submitted_orders = service.list_orders(status=OrderStatus.SUBMITTED.value)
    assert len(submitted_orders) == 1
    
    completed_orders = service.list_orders(status=OrderStatus.COMPLETED.value)
    assert len(completed_orders) == 1
    
    cancelled_orders = service.list_orders(status=OrderStatus.CANCELLED.value)
    assert len(cancelled_orders) == 1


def test_list_orders_pagination(db_session, test_user, test_dishes):
    """测试订单分页"""
    service = OrderService(db_session)
    
    # 创建5个订单
    for i in range(5):
        order_dto = OrderCreate(
            user_id=test_user.user_id,
            remark=f"订单{i+1}",
            items=[OrderItemCreate(dish_id=test_dishes[0].dish_id, qty=1, option_item_ids=[])]
        )
        service.create_order(order_dto)
    
    # 第一页，每页2条
    page1 = service.list_orders(page=1, size=2)
    assert len(page1) == 2
    
    # 第二页，每页2条
    page2 = service.list_orders(page=2, size=2)
    assert len(page2) == 2
    
    # 第三页，每页2条
    page3 = service.list_orders(page=3, size=2)
    assert len(page3) == 1


def test_create_order_with_empty_remark(db_session, test_user, test_dishes):
    """测试创建订单时备注为空"""
    service = OrderService(db_session)
    
    order_dto = OrderCreate(
        user_id=test_user.user_id,
        remark=None,  # 空备注
        items=[
            OrderItemCreate(dish_id=test_dishes[0].dish_id, qty=1, option_item_ids=[])
        ]
    )
    
    result = service.create_order(order_dto)
    assert result.remark == ""


def test_create_order_multiple_same_dish(db_session, test_user, test_dishes):
    """测试同一订单包含同一菜品多次"""
    service = OrderService(db_session)
    
    order_dto = OrderCreate(
        user_id=test_user.user_id,
        remark="",
        items=[
            OrderItemCreate(dish_id=test_dishes[0].dish_id, qty=2, option_item_ids=[]),
            OrderItemCreate(dish_id=test_dishes[0].dish_id, qty=3, option_item_ids=[])
        ]
    )
    
    result = service.create_order(order_dto)
    
    # 验证总价：30*2 + 30*3 = 150
    assert result.total_price == Decimal("150")
    
    # 验证库存扣减：10 - 2 - 3 = 5
    db_session.refresh(test_dishes[0])
    assert test_dishes[0].stock == 5


