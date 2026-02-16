from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from app.database.db import get_db
from app.routes.dependencies import get_current_active_user, get_current_user, RoleChecker, get_pagination_params, get_sort_by_params, get_current_active_user_or_client
from app.schemas.scoring import (
    Category, CategoryCreate, CategoryUpdate, CategoryWithCriteria,
    Criterion, CriterionCreate, CriterionUpdate,
    BrandCriterionScore, BrandCriterionScoreCreate, BrandCriterionScoreUpdate,
    BrandScoringReport, CategoryFilters, CriterionFilters, CategoryOutPaginated, CriterionOutPaginated
)
from app.crud import scoring as crud_scoring

router = APIRouter()


@router.post("/categories", response_model=Category, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def create_category(
    *,
    db: Session = Depends(get_db),
    category_in: CategoryCreate
):
    """
    Create a new scoring category.

    **Example payload:**
    ```json
    {
        "name": "Animaux humains & non-humains"
    }
    ```
    """
    # Check whether the category already exists using the filter system
    existing_category = crud_scoring.category.get_one(
        db, name=category_in.name)
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category with name '{category_in.name}' already exists"
        )

    return crud_scoring.category.create(db, category_in)


@router.get("/categories/search", response_model=Optional[CategoryOutPaginated], status_code=status.HTTP_200_OK, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def fetch_paginated_categories(
    db: Session = Depends(get_db),
    pagination_params: Tuple[int, int] = Depends(get_pagination_params),
    orderby_params: Tuple[str, bool] = Depends(get_sort_by_params),
    filter_params: CategoryFilters = Depends()
) -> Optional[CategoryOutPaginated]:
    """
    Fetch many categories with pagination.

    This function fetches all categories from the
    database based on the pagination parameters.

    Parameters:
        db (Session): The database session.
        pagination_params (Tuple[int, int]): The pagination parameters (skip, limit).
        orderby_params (Tuple[str, bool]): The order by parameters (sortby, descending).
        filter_params (CategoryFilters): The filter parameters.

    Returns:
        CategoryOutPaginated: The list of categories fetched from the database with pagination data.
    """
    page, size = pagination_params
    sortby, descending = orderby_params
    categories, total = crud_scoring.category.get_many(
        db,
        skip=page,
        limit=size,
        order_by=sortby,
        descending=descending,
        **filter_params.model_dump(exclude_none=True)
    )
    pages = (total + size - 1) // size
    return {
        "items": categories,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get("/categories", response_model=List[CategoryWithCriteria], dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def read_categories(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Nombre maximum d'éléments à retourner")
):
    """Retrieve all categories with their criteria (backward compatibility)."""
    categories = crud_scoring.category.get_all(db, skip=skip, limit=limit)
    return categories


@router.get("/categories/{category_id}", response_model=CategoryWithCriteria, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def read_category(
    *,
    db: Session = Depends(get_db),
    category_id: int
):
    category = crud_scoring.category.get_one(db, id=category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Category with id '{category_id}' not found")
    return category


@router.put("/categories/{category_id}", response_model=Category, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def update_category(
    *,
    db: Session = Depends(get_db),
    category_id: int,
    category_in: CategoryUpdate
):
    """
    Update a category

    **Exemple de payload:**
    ```json
    {
        "name": "Environnement & Durabilité"

    }
    ```
    """
    category = crud_scoring.category.get_one(db, id=category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Category with id '{category_id}' not found")

    return crud_scoring.category.update(db, db_obj=category, obj_update=category_in)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker(["admin"]))])
def delete_category(
    *,
    db: Session = Depends(get_db),
    category_id: int
):
    """Delete a category (and all its associated criteria)."""
    category = crud_scoring.category.get_one(db, id=category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Category with id '{category_id}' not found")

    crud_scoring.category.delete(db, category)


# Criteria endpoints
@router.post("/criteria", response_model=Criterion, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def create_criterion(
    *,
    db: Session = Depends(get_db),
    criterion_in: CriterionCreate
):
    """
    Create a new scoring criterion.

    **Payload example:**
    ```json
    {
        "name": "Conditions de travail",
        "category_id": 1
    }
    ```
    """
    # Check that the category exists
    category = crud_scoring.category.get_one(db, id=criterion_in.category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Category with id '{criterion_in.category_id}' not found")

    # Check uniqueness in the category
    existing_criterion = crud_scoring.criterion.get_one(
        db, name=criterion_in.name, category_id=criterion_in.category_id
    )
    if existing_criterion:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Criterion with name '{criterion_in.name}' already exists in this category"
        )

    return crud_scoring.criterion.create(db, obj_create=criterion_in)


@router.get("/criteria/search", response_model=Optional[CriterionOutPaginated], status_code=status.HTTP_200_OK, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def fetch_paginated_criteria(
    db: Session = Depends(get_db),
    pagination_params: Tuple[int, int] = Depends(get_pagination_params),
    orderby_params: Tuple[str, bool] = Depends(get_sort_by_params),
    filter_params: CriterionFilters = Depends()
) -> Optional[CriterionOutPaginated]:
    """
    Fetch many criteria with pagination.

    This function fetches all criteria from the
    database based on the pagination parameters.

    Parameters:
        db (Session): The database session.
        pagination_params (Tuple[int, int]): The pagination parameters (skip, limit).
        orderby_params (Tuple[str, bool]): The order by parameters (sortby, descending).
        filter_params (CriterionFilters): The filter parameters.

    Returns:
        CriterionOutPaginated: The list of criteria fetched from the database with pagination data.
    """
    page, size = pagination_params
    sortby, descending = orderby_params
    criteria, total = crud_scoring.criterion.get_many(
        db,
        skip=page,
        limit=size,
        order_by=sortby,
        descending=descending,
        **filter_params.model_dump(exclude_none=True)
    )
    pages = (total + size - 1) // size
    return {
        "items": criteria,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get("/criteria", response_model=List[Criterion], dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def read_criteria(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Nombre maximum d'éléments à retourner"),
    category_id: Optional[int] = Query(
        None, description="Filtrer par catégorie")
):
    """Retrieve all criteria, optionally filtered by category (backward compatibility)."""
    if category_id:
        return crud_scoring.criterion.get_all(db, category_id=category_id)
    else:
        return crud_scoring.criterion.get_all(db, skip=skip, limit=limit)


@router.get("/criteria/{criterion_id}", response_model=Criterion, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def read_criterion(
    criterion_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Retrieve a specific criterion."""
    criterion = crud_scoring.criterion.get_one(db, id=criterion_id)
    if not criterion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Criterion not found")
    return criterion


@router.put("/criteria/{criterion_id}", response_model=Criterion, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def update_criterion(
    *,
    db: Session = Depends(get_db),
    criterion_id: int,
    criterion_in: CriterionUpdate
):
    """
    Update a criterion.

    **Example of a payload:**
    ```json
    {
        "name": "Empreinte carbone",
        "category_id": 2
    }
    ```
    """
    criterion = crud_scoring.criterion.get_one(db, id=criterion_id)
    if not criterion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Critère non trouvé")

    # Check that the new category exists if changed
    if criterion_in.category_id and criterion_in.category_id != criterion.category_id:
        category = crud_scoring.category.get_one(
            db, id=criterion_in.category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Category with id '{criterion_in.category_id}' not found")

    return crud_scoring.criterion.update(db, db_obj=criterion, obj_update=criterion_in)


@router.delete("/criteria/{criterion_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker(["admin"]))])
def delete_criterion(
    *,
    db: Session = Depends(get_db),
    criterion_id: int
):
    """Delete a criterion (and all associated scores)."""
    criterion = crud_scoring.criterion.get_one(db, id=criterion_id)
    if not criterion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Criterion with id '{criterion_id}' not found")

    crud_scoring.criterion.delete(db, db_obj=criterion)


# Brand criterion scores endpoints
@router.post("/brands/{brand_id}/scores", response_model=BrandCriterionScore, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def create_or_update_brand_score(
    *,
    db: Session = Depends(get_db),
    brand_id: int,
    score_in: BrandCriterionScoreCreate
):
    """
    Create or update a brand score for a specific criterion.

    **Payload example:**
    ```json
    {
        "criterion_id": 1,
        "score": 2,
        "description": "La marque respecte les conditions de travail équitables avec certification Fair Trade."
    }
    ```
    """
    from app.crud.brand import brand_crud
    from app.models import Brand
    brand = brand_crud.get_one(db, Brand.id == brand_id)
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Brand with id '{brand_id}' not found")

    # Check that the criterion exists
    criterion = crud_scoring.criterion.get_one(db, id=score_in.criterion_id)
    if not criterion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Criterion with id '{score_in.criterion_id}' not found")

    return crud_scoring.brand_criterion_score.create_or_update(db, brand_id=brand_id, obj_in=score_in)


@router.get("/brands/{brand_id}/scores", response_model=List[BrandCriterionScore], dependencies=[Depends(get_current_active_user)])
def read_brand_scores(
    *,
    db: Session = Depends(get_db),
    brand_id: int
):
    """Get all scores for a brand."""
    from app.crud.brand import brand_crud
    from app.models import Brand
    brand = brand_crud.get_one(db, Brand.id == brand_id)
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Brand with id '{brand_id}' not found")

    return crud_scoring.brand_criterion_score.get_brand_scores(db, brand_id=brand_id)


@router.get("/brands/{brand_id}/scoring-report", response_model=BrandScoringReport, dependencies=[Depends(get_current_active_user_or_client)])
def get_brand_scoring_report(
    *,
    db: Session = Depends(get_db),
    brand_id: int
):
    """
    Get complete scoring report for a brand.
    - Note per criterion with description
    - Per category average
    - Global score
    """
    report = crud_scoring.brand_criterion_score.get_brand_scoring_report(
        db, brand_id=brand_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Brand with id '{brand_id}' not found")

    return report


@router.get("/brands/{brand_id}/scores/{criterion_id}", response_model=BrandCriterionScore, dependencies=[Depends(get_current_active_user)])
def read_brand_criterion_score(
    *,
    db: Session = Depends(get_db),
    brand_id: int,
    criterion_id: int
):
    """Get a specific brand score for a specific criterion."""
    score = crud_scoring.brand_criterion_score.get_by_brand_and_criterion(
        db, brand_id=brand_id, criterion_id=criterion_id
    )
    if not score:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Score with id '{criterion_id}' not found")
    return score


@router.put("/brands/{brand_id}/scores/{criterion_id}", response_model=BrandCriterionScore, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def update_brand_criterion_score(
    *,
    db: Session = Depends(get_db),
    brand_id: int,
    criterion_id: int,
    score_in: BrandCriterionScoreUpdate
):
    """
    Update a brand score for a specific criterion.

    **Payload example:**
    ```json
    {
        "score": 4.0,
        "description": "Amélioration notable avec nouvelle certification B-Corp."
    }
    ```
    """
    existing_score = crud_scoring.brand_criterion_score.get_by_brand_and_criterion(
        db, brand_id=brand_id, criterion_id=criterion_id
    )
    if not existing_score:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Score with id '{criterion_id}' not found")

    # Create a creation object to reuse existing logic
    score_create = BrandCriterionScoreCreate(
        criterion_id=criterion_id,
        score=score_in.score if score_in.score is not None else existing_score.score,
        description=score_in.description if score_in.description is not None else existing_score.description
    )

    return crud_scoring.brand_criterion_score.create_or_update(db, brand_id=brand_id, obj_in=score_create)


@router.delete("/brands/{brand_id}/scores/{criterion_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def delete_brand_criterion_score(
    *,
    db: Session = Depends(get_db),
    brand_id: int,
    criterion_id: int
):
    """Delete a brand score for a specific criterion."""
    if not crud_scoring.brand_criterion_score.delete_by_brand_and_criterion(
        db, brand_id=brand_id, criterion_id=criterion_id
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Score with id '{criterion_id}' not found")
