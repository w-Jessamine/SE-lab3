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


def test_get_stock(db_session, sample_dish):
    """测试查询库存"""
    service = InventoryService(db_session)
    stock = service.get_stock(sample_dish.dish_id)
    
    assert stock == sample_dish.stock

