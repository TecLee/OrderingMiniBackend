"""Shared image processing — resize & compress uploads."""
import os
import uuid
from io import BytesIO

from fastapi import UploadFile
from PIL import Image

MAX_SIZE = (800, 800)
JPEG_QUALITY = 80


def save_upload_image(image: UploadFile, upload_dir: str) -> str:
    """Save and compress uploaded image, return relative URL path."""
    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(upload_dir, filename)

    try:
        img = Image.open(image.file)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail(MAX_SIZE, Image.LANCZOS)
        img.save(filepath, "JPEG", quality=JPEG_QUALITY, optimize=True)
    except Exception:
        # Fallback: raw save
        ext = os.path.splitext(image.filename or "img.jpg")[1] or ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, "wb") as f:
            f.write(image.file.read())

    return f"/uploads/{filename}"
