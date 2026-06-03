from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth_middleware import get_current_user
from models.cart_item import CartItem
from models.dish import Dish
from models.order import Order, OrderItem
from models.user import User
from schemas.common import PaginatedData
from schemas.order import OrderCreate, OrderOut
from utils.responses import ok, error

router = APIRouter(prefix="/api/v1/miniapp/orders", tags=["小程序-订单"])


@router.post("")
def place_order(
    req: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not req.items:
        return error(40000, "订单不能为空")

    total_amount = 0.0
    order_items = []

    for item in req.items:
        dish = db.query(Dish).filter(Dish.id == item.dish_id, Dish.is_deleted == False).first()
        if not dish:
            return error(40400, f"菜品不存在 (id={item.dish_id})")
        total_amount += dish.price * item.quantity
        order_items.append(OrderItem(
            dish_id=dish.id,
            dish_name=dish.name,
            quantity=item.quantity,
            unit_price=dish.price,
            note=item.note,
        ))

    order = Order(
        user_id=current_user.id,
        status="pending",
        total_amount=round(total_amount, 2),
        note=req.note,
        items=order_items,
    )
    db.add(order)

    # Clear cart after placing order
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()

    db.commit()
    db.refresh(order)
    # Broadcast new order to kitchen boards
    _notify_new_order(order)
    return ok(OrderOut.model_validate(order).model_dump())


def _notify_new_order(order: Order):
    from utils.ws_manager import kitchen_ws
    kitchen_ws.notify("new_order", {
        "order_id": order.id,
        "total_amount": order.total_amount,
        "status": order.status,
    })


@router.get("")
def list_my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.id.desc())
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id,
    ).first()
    if not order:
        return error(40400, "订单不存在")
    return ok(OrderOut.model_validate(order).model_dump())
