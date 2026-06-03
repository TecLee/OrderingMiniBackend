from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from middleware.admin_auth_middleware import get_current_admin
from models.admin_user import AdminUser
from models.order import Order
from schemas.common import PaginatedData
from schemas.order import OrderOut, OrderStatusUpdate
from utils.responses import ok, error

router = APIRouter(prefix="/api/v1/admin/orders", tags=["后台-订单管理"])

ALLOWED_TRANSITIONS = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["cooking", "cancelled"],
    "cooking": ["completed"],
    "completed": [],
    "cancelled": [],
}


@router.get("")
def list_orders(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Order).order_by(Order.id.desc())
    if status:
        query = query.filter(Order.status == status)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return ok(PaginatedData(
        items=[OrderOut.model_validate(o).model_dump() for o in items],
        total=total,
        page=page,
        page_size=page_size,
        has_more=page * page_size < total,
    ))


@router.get("/{order_id}")
def get_order_detail(
    order_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return error(40400, "订单不存在")
    return ok(OrderOut.model_validate(order).model_dump())


@router.put("/{order_id}/status")
def update_order_status(
    order_id: int,
    req: OrderStatusUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return error(40400, "订单不存在")

    allowed = ALLOWED_TRANSITIONS.get(order.status, [])
    if req.status not in allowed:
        return error(40000, f"不能从 {order.status} 变更为 {req.status}")

    order.status = req.status
    db.commit()
    db.refresh(order)
    # Broadcast to kitchen boards
    _notify_kitchen(order)
    return ok(OrderOut.model_validate(order).model_dump())


def _notify_kitchen(order: Order):
    """Broadcast order update to kitchen WebSocket clients."""
    from utils.ws_manager import kitchen_ws
    kitchen_ws.notify("order_update", {
        "order_id": order.id,
        "status": order.status,
    })
