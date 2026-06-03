from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from database import get_db
from models.admin_user import AdminUser
from services.auth import decode_token


def get_current_admin(
    authorization: str = Header(...),
    db: Session = Depends(get_db),
) -> AdminUser:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    token = authorization[7:]
    try:
        payload = decode_token(token)
        admin_id = payload.get("sub")
        if admin_id is None:
            raise HTTPException(status_code=401, detail="令牌无效")
    except Exception:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")

    admin = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
    if not admin or not admin.is_active:
        raise HTTPException(status_code=401, detail="管理员不存在或已禁用")
    return admin
