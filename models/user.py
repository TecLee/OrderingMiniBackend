from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    openid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, default="")
    phone: Mapped[str | None] = mapped_column(String(20), default="")
    nickname: Mapped[str] = mapped_column(String(64), default="")
    avatar_url: Mapped[str] = mapped_column(String(512), default="")
    role: Mapped[str] = mapped_column(String(20), default="user")
    permissions: Mapped[str] = mapped_column(String(512), default="dish:query")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
