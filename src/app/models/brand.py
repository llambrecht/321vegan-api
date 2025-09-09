from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, select, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from app.database.base_class import Base

class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    name = Column(String, unique=True, index=True, nullable=False)
    logo_path = Column(String, nullable=True)
    parent_id = Column(Integer, ForeignKey("brands.id"), nullable=True)
    children = relationship("Brand", back_populates="parent")
    parent = relationship("Brand", back_populates="children", remote_side=[id])
    products = relationship("Product", back_populates="brand")


    @hybrid_property
    def parent_name(self):
        if self.parent:
            return self.parent.name
        else:
            return None

    @parent_name.inplace.expression
    @classmethod
    def _parent_name_expression(cls):
        return Brand.parent

    @hybrid_property
    def score(self):
        """Calculate the average score for this brand."""
        from app.models.scoring import BrandCriterionScore
        if hasattr(self, '_score_cache'):
            return self._score_cache
        
        if len(self.criterion_scores) == 0:
            return None
        
        total_score = sum(score.score for score in self.criterion_scores)
        avg_score = total_score / len(self.criterion_scores)
        return round(avg_score, 2)

    @score.expression
    @classmethod
    def _score_expression(cls):
        """SQL expression for calculating brand score."""
        from app.models.scoring import BrandCriterionScore
        return (
            select(func.round(func.avg(BrandCriterionScore.score), 2))
            .where(BrandCriterionScore.brand_id == cls.id)
            .scalar_subquery()
        )

    @property
    def parent_name_tree(self) -> list:
        if self.parent:
            return [self.name] + self.parent.parent_name_tree
        return [self.name]