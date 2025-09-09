from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from app.crud.base import CRUDRepository
from app.models.brand import Brand
from app.models.scoring import BrandCriterionScore, Criterion
from app.crud.filters import buildQueryFilters
from app.log import get_logger

log = get_logger(__name__)

class BrandCRUDRepository(CRUDRepository):
    """Extended CRUD repository for Brand with score calculation."""
    
    def __init__(self):
        super().__init__(model=Brand)
    
    def _calculate_brand_score(self, db: Session, brand_id: int) -> Optional[float]:
        """Calculate the global score for a brand."""
        scores = (
            db.query(func.avg(BrandCriterionScore.score))
            .filter(BrandCriterionScore.brand_id == brand_id)
            .scalar()
        )
        return round(float(scores), 2) if scores is not None else None
    
    def _add_scores_to_brands(self, db: Session, brands: List[Brand]) -> List[Brand]:
        """Add score attribute to a list of brands."""
        for brand in brands:
            brand.score = self._calculate_brand_score(db, brand.id)
        return brands
    
    def get_one_with_score(self, db: Session, *args, **kwargs) -> Optional[Brand]:
        """Get one brand with its score."""
        brand = super().get_one(db, *args, **kwargs)
        if brand:
            brand.score = self._calculate_brand_score(db, brand.id)
        return brand
    
    def get_all_with_scores(self, db: Session) -> List[Brand]:
        """Get all brands with their scores."""
        brands = super().get_all(db)
        return self._add_scores_to_brands(db, brands)
    
    def get_many_with_scores(
        self, 
        db: Session, 
        *args, 
        skip: int = 0, 
        limit: int = 100, 
        order_by: str = 'created_at', 
        descending: bool = False, 
        **kwargs
    ) -> Tuple[List[Brand], int]:
        """Get many brands with their scores."""
        brands, total = super().get_many(
            db, *args, skip=skip, limit=limit, order_by=order_by, 
            descending=descending, **kwargs
        )
        brands_with_scores = self._add_scores_to_brands(db, brands)
        return brands_with_scores, total
    
    def get_one_lookalike_with_score(self, db: Session, filter_param) -> Optional[Brand]:
        """Get one brand by lookalike search with its score."""
        brand = super().get_one_lookalike(db, filter_param)
        if brand:
            brand.score = self._calculate_brand_score(db, brand.id)
        return brand

brand_crud = BrandCRUDRepository()