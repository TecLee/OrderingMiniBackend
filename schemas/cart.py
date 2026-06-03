from pydantic import BaseModel

from schemas.dish import DishOut


class CartItemCreate(BaseModel):
    dish_id: int
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemOut(BaseModel):
    id: int
    user_id: int
    dish_id: int
    quantity: int
    dish: DishOut | None = None

    class Config:
        from_attributes = True
