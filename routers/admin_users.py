from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from middleware.admin_auth_middleware import get_current_admin
from models.admin_user import AdminUser
from models.user import User
from schemas.common import PaginatedData
from schemas.user import UserAdminUpdate, UserOut
from utils.responses import ok

router = APIRouter(prefix="/api/v1/admin/users", tags=["后台-用户管理"])


@router.get("")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User).order_by(User.id.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return ok({
        "items": [UserOut.model_validate(u).model_dump() for u in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": page * page_size < total,
    })


@router.put("/{user_id}")
def update_user(
    user_id: int,
    body: UserAdminUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if body.role is not None:
        user.role = body.role
    if body.permissions is not None:
        user.permissions = body.permissions

    db.commit()
    db.refresh(user)
    return ok(UserOut.model_validate(user).model_dump())
