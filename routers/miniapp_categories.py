from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.category import Category
from schemas.category import CategoryOut
from utils.responses import ok

router = APIRouter(prefix="/api/v1/miniapp/categories", tags=["小程序-分类"])


@router.get("")
def list_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.name).all()
    return ok([CategoryOut.model_validate(c).model_dump() for c in categories])
