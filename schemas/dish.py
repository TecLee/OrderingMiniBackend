from pydantic import BaseModel

from schemas.category import CategoryOut


class DishCreate(BaseModel):
    name: str
    description: str = ""
    price: float = 0.0
    category_id: int


class DishUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    category_id: int | None = None
    image_url: str | None = None


class DishOut(BaseModel):
    id: int
    name: str
    description: str
    price: float
    image_url: str
    category_id: int
    category: CategoryOut | None = None
    created_by: int | None = None

    class Config:
        from_attributes = True
