"""库存服务测试"""
import pytest
from decimal import Decimal
from app.models.user import User
from app.models.dish import Category, Dish
from app.models.enums import DishStatus
from app.services.inventory_service import InventoryService


@pytest.fixture
def sample_dish(db_session):
    """创建测试菜品"""
    category = Category(name="测试分类", sort_order=1)
    db_session.add(category)
    db_session.flush()
    
    dish = Dish(
        category_id=category.category_id,
        name="测试菜品",
        price=Decimal("30"),
        stock=10,
        status=DishStatus.ON_SHELF
    )
    db_session.add(dish)
    db_session.commit()
    return dish


@pytest.fixture
def multiple_dishes(db_session):
    """创建多个测试菜品用于批量测试"""
    category = Category(name="测试分类", sort_order=1)
    db_session.add(category)
    db_session.flush()
    
    dishes = []
    for i in range(3):
        dish = Dish(
            category_id=category.category_id,
            name=f"测试菜品{i+1}",
            price=Decimal("30"),
            stock=10,
            status=DishStatus.ON_SHELF
        )
        db_session.add(dish)
        dishes.append(dish)
    db_session.commit()
    return dishes


def test_check_stock_sufficient(db_session, sample_dish):
    """测试库存充足时返回 True"""
    service = InventoryService(db_session)
    assert service.check_stock(sample_dish.dish_id, 5) is True


def test_check_stock_insufficient(db_session, sample_dish):
    """测试库存不足时返回 False"""
    service = InventoryService(db_session)
    assert service.check_stock(sample_dish.dish_id, 15) is False


def test_check_stock_off_shelf(db_session, sample_dish):
    """测试下架菜品返回 False"""
    sample_dish.status = DishStatus.OFF_SHELF
    db_session.commit()
    
    service = InventoryService(db_session)
    assert service.check_stock(sample_dish.dish_id, 5) is False


def test_check_stock_nonexistent_dish(db_session):
    """测试不存在的菜品返回 False"""
    service = InventoryService(db_session)
    assert service.check_stock(9999, 1) is False


def test_deduct_stock_success(db_session, sample_dish):
    """测试扣减库存成功"""
    service = InventoryService(db_session)
    original_stock = sample_dish.stock
    
    service.deduct_stock(sample_dish.dish_id, 3)
    db_session.refresh(sample_dish)
    
    assert sample_dish.stock == original_stock - 3


def test_deduct_stock_failure(db_session, sample_dish):
    """测试扣减库存失败（库存不足）"""
    service = InventoryService(db_session)
    
    with pytest.raises(ValueError, match="库存不足"):
        service.deduct_stock(sample_dish.dish_id, 20)


def test_deduct_stock_nonexistent_dish(db_session):
    """测试扣减不存在的菜品库存抛出异常"""
    service = InventoryService(db_session)
    
    with pytest.raises(ValueError, match="菜品不存在"):
        service.deduct_stock(9999, 1)


def test_deduct_stock_off_shelf_dish(db_session, sample_dish):
    """测试扣减下架菜品库存抛出异常"""
    sample_dish.status = DishStatus.OFF_SHELF
    db_session.commit()
    
    service = InventoryService(db_session)
    
    with pytest.raises(ValueError, match="菜品不可用"):
        service.deduct_stock(sample_dish.dish_id, 1)


def test_adjust_stock_positive(db_session, sample_dish):
    """测试增加库存"""
    service = InventoryService(db_session)
    original_stock = sample_dish.stock
    
    service.adjust_stock(sample_dish.dish_id, 5)
    db_session.refresh(sample_dish)
    
    assert sample_dish.stock == original_stock + 5


def test_adjust_stock_negative(db_session, sample_dish):
    """测试减少库存（不低于0）"""
    service = InventoryService(db_session)
    original_stock = sample_dish.stock
    
    service.adjust_stock(sample_dish.dish_id, -5)
    db_session.refresh(sample_dish)
    
    assert sample_dish.stock == original_stock - 5


def test_adjust_stock_negative_failure(db_session, sample_dish):
    """测试减少库存失败（会导致负数）"""
    service = InventoryService(db_session)
    
    with pytest.raises(ValueError, match="库存不足"):
        service.adjust_stock(sample_dish.dish_id, -20)


def test_adjust_stock_nonexistent_dish(db_session):
    """测试调整不存在的菜品库存抛出异常"""
    service = InventoryService(db_session)
    
    with pytest.raises(ValueError, match="菜品不存在"):
        service.adjust_stock(9999, 5)


def test_get_stock(db_session, sample_dish):
    """测试查询库存"""
    service = InventoryService(db_session)
    stock = service.get_stock(sample_dish.dish_id)
    
    assert stock == sample_dish.stock


def test_get_stock_nonexistent_dish(db_session):
    """测试查询不存在的菜品库存抛出异常"""
    service = InventoryService(db_session)
    
    with pytest.raises(ValueError, match="菜品不存在"):
        service.get_stock(9999)


def test_adjust_stock_batch_success(db_session, multiple_dishes):
    """测试批量调整库存成功"""
    service = InventoryService(db_session)
    
    updates = [
        (multiple_dishes[0].dish_id, 5),   # 增加5
        (multiple_dishes[1].dish_id, -3),  # 减少3
        (multiple_dishes[2].dish_id, 10),  # 增加10
    ]
    
    service.adjust_stock_batch(updates)
    
    db_session.refresh(multiple_dishes[0])
    db_session.refresh(multiple_dishes[1])
    db_session.refresh(multiple_dishes[2])
    
    assert multiple_dishes[0].stock == 15  # 10 + 5
    assert multiple_dishes[1].stock == 7   # 10 - 3
    assert multiple_dishes[2].stock == 20  # 10 + 10


def test_adjust_stock_batch_rollback_on_failure(db_session, multiple_dishes):
    """测试批量调整库存失败时回滚"""
    service = InventoryService(db_session)
    
    # 第三个更新会失败（库存不足）
    updates = [
        (multiple_dishes[0].dish_id, 5),
        (multiple_dishes[1].dish_id, -3),
        (multiple_dishes[2].dish_id, -20),  # 会失败
    ]
    
    with pytest.raises(ValueError, match="库存不足"):
        service.adjust_stock_batch(updates)
    
    # 验证所有更改都被回滚
    db_session.refresh(multiple_dishes[0])
    db_session.refresh(multiple_dishes[1])
    db_session.refresh(multiple_dishes[2])
    
    assert multiple_dishes[0].stock == 10  # 回滚
    assert multiple_dishes[1].stock == 10  # 回滚
    assert multiple_dishes[2].stock == 10  # 未变


def test_adjust_stock_batch_nonexistent_dish(db_session, multiple_dishes):
    """测试批量调整包含不存在的菜品时回滚"""
    service = InventoryService(db_session)
    
    updates = [
        (multiple_dishes[0].dish_id, 5),
        (9999, 10),  # 不存在的菜品
    ]
    
    with pytest.raises(ValueError, match="菜品不存在"):
        service.adjust_stock_batch(updates)
    
    # 验证回滚
    db_session.refresh(multiple_dishes[0])
    assert multiple_dishes[0].stock == 10


