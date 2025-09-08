from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base_class import Base


class Category(Base):
    __tablename__ = "scoring_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    name = Column(String(100), nullable=False, unique=True, index=True)
    
    # Relationships
    criteria = relationship("Criterion", back_populates="category", cascade="all, delete-orphan")


class Criterion(Base):
    __tablename__ = "scoring_criteria"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    name = Column(String(200), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("scoring_categories.id"), nullable=False)
    
    # Relationships
    category = relationship("Category", back_populates="criteria")
    brand_scores = relationship("BrandCriterionScore", back_populates="criterion", cascade="all, delete-orphan")


class BrandCriterionScore(Base):
    __tablename__ = "brand_criterion_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)
    criterion_id = Column(Integer, ForeignKey("scoring_criteria.id"), nullable=False)
    score = Column(Float, nullable=False)  # 0 to 5
    description = Column(Text, nullable=True)
    
    # Unique constraint: one score per brand and criterion
    __table_args__ = (
        UniqueConstraint('brand_id', 'criterion_id', name='unique_brand_criterion_score'),
    )
    
    # Relationships
    brand = relationship("Brand", backref="criterion_scores")
    criterion = relationship("Criterion", back_populates="brand_scores")
