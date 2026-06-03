from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from middleware.admin_auth_middleware import get_current_admin
from models.admin_user import AdminUser
from models.category import Category
from models.dish import Dish
from schemas.category import CategoryCreate, CategoryUpdate, CategoryOut
from utils.responses import ok, error

router = APIRouter(prefix="/api/v1/admin/categories", tags=["后台-分类"])


@router.get("")
def list_categories(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    categories = db.query(Category).order_by(Category.name).all()
    return ok([CategoryOut.model_validate(c).model_dump() for c in categories])


@router.post("")
def create_category(
    req: CategoryCreate,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    existing = db.query(Category).filter(Category.name == req.name).first()
    if existing:
        return error(40001, "分类名称已存在")
    cat = Category(name=req.name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return ok(CategoryOut.model_validate(cat).model_dump())


@router.put("/{cat_id}")
def update_category(
    cat_id: int,
    req: CategoryUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        return error(40400, "分类不存在")
    if req.name is not None:
        cat.name = req.name
    db.commit()
    db.refresh(cat)
    return ok(CategoryOut.model_validate(cat).model_dump())


@router.delete("/{cat_id}")
def delete_category(
    cat_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        return error(40400, "分类不存在")
    # Check if dishes reference this category
    dish_count = db.query(Dish).filter(Dish.category_id == cat_id, Dish.is_deleted == False).count()
    if dish_count > 0:
        return error(40001, f"该分类下有 {dish_count} 个菜品，无法删除")
    db.delete(cat)
    db.commit()
    return ok(message="删除成功")
