from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from middleware.auth_middleware import get_current_user
from models.user import User
from schemas.user import (
    MiniAppLoginRequest,
    MockLoginRequest,
    PhoneBindRequest,
    UserOut,
    UserUpdate,
)
from services.auth import create_token
from utils.responses import ok, error

router = APIRouter(prefix="/api/v1/miniapp/auth", tags=["小程序-认证"])


@router.post("/login")
def miniapp_login(req: MiniAppLoginRequest, db: Session = Depends(get_db)):
    if settings.MOCK_AUTH:
        return error(40001, "本地测试请使用 /auth/mock-login 接口")

    # Real WeChat login: call code2Session, get openid
    # For now, placeholder — this path is not used in local dev
    return error(50000, "暂不支持真实微信登录")


@router.post("/mock-login")
def mock_login(req: MockLoginRequest, db: Session = Depends(get_db)):
    if not settings.MOCK_AUTH:
        return error(40001, "Mock登录未启用")

    if req.code != settings.MOCK_VERIFY_CODE:
        return error(40001, "验证码错误")

    # Find or create user by phone
    user = db.query(User).filter(User.phone == req.phone).first()
    if not user:
        user = User(
            openid=f"mock_{req.phone}",
            phone=req.phone,
            nickname=req.phone,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_token({"sub": str(user.id), "phone": user.phone or ""})
    return ok({
        "token": token,
        "user": UserOut.model_validate(user),
    })


@router.post("/phone")
def bind_phone(
    req: PhoneBindRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    phone = req.phone
    if not phone and settings.MOCK_AUTH:
        return error(40001, "手机号不能为空")

    current_user.phone = phone
    db.commit()
    db.refresh(current_user)
    return ok({"phone": phone})
