from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from middleware.admin_auth_middleware import get_current_admin
from models.admin_user import AdminUser
from models.category import Category
from models.dish import Dish
from models.order import Order, OrderItem
from models.user import User
from utils.responses import ok

router = APIRouter(prefix="/api/v1/admin/stats", tags=["后台-统计"])


@router.get("")
def get_stats(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    today = date.today()

    today_orders = db.query(Order).filter(func.date(Order.created_at) == today).count()
    pending_orders = db.query(Order).filter(Order.status == "pending").count()
    completed_orders = db.query(Order).filter(Order.status == "completed").count()
    cancelled_orders = db.query(Order).filter(Order.status == "cancelled").count()
    cooking_orders = db.query(Order).filter(Order.status == "cooking").count()

    # Hourly distribution for today
    hourly_rows = (
        db.query(func.strftime("%H", Order.created_at).label("hour"), func.count().label("count"))
        .filter(func.date(Order.created_at) == today)
        .group_by("hour")
        .order_by("hour")
        .all()
    )
    hourly_distribution = [{"hour": int(r.hour), "count": r.count} for r in hourly_rows]

    # Top 5 dishes
    top_dishes_rows = (
        db.query(OrderItem.dish_name, func.sum(OrderItem.quantity).label("total_qty"))
        .group_by(OrderItem.dish_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )
    top_dishes = [{"dish_name": r.dish_name, "total_quantity": r.total_qty} for r in top_dishes_rows]

    # Status breakdown for today
    status_rows = (
        db.query(Order.status, func.count().label("count"))
        .filter(func.date(Order.created_at) == today)
        .group_by(Order.status)
        .all()
    )
    status_breakdown = {r.status: r.count for r in status_rows}

    total_dishes = db.query(Dish).filter(Dish.is_deleted == False).count()
    total_categories = db.query(Category).count()
    total_users = db.query(User).count()

    return ok({
        "today_orders": today_orders,
        "pending_orders": pending_orders,
        "completed_orders": completed_orders,
        "cancelled_orders": cancelled_orders,
        "cooking_orders": cooking_orders,
        "hourly_distribution": hourly_distribution,
        "top_dishes": top_dishes,
        "status_breakdown": status_breakdown,
        "total_dishes": total_dishes,
        "total_categories": total_categories,
        "total_users": total_users,
    })
