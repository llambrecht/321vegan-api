import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from typing import Optional


class FileService:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.brands_dir = self.upload_dir / "brands"
        
        self.brands_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_image(self, file: UploadFile) -> bool:
        """Check if the uploaded file is a valid image."""
        allowed_types = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
        if file.content_type not in allowed_types:
            return False
        
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        file_extension = Path(file.filename or "").suffix.lower()
        if file_extension not in allowed_extensions:
            return False
        
        return True
    
    def save_brand_logo(self, brand_id: int, file: UploadFile) -> str:
        """
        Save the logo and return the relative path.
        
        Args:
            brand_id: Brand ID
            file: Uploaded file
            
        Returns:
            str: Relative path of the saved file
            
        Raises:
            HTTPException: If the file is not valid
        """
        if not self.validate_image(file):
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
        
        file_extension = Path(file.filename or "").suffix.lower()
        filename = f"brand_{brand_id}_{uuid.uuid4().hex}{file_extension}"
        file_path = self.brands_dir / filename
        
        try:
            self.delete_old_brand_logo(brand_id)
            
            with open(file_path, "wb") as buffer:
                content = file.file.read()
                buffer.write(content)
                        
            return f"uploads/brands/{filename}"
            
        except Exception as e:
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=500,
                detail=f"Error saving file: {str(e)}"
            )
    
    def delete_old_brand_logo(self, brand_id: int) -> bool:
        """Delete the old logo of a brand."""
        try:
            pattern = f"brand_{brand_id}_*"
            for file_path in self.brands_dir.glob(pattern):
                file_path.unlink()
            return True
        except Exception:
            return False

    
    def delete_brand_logo(self, logo_path: str) -> bool:
        try:
            full_path = Path(logo_path)
            if full_path.exists() and full_path.is_relative_to(self.upload_dir):
                full_path.unlink()
                return True
        except Exception:
            pass
        return False


file_service = FileService()
