from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth_middleware import get_current_user
from models.cart_item import CartItem
from models.dish import Dish
from models.user import User
from schemas.cart import CartItemCreate, CartItemUpdate, CartItemOut
from utils.responses import ok, error

router = APIRouter(prefix="/api/v1/miniapp/cart", tags=["小程序-购物车"])


@router.get("")
def list_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.dish.has(Dish.is_deleted == False),
    ).all()
    data = [CartItemOut.model_validate(item).model_dump() for item in items]
    return ok({"items": data, "total_count": len(data)})


@router.post("")
def add_to_cart(
    req: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dish = db.query(Dish).filter(Dish.id == req.dish_id, Dish.is_deleted == False).first()
    if not dish:
        return error(40400, "菜品不存在")

    existing = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.dish_id == req.dish_id,
    ).first()

    if existing:
        existing.quantity += req.quantity
        db.commit()
        db.refresh(existing)
        return ok(CartItemOut.model_validate(existing).model_dump())
    else:
        item = CartItem(user_id=current_user.id, dish_id=req.dish_id, quantity=req.quantity)
        db.add(item)
        db.commit()
        db.refresh(item)
        return ok(CartItemOut.model_validate(item).model_dump())


@router.put("/{item_id}")
def update_cart_item(
    item_id: int,
    req: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.user_id == current_user.id,
    ).first()
    if not item:
        return error(40400, "购物车项不存在")
    if req.quantity <= 0:
        db.delete(item)
        db.commit()
        return ok(message="已移除")
    item.quantity = req.quantity
    db.commit()
    db.refresh(item)
    return ok(CartItemOut.model_validate(item).model_dump())


@router.delete("/{item_id}")
def remove_cart_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.user_id == current_user.id,
    ).first()
    if not item:
        return error(40400, "购物车项不存在")
    db.delete(item)
    db.commit()
    return ok(message="已移除")
