"""订单路由"""
from fastapi import APIRouter, Depends, Path, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.order import OrderCreate, OrderResponse, OrderDetailResponse
from app.services.order_service import OrderService

router = APIRouter(prefix="/api", tags=["订单"])


@router.post("/orders", response_model=OrderResponse, status_code=201)
def create_order(dto: OrderCreate, db: Session = Depends(get_db)):
    """
    创建订单
    入参：OrderCreate (user_id, items, remark)
    逻辑：调用 OrderService.create_order()
    返回：{"order_id": int, "total_price": Decimal, "status": "Submitted"}
    异常：400 - 菜品下架/库存不足
    """
    service = OrderService(db)
    try:
        return service.create_order(dto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orders/{order_id}", response_model=OrderDetailResponse)
def get_order(order_id: int = Path(..., description="订单ID"), db: Session = Depends(get_db)):
    """
    查询订单详情
    返回：订单完整信息（含订单项）
    """
    service = OrderService(db)
    order = service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order


@router.post("/orders/{order_id}/cancel", status_code=204)
def cancel_order(order_id: int = Path(..., description="订单ID"), db: Session = Depends(get_db)):
    """
    取消订单
    前置条件：订单状态允许取消
    后置条件：状态变更为 Cancelled
    """
    service = OrderService(db)
    try:
        service.cancel_order(order_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

