"""Utils module"""
from fastapi import UploadFile
from pathlib import Path


def to_snake_case(s: str) -> str:
    try:
        return ''.join(['_' + ch.lower() if i > 0 and ch.isupper() else ch.lower()
                        for i, ch in enumerate(s)])
    except:
        return s


def validate_image(file: UploadFile) -> bool:
    """Check if an uploaded file is a valid image."""
    try:
        allowed_types = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
        if file.content_type not in allowed_types:
            return False
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        file_extension = Path(file.filename or "").suffix.lower()
        if file_extension not in allowed_extensions:
            return False
        return True
    except:
        return False
