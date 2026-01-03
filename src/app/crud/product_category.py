from typing import Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDRepository
from app.models.product_category import ProductCategory


class ProductCategoryCRUDRepository(CRUDRepository):
    def get_by_name(self, db: Session, name: str) -> Optional[ProductCategory]:
        """
        Get a product category by name.

        Parameters:
            db (Session): The database session.
            name (str): The name of the category.

        Returns:
            Optional[ProductCategory]: The category found by name, or None if not found.
        """
        return self.get_one(db, self._model.name == name)
    
    def get_children(self, db: Session, category_id: int) -> list[ProductCategory]:
        """
        Get all child categories of a given category.

        Parameters:
            db (Session): The database session.
            category_id (int): The parent category ID.

        Returns:
            list[ProductCategory]: List of child categories.
        """
        return db.query(self._model).filter(
            self._model.parent_category_id == category_id
        ).all()
    
    def get_root_categories(self, db: Session) -> list[ProductCategory]:
        """
        Get all root categories (categories without parent).

        Parameters:
            db (Session): The database session.

        Returns:
            list[ProductCategory]: List of root categories.
        """
        return db.query(self._model).filter(
            self._model.parent_category_id.is_(None)
        ).all()


product_category_crud = ProductCategoryCRUDRepository(model=ProductCategory)
