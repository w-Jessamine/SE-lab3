"""并发测试"""
import pytest
import threading
from decimal import Decimal
from app.models.user import User
from app.models.dish import Category, Dish
from app.models.enums import DishStatus
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.order_service import OrderService
from app.db import SessionLocal


@pytest.fixture
def test_users(db_session):
    """创建两个测试用户"""
    user1 = User(username="user1", is_admin=False)
    user2 = User(username="user2", is_admin=False)
    db_session.add_all([user1, user2])
    db_session.commit()
    return [user1, user2]


@pytest.fixture
def limited_dish(db_session):
    """创建库存有限的测试菜品"""
    category = Category(name="测试分类", sort_order=1)
    db_session.add(category)
    db_session.flush()
    
    dish = Dish(
        category_id=category.category_id,
        name="限量菜品",
        price=Decimal("50"),
        stock=5,  # 库存仅够一个订单
        status=DishStatus.ON_SHELF
    )
    db_session.add(dish)
    db_session.commit()
    return dish


def test_concurrent_order_prevent_oversell(test_users, limited_dish):
    """
    并发超卖测试
    场景：
      - 菜品库存 = 5
      - 用户1 下单 5 份
      - 用户2 下单 5 份
      - 并发提交
    预期：
      - 一个订单成功，一个失败
      - 最终库存 = 0
    """
    results = {"success": 0, "failure": 0, "final_stock": None}
    
    def place_order(user_id, dish_id):
        """下单线程函数"""
        # 每个线程使用独立的数据库会话
        db = SessionLocal()
        try:
            service = OrderService(db)
            order_dto = OrderCreate(
                user_id=user_id,
                remark="",
                items=[
                    OrderItemCreate(dish_id=dish_id, qty=5, option_item_ids=[])
                ]
            )
            
            # 尝试创建订单
            service.create_order(order_dto)
            results["success"] += 1
        except ValueError as e:
            # 库存不足，订单失败
            results["failure"] += 1
        finally:
            db.close()
    
    # 创建两个线程并发下单
    thread1 = threading.Thread(target=place_order, args=(test_users[0].user_id, limited_dish.dish_id))
    thread2 = threading.Thread(target=place_order, args=(test_users[1].user_id, limited_dish.dish_id))
    
    # 启动线程
    thread1.start()
    thread2.start()
    
    # 等待线程结束
    thread1.join()
    thread2.join()
    
    # 验证结果
    assert results["success"] == 1, "应该有且仅有一个订单成功"
    assert results["failure"] == 1, "应该有且仅有一个订单失败"
    
    # 验证最终库存
    db = SessionLocal()
    try:
        final_dish = db.query(Dish).filter(Dish.dish_id == limited_dish.dish_id).first()
        assert final_dish.stock == 0, "最终库存应为0（防止超卖）"
    finally:
        db.close()


def test_sequential_orders(test_users, limited_dish):
    """
    顺序下单测试（对比组）
    场景：先后下单两次，第二次应失败
    """
    db = SessionLocal()
    try:
        service = OrderService(db)
        
        # 第一个订单：成功
        order1 = OrderCreate(
            user_id=test_users[0].user_id,
            remark="",
            items=[OrderItemCreate(dish_id=limited_dish.dish_id, qty=5, option_item_ids=[])]
        )
        result1 = service.create_order(order1)
        assert result1.order_id > 0
        
        # 第二个订单：应该失败（库存不足）
        order2 = OrderCreate(
            user_id=test_users[1].user_id,
            remark="",
            items=[OrderItemCreate(dish_id=limited_dish.dish_id, qty=1, option_item_ids=[])]
        )
        
        with pytest.raises(ValueError, match="库存不足"):
            service.create_order(order2)
        
        # 验证最终库存
        db.refresh(limited_dish)
        assert limited_dish.stock == 0
    finally:
        db.close()

