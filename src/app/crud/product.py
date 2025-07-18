from typing import Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDRepository
from app.models.product import Product

class ProductCRUDRepository(CRUDRepository):
    def get_product_by_ean(self, db: Session, ean: str) -> Optional[Product]:
        """
        Get a product by ean.

        Parameters:
            db (Session): The database session.
            ean (str): The ean of the product.

        Returns:
            Optional[Product]: The product found by ean, or None if not found.
        """
        return self.get_one(db, self._model.ean == ean)

product_crud = ProductCRUDRepository(model=Product)

