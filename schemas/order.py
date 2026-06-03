from datetime import datetime

from pydantic import BaseModel


class OrderItemCreate(BaseModel):
    dish_id: int
    quantity: int = 1
    note: str = ""


class OrderCreate(BaseModel):
    note: str = ""
    items: list[OrderItemCreate]


class OrderItemOut(BaseModel):
    id: int
    dish_id: int
    dish_name: str
    quantity: int
    unit_price: float
    note: str

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    user_id: int
    status: str
    total_amount: float
    note: str
    items: list[OrderItemOut] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: str
