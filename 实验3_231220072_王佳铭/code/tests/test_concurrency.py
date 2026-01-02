"""并发测试"""
import pytest
import threading
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base
from app.models.user import User
from app.models.dish import Category, Dish
from app.models.enums import DishStatus
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.order_service import OrderService


# 创建测试用的数据库引擎和会话工厂
test_engine = create_engine(
    "sqlite:///./test_concurrent.db",
    connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def concurrent_db_session():
    """创建并发测试数据库会话"""
    # 创建表
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    yield session
    session.close()
    # 清理
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def test_users(concurrent_db_session):
    """创建两个测试用户"""
    user1 = User(username="user1", is_admin=False)
    user2 = User(username="user2", is_admin=False)
    concurrent_db_session.add_all([user1, user2])
    concurrent_db_session.commit()
    return [user1, user2]


@pytest.fixture
def limited_dish(concurrent_db_session):
    """创建库存有限的测试菜品"""
    category = Category(name="测试分类", sort_order=1)
    concurrent_db_session.add(category)
    concurrent_db_session.flush()
    
    dish = Dish(
        category_id=category.category_id,
        name="限量菜品",
        price=Decimal("50"),
        stock=5,  # 库存仅够一个订单
        status=DishStatus.ON_SHELF
    )
    concurrent_db_session.add(dish)
    concurrent_db_session.commit()
    return dish


def test_concurrent_order_prevent_oversell(concurrent_db_session, test_users, limited_dish):
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
    results = {"success": 0, "failure": 0}
    lock = threading.Lock()
    
    def place_order(user_id, dish_id):
        """下单线程函数"""
        # 每个线程使用独立的数据库会话
        db = TestSessionLocal()
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
            with lock:
                results["success"] += 1
        except ValueError:
            # 库存不足，订单失败
            with lock:
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
    assert results["success"] == 1, f"应该有且仅有一个订单成功，实际成功 {results['success']}"
    assert results["failure"] == 1, f"应该有且仅有一个订单失败，实际失败 {results['failure']}"
    
    # 验证最终库存
    db = TestSessionLocal()
    try:
        final_dish = db.query(Dish).filter(Dish.dish_id == limited_dish.dish_id).first()
        assert final_dish.stock == 0, f"最终库存应为0（防止超卖），实际为 {final_dish.stock}"
    finally:
        db.close()


def test_sequential_orders(concurrent_db_session, test_users, limited_dish):
    """
    顺序下单测试（对比组）
    场景：先后下单两次，第二次应失败
    """
    db = TestSessionLocal()
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
        
        # 验证最终库存（使用当前session重新查询）
        final_dish = db.query(Dish).filter(Dish.dish_id == limited_dish.dish_id).first()
        assert final_dish.stock == 0
    finally:
        db.close()

