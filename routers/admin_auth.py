from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from middleware.admin_auth_middleware import get_current_admin
from models.admin_user import AdminUser
from schemas.admin_user import AdminLoginRequest, AdminUserOut
from services.auth import create_token
from utils.responses import ok, error
from utils.security import verify_password

router = APIRouter(prefix="/api/v1/admin/auth", tags=["后台-认证"])


@router.post("/login")
def admin_login(req: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = db.query(AdminUser).filter(AdminUser.username == req.username).first()
    if not admin or not verify_password(req.password, admin.password_hash):
        return error(40100, "用户名或密码错误")
    if not admin.is_active:
        return error(40300, "账号已禁用")

    token = create_token({"sub": str(admin.id), "role": admin.role})
    return ok({
        "token": token,
        "user": AdminUserOut.model_validate(admin).model_dump(),
    })


@router.get("/me")
def get_me(admin: AdminUser = Depends(get_current_admin)):
    return ok(AdminUserOut.model_validate(admin).model_dump())
