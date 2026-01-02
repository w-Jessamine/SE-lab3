"""菜品浏览路由"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.dish import CategoryResponse, DishResponse
from app.schemas.option import OptionGroupResponse
from app.services.menu_service import MenuService
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/api", tags=["菜品"])


@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """
    获取所有分类
    返回：按 sort_order 排序的分类列表
    """
    service = MenuService(db)
    return service.get_all_categories()


@router.get("/dishes", response_model=List[DishResponse])
def get_dishes(
    category_id: Optional[int] = Query(None, description="分类ID（可选）"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    分页查询菜品
    参数：
      - category_id: 可选，按分类筛选
      - page: 页码
      - size: 每页数量
    返回：菜品列表
    """
    service = MenuService(db)
    return service.get_dishes_by_category(category_id, page, size)


@router.get("/dishes/{dish_id}", response_model=DishResponse)
def get_dish_detail(dish_id: int, db: Session = Depends(get_db)):
    """
    获取菜品详情
    返回：菜品信息
    """
    service = MenuService(db)
    dish = service.get_dish_detail(dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="菜品不存在")
    return DishResponse.model_validate(dish)


@router.get("/dishes/{dish_id}/options", response_model=List[OptionGroupResponse])
def get_dish_options(dish_id: int, db: Session = Depends(get_db)):
    """
    获取菜品的口味选项
    返回：口味组列表
    """
    service = MenuService(db)
    dish = service.get_dish_detail(dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="菜品不存在")
    
    return [OptionGroupResponse.model_validate(group) for group in dish.option_groups]


@router.get("/stock", response_model=dict)
def get_stock(dish_id: int = Query(..., description="菜品ID"), db: Session = Depends(get_db)):
    """
    查询菜品库存
    参数：dish_id
    返回：{"dish_id": int, "stock": int}
    """
    service = InventoryService(db)
    try:
        stock = service.get_stock(dish_id)
        return {"dish_id": dish_id, "stock": stock}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

