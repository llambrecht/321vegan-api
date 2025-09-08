from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.scoring import Category, Criterion, BrandCriterionScore
from app.models.brand import Brand
from app.schemas.scoring import (
    BrandCriterionScoreCreate,
    CategoryScore, BrandScoringReport
)
from app.crud.base import CRUDRepository

category = CRUDRepository(model=Category)
criterion = CRUDRepository(model=Criterion)

class BrandCriterionScoreCRUD():
    def create_or_update(self, db: Session, *, brand_id: int, obj_in: BrandCriterionScoreCreate) -> BrandCriterionScore:
        """Create or update a score for a brand and criterion."""
        existing_score = db.query(BrandCriterionScore).filter(
            BrandCriterionScore.brand_id == brand_id,
            BrandCriterionScore.criterion_id == obj_in.criterion_id
        ).first()
        
        if existing_score:
            # Update
            for field, value in obj_in.dict().items():
                if field != 'criterion_id' and value is not None:
                    setattr(existing_score, field, value)
            db.commit()
            db.refresh(existing_score)
            return existing_score
        else:
            # Create
            db_obj = BrandCriterionScore(brand_id=brand_id, **obj_in.dict())
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
    
    def get_brand_scores(self, db: Session, *, brand_id: int) -> List[BrandCriterionScore]:
        """Get all scores for a brand."""
        return db.query(BrandCriterionScore).filter(
            BrandCriterionScore.brand_id == brand_id
        ).all()
    
    def get_by_brand_and_criterion(self, db: Session, *, brand_id: int, criterion_id: int) -> Optional[BrandCriterionScore]:
        """Get a specific score for a brand and criterion."""
        return db.query(BrandCriterionScore).filter(
            BrandCriterionScore.brand_id == brand_id,
            BrandCriterionScore.criterion_id == criterion_id
        ).first()
    
    def delete_by_brand_and_criterion(self, db: Session, *, brand_id: int, criterion_id: int) -> bool:
        """Delete a score for a brand and criterion."""
        score = self.get_by_brand_and_criterion(db, brand_id=brand_id, criterion_id=criterion_id)
        if score:
            db.delete(score)
            db.commit()
            return True
        return False
    
    def get_brand_scoring_report(self, db: Session, *, brand_id: int) -> Optional[BrandScoringReport]:
        """Generate the complete scoring report for a brand."""
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            return None

        # Retrieve all categories and their criteria
        categories = db.query(Category).all()
        category_scores = []
        all_category_averages = []
        total_scores_count = 0
        total_criteria_count = 0
        
        for category in categories:
            scores = (
                db.query(BrandCriterionScore)
                .join(Criterion)
                .filter(
                    BrandCriterionScore.brand_id == brand_id,
                    Criterion.category_id == category.id
                )
                .all()
            )
            
            criteria_count = db.query(Criterion).filter(Criterion.category_id == category.id).count()
            total_criteria_count += criteria_count
            
            category_average = None
            if scores:
                category_average = sum(score.score for score in scores) / len(scores)
                all_category_averages.append(category_average)
                total_scores_count += len(scores)
            
            category_scores.append(CategoryScore(
                category_id=category.id,
                category_name=category.name,
                average_score=round(category_average, 2) if category_average is not None else None,
                scores=scores
            ))
        
        global_score = None
        if all_category_averages:
            global_score = sum(all_category_averages) / len(all_category_averages)
            global_score = round(global_score, 2)
        
        # Get parent brand names hierarchy (exclude current brand)
        parent_brands = brand.parent_name_tree[1:] if len(brand.parent_name_tree) > 1 else []
        
        return BrandScoringReport(
            brand_id=brand_id,
            brand_name=brand.name,
            brand_logo_path=brand.logo_path,
            parent_brands=parent_brands,
            global_score=global_score,
            category_scores=category_scores,
            total_scores_count=total_scores_count,
            total_criteria_count=total_criteria_count
        )

brand_criterion_score = BrandCriterionScoreCRUD()