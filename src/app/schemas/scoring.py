from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from fastapi import Query

# Category schemas
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Category name")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Category name")


class Category(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CategoryWithCriteria(Category):
    criteria: List["Criterion"] = []


# Criterion schemas
class CriterionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Criterion name")
    category_id: int = Field(..., description="Category ID")


class CriterionCreate(CriterionBase):
    pass


class CriterionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Criterion name")
    category_id: Optional[int] = Field(None, description="Category ID")


class Criterion(CriterionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    category: Optional[Category] = None
    
    class Config:
        from_attributes = True


# Brand Criterion Score schemas
class BrandCriterionScoreBase(BaseModel):
    score: float = Field(..., ge=0, le=5, description="Score from 0 to 5")
    description: Optional[str] = Field(None, description="Textual description of the score")


class BrandCriterionScoreCreate(BrandCriterionScoreBase):
    criterion_id: int = Field(..., description="Criterion ID")


class BrandCriterionScoreUpdate(BrandCriterionScoreBase):
    score: Optional[float] = Field(None, ge=0, le=5, description="Score from 0 to 5")


class BrandCriterionScore(BrandCriterionScoreBase):
    id: int
    brand_id: int
    criterion_id: int
    created_at: datetime
    updated_at: datetime
    criterion: Optional[Criterion] = None
    
    class Config:
        from_attributes = True


# Response schemas pour les rapports de scoring
class CategoryScore(BaseModel):
    category_id: int
    category_name: str
    average_score: Optional[float] = Field(None, description="Average score for this category")
    scores: List[BrandCriterionScore] = []

    class Config:
        from_attributes = True


class BrandScoringReport(BaseModel):
    brand_id: int
    brand_name: str
    brand_logo_path: Optional[str] = Field(None, description="Path to brand logo")
    parent_brands: List[str] = Field(default_factory=list, description="List of parent brand names in hierarchy")
    global_score: Optional[float] = Field(None, description="Global brand score")
    category_scores: List[CategoryScore] = []
    total_scores_count: int = Field(0, description="Total number of scored criteria")
    total_criteria_count: int = Field(0, description="Total number of available criteria")

    class Config:
        from_attributes = True


# Filter schemas
class CategoryFilters(BaseModel):
    name: Optional[str] = None
    name__ilike: Optional[str] = None
    name__contains: Optional[str] = None
    name__lookalike: Optional[str] = None


class CriterionFilters(BaseModel):
    name: Optional[str] = None
    name__ilike: Optional[str] = None
    name__contains: Optional[str] = None
    name__lookalike: Optional[str] = None
    category_id: Optional[int] = None
    category___name__contains: Optional[str] = None
    category___name__lookalike: Optional[str] = None

# Paginated response schemas
class CategoryOutPaginated(BaseModel):
    items: List[CategoryWithCriteria]
    total: int
    page: int
    size: int
    pages: int

    class Config:
        from_attributes = True


class CriterionOutPaginated(BaseModel):
    items: List[Criterion]
    total: int
    page: int
    size: int
    pages: int

    class Config:
        from_attributes = True


class BrandFilters(BaseModel):
    name: Optional[str] = None
    name__ilike: Optional[str] = None
    name__contains: Optional[str] = None
    name__lookalike: Optional[str] = None
    name__in: Optional[List[str]] = Field(Query(None))
    name__iin: Optional[List[str]] = Field(Query(None))
    parent_id: Optional[int] = None
    parent___name__contains: Optional[str] = None
    parent___name__lookalike: Optional[str] = None


CategoryWithCriteria.model_rebuild()
