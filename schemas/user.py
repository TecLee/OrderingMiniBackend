from pydantic import BaseModel


class MiniAppLoginRequest(BaseModel):
    code: str


class MockLoginRequest(BaseModel):
    phone: str
    code: str


class PhoneBindRequest(BaseModel):
    encrypted_data: str | None = None
    iv: str | None = None
    phone: str | None = None


class UserOut(BaseModel):
    id: int
    openid: str
    phone: str | None = None
    nickname: str
    avatar_url: str
    role: str
    permissions: str = "dish:query"

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None


class UserAdminUpdate(BaseModel):
    role: str | None = None
    permissions: str | None = None
