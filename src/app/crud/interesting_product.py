from typing import Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDRepository
from app.models.interesting_product import InterestingProduct


class InterestingProductCRUDRepository(CRUDRepository):
    def get_by_ean(self, db: Session, ean: str) -> Optional[InterestingProduct]:
        """
        Get an interesting product by EAN.

        Parameters:
            db (Session): The database session.
            ean (str): The EAN of the product.

        Returns:
            Optional[InterestingProduct]: The product found by EAN, or None if not found.
        """
        return self.get_one(db, self._model.ean == ean)


interesting_product_crud = InterestingProductCRUDRepository(model=InterestingProduct)
