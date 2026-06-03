from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth_middleware import get_current_user
from models.dish import Dish
from models.user import User
from schemas.common import PaginatedData
from schemas.dish import DishOut
from utils.responses import ok, error
from utils.pagination import paginate

import os, uuid
from config import settings

router = APIRouter(prefix="/api/v1/miniapp/dishes", tags=["小程序-菜品"])


@router.get("")
def list_dishes(
    category_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    query = db.query(Dish).filter(Dish.is_deleted == False)
    if category_id:
        query = query.filter(Dish.category_id == category_id)
    query = query.order_by(Dish.id.desc())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return ok(PaginatedData(
        items=[DishOut.model_validate(d).model_dump() for d in items],
        total=total,
        page=page,
        page_size=page_size,
        has_more=page * page_size < total,
    ))


@router.get("/{dish_id}")
def get_dish(dish_id: int, db: Session = Depends(get_db)):
    dish = db.query(Dish).filter(Dish.id == dish_id, Dish.is_deleted == False).first()
    if not dish:
        return error(40400, "菜品不存在")
    return ok(DishOut.model_validate(dish))


@router.post("")
def create_dish(
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(0),
    category_id: int = Form(...),
    image: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    image_url = ""
    if image and image.filename:
        from utils.image_utils import save_upload_image
        image_url = save_upload_image(image, settings.UPLOAD_DIR)

    dish = Dish(
        name=name,
        description=description,
        price=price,
        category_id=category_id,
        image_url=image_url,
        created_by=current_user.id,
    )
    db.add(dish)
    db.commit()
    db.refresh(dish)
    return ok(DishOut.model_validate(dish).model_dump())


@router.put("/{dish_id}")
def update_dish(
    dish_id: int,
    name: str | None = Form(None),
    description: str | None = Form(None),
    price: float | None = Form(None),
    category_id: int | None = Form(None),
    image: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dish = db.query(Dish).filter(Dish.id == dish_id, Dish.is_deleted == False).first()
    if not dish:
        return error(40400, "菜品不存在")

    if name is not None:
        dish.name = name
    if description is not None:
        dish.description = description
    if price is not None:
        dish.price = price
    if category_id is not None:
        dish.category_id = category_id
    if image and image.filename:
        from utils.image_utils import save_upload_image
        dish.image_url = save_upload_image(image, settings.UPLOAD_DIR)

    db.commit()
    db.refresh(dish)
    return ok(DishOut.model_validate(dish).model_dump())


@router.delete("/{dish_id}")
def delete_dish(
    dish_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dish = db.query(Dish).filter(Dish.id == dish_id, Dish.is_deleted == False).first()
    if not dish:
        return error(40400, "菜品不存在")
    dish.is_deleted = True
    db.commit()
    return ok(message="删除成功")
