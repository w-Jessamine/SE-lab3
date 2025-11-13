"""后台管理路由"""
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.dish import DishCreate, DishResponse
from app.schemas.order import OrderResponse
from app.services.menu_service import MenuService
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService

router = APIRouter(prefix="/api/admin", tags=["后台管理"])


@router.post("/dishes", response_model=DishResponse, status_code=201)
def create_dish(dto: DishCreate, db: Session = Depends(get_db)):
    """
    创建菜品
    权限：管理员（本演示暂不验证权限）
    """
    service = MenuService(db)
    try:
        dish = service.create_dish(
            category_id=dto.category_id,
            name=dto.name,
            price=float(dto.price),
            image_url=dto.image_url,
            stock=dto.stock,
            status=dto.status
        )
        return DishResponse.model_validate(dish)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/dishes/{dish_id}/status", response_model=DishResponse)
def update_dish_status(
    dish_id: int,
    status: str = Body(..., embed=True, regex="^(OnShelf|OffShelf)$"),
    db: Session = Depends(get_db)
):
    """
    上下架菜品
    参数：dish_id, status ("OnShelf" | "OffShelf")
    """
    service = MenuService(db)
    try:
        dish = service.update_dish_status(dish_id, status)
        return DishResponse.model_validate(dish)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/inventory/adjust", status_code=204)
def adjust_inventory(
    dish_id: int = Query(..., description="菜品ID"),
    delta: int = Query(..., description="调整量（可正可负）"),
    db: Session = Depends(get_db)
):
    """
    调整库存
    参数：dish_id, delta (可正可负)
    契约：调用 InventoryService.adjust_stock()
    """
    service = InventoryService(db)
    try:
        service.adjust_stock(dish_id, delta)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orders", response_model=List[OrderResponse])
def list_all_orders(
    status: Optional[str] = Query(None, description="订单状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    查看所有订单（后台管理）
    参数：可选按 status 筛选
    """
    service = OrderService(db)
    return service.list_orders(user_id=None, status=status, page=page, size=size)


@router.post("/orders/{order_id}/complete", status_code=204)
def complete_order(order_id: int, db: Session = Depends(get_db)):
    """
    完成订单
    前置条件：status == Submitted
    后置条件：status = Completed
    """
    service = OrderService(db)
    try:
        service.complete_order(order_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

