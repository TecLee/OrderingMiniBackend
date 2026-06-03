from fastapi import APIRouter, Depends, UploadFile, File

from config import settings
from middleware.auth_middleware import get_current_user
from utils.image_utils import save_upload_image
from utils.responses import ok, error

router = APIRouter(prefix="/api/v1/miniapp", tags=["小程序-上传"])


@router.post("/upload")
def upload_image(
    image: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    if not image.filename:
        return error(40001, "请选择文件")

    url = save_upload_image(image, settings.UPLOAD_DIR)
    return ok({"url": url})
