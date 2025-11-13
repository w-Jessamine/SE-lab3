"""后台管理路由"""
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.dish import DishCreate, DishResponse
from app.schemas.order import OrderResponse, OrderDetailResponse
from app.services.menu_service import MenuService
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/admin", tags=["后台管理"])

class BatchAdjustItem(BaseModel):
    dish_id: int
    delta: int

class CategoryCU(BaseModel):
    name: str
    sort_order: int = 0

class DishUpdateDTO(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    stock: Optional[int] = None
    status: Optional[str] = None
    category_id: Optional[int] = None


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
    status: str = Body(..., embed=True, pattern="^(OnShelf|OffShelf)$"),
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

@router.post("/inventory/adjust-batch", status_code=204)
def adjust_inventory_batch(items: list[BatchAdjustItem], db: Session = Depends(get_db)):
    """
    批量调整库存
    入参：[{dish_id:int, delta:int}, ...]
    """
    service = InventoryService(db)
    try:
        service.adjust_stock_batch([(i.dish_id, i.delta) for i in items])
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

@router.get("/orders/{order_id}", response_model=OrderDetailResponse)
def get_order_detail_admin(order_id: int, db: Session = Depends(get_db)):
    """
    管理员查询订单详情（含明细与选项）
    """
    service = OrderService(db)
    order = service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order


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

@router.post("/orders/{order_id}/cancel", status_code=204)
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    """
    取消订单
    前置条件：status in [Created, Submitted]
    后置条件：status = Cancelled
    """
    service = OrderService(db)
    try:
        service.cancel_order(order_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ------- Category CRUD -------
@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    return MenuService(db).get_all_categories()

@router.post("/categories")
def create_category(dto: CategoryCU, db: Session = Depends(get_db)):
    svc = MenuService(db)
    cat = svc.create_category(dto.name, dto.sort_order)
    return {"category_id": cat.category_id, "name": cat.name, "sort_order": cat.sort_order}

@router.patch("/categories/{category_id}")
def update_category(category_id: int, dto: CategoryCU, db: Session = Depends(get_db)):
    svc = MenuService(db)
    cat = svc.update_category(category_id, dto.name, dto.sort_order)
    return {"category_id": cat.category_id, "name": cat.name, "sort_order": cat.sort_order}

@router.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    MenuService(db).delete_category(category_id)
    return {}

@router.patch("/dishes/{dish_id}")
def update_dish(dish_id: int, dto: DishUpdateDTO, db: Session = Depends(get_db)):
    svc = MenuService(db)
    try:
        dish = svc.update_dish(
            dish_id,
            name=dto.name,
            price=dto.price,
            image_url=dto.image_url,
            stock=dto.stock,
            status=dto.status,
            category_id=dto.category_id,
        )
        return DishResponse.model_validate(dish)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/dishes/{dish_id}", status_code=204)
def delete_dish(dish_id: int, db: Session = Depends(get_db)):
    MenuService(db).delete_dish(dish_id)
    return {}

