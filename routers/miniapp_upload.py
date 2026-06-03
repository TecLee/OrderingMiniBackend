import os
import uuid

from fastapi import APIRouter, Depends, UploadFile, File

from config import settings
from middleware.auth_middleware import get_current_user
from utils.responses import ok, error

router = APIRouter(prefix="/api/v1/miniapp", tags=["小程序-上传"])


@router.post("/upload")
def upload_image(
    image: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    if not image.filename:
        return error(40001, "请选择文件")

    ext = os.path.splitext(image.filename)[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(image.file.read())

    return ok({"url": f"/uploads/{filename}"})
