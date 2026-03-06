import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from typing import TypeVar
from app.utils import to_snake_case, validate_image

ORMModel = TypeVar("ORMModel")


class FileService:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.brands_dir = self.upload_dir / "brands"
        self.interesting_products_dir = self.upload_dir / "interesting_products"
        self.product_categories_dir = self.upload_dir / "product_categories"
        self.partners_dir = self.upload_dir / "partners"

        self.brands_dir.mkdir(parents=True, exist_ok=True)
        self.interesting_products_dir.mkdir(parents=True, exist_ok=True)
        self.product_categories_dir.mkdir(parents=True, exist_ok=True)
        self.partners_dir.mkdir(parents=True, exist_ok=True)

    def save_image(self, obj: ORMModel, upload_dir: str, file: UploadFile) -> str:
        """
        Save any image in JPG, PNG or WebP format and Maximum size: 5MB.

        Args:
            obj (ORMModel): the object to which you wish to attach the file 
            upload_dir (str): the directory where you want to place the file
            file (UploadFile): the Uploaded file

        Returns:
            str: Relative path of the saved file

        Raises:
            HTTPException: If the file is not valid
        """
        if not validate_image(file):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Use JPG, PNG or WebP."
            )
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File is too large. Maximum size: 5MB."
            )

        pattern = f"{to_snake_case(obj.__class__.__name__)}_{obj.id}"
        file_extension = Path(file.filename or "").suffix.lower()
        filename = f"{pattern}_{uuid.uuid4().hex}{file_extension}"
        file_path = upload_dir / filename

        try:
            self.delete_image_by_pattern(pattern, upload_dir)

            with open(file_path, "wb") as buffer:
                content = file.file.read()
                buffer.write(content)

            return f"{upload_dir}/{filename}"

        except Exception as e:
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=500,
                detail=f"Error saving file: {str(e)}"
            )

    def delete_image_by_pattern(self, pattern: str, upload_dir: str) -> bool:
        """
        Delete the old image by pattern.

        Args:
            pattern (str): the base filename of the image 
            upload_dir (str): the directory 

        Returns:
            boolean: True if successfully deleted otherwise False
        """
        try:
            for file_path in upload_dir.glob(f"{pattern}_*"):
                file_path.unlink()
            return True
        except Exception:
            return False

    def delete_image(self, img_path: str) -> bool:
        """
        Delete an image by path.

        Args:
            img_path (str): the full path of the image 

        Returns:
            boolean: True if successfully deleted otherwise False
        """
        try:
            full_path = Path(img_path)
            if full_path.exists() and full_path.is_relative_to(self.upload_dir):
                full_path.unlink()
                return True
        except Exception:
            pass
        return False


file_service = FileService()
