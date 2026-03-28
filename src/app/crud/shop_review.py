from sqlalchemy.orm import Session
from sqlalchemy import func
from app.crud.base import CRUDRepository
from app.models.shop_review import ShopReview, ShopReviewStatus


class ShopReviewCRUDRepository(CRUDRepository):
    def get_shop_summary(self, db: Session, shop_id: int) -> dict:
        """
        Get review count and average rating for a shop (approved reviews only).

        Parameters:
            db (Session): The database session.
            shop_id (int): The shop ID.

        Returns:
            dict: { shop_id, review_count, rating_avg }
        """
        result = db.query(
            func.count(self._model.id).label("review_count"),
            func.avg(self._model.rating).label("rating_avg"),
        ).filter(
            self._model.shop_id == shop_id,
            self._model.status == ShopReviewStatus.APPROVED,
        ).first()

        return {
            "shop_id": shop_id,
            "review_count": result.review_count or 0,
            "rating_avg": round(float(result.rating_avg), 1) if result.rating_avg else 0.0,
        }


shop_review_crud = ShopReviewCRUDRepository(model=ShopReview)
