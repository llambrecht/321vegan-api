from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from app.database.db import get_db
from app.routes.dependencies import get_current_user, get_pagination_params, get_sort_by_params
from app.schemas.scoring import (
    Category, CategoryCreate, CategoryUpdate, CategoryWithCriteria,
    Criterion, CriterionCreate, CriterionUpdate,
    BrandCriterionScore, BrandCriterionScoreCreate, BrandCriterionScoreUpdate,
    BrandScoringReport, CategoryFilters, CriterionFilters, CategoryOutPaginated, CriterionOutPaginated
)
from app.crud import scoring as crud_scoring

router = APIRouter()

@router.post("/categories", response_model=Category, status_code=status.HTTP_201_CREATED)
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
        "name": "Humains & Animaux"
    }
    ```
    """
    # Vérifier si la catégorie existe déjà en utilisant le système de filtres
    existing_category = crud_scoring.category.get_one(db, name=category_in.name)
    if existing_category:
        raise HTTPException(
            status_code=400,
            detail="Une catégorie avec ce nom existe déjà"
        )
    
    return crud_scoring.category.create(db, category_in)


@router.get("/categories/search", response_model=Optional[CategoryOutPaginated], status_code=status.HTTP_200_OK)
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


@router.get("/categories", response_model=List[CategoryWithCriteria])
def read_categories(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner")
):
    """Récupérer toutes les catégories avec leurs critères (backward compatibility)."""
    categories = crud_scoring.category.get_all(db, skip=skip, limit=limit)
    return categories


@router.get("/categories/{category_id}", response_model=CategoryWithCriteria)
def read_category(
    *,
    db: Session = Depends(get_db),
    category_id: int
):
    category = crud_scoring.category.get_one(db, id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return category


@router.put("/categories/{category_id}", response_model=Category)
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
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    
    return crud_scoring.category.update(db, db_obj=category, obj_update=category_in)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    *,
    db: Session = Depends(get_db),
    category_id: int
):
    """Supprimer une catégorie (et tous ses critères associés)."""
    category = crud_scoring.category.get_one(db, id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    
    crud_scoring.category.delete(db, category)


# Criteria endpoints
@router.post("/criteria", response_model=Criterion, status_code=status.HTTP_201_CREATED)
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
    # Vérifier que la catégorie existe
    category = crud_scoring.category.get_one(db, id=criterion_in.category_id)
    if not category:
        raise HTTPException(status_code=400, detail="Catégorie non trouvée")
    
    # Vérifier l'unicité dans la catégorie
    existing_criterion = crud_scoring.criterion.get_one(
        db, name=criterion_in.name, category_id=criterion_in.category_id
    )
    if existing_criterion:
        raise HTTPException(
            status_code=400,
            detail=f"Criterion with name '{criterion_in.name}' already exists in this category"
        )
    
    return crud_scoring.criterion.create(db, obj_create=criterion_in)


@router.get("/criteria/search", response_model=Optional[CriterionOutPaginated], status_code=status.HTTP_200_OK)
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


@router.get("/criteria", response_model=List[Criterion])
def read_criteria(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner"),
    category_id: Optional[int] = Query(None, description="Filtrer par catégorie")
):
    """Récupérer tous les critères, optionnellement filtrés par catégorie (backward compatibility)."""
    if category_id:
        return crud_scoring.criterion.get_all(db, category_id=category_id)
    else:
        return crud_scoring.criterion.get_all(db, skip=skip, limit=limit)


@router.get("/criteria/{criterion_id}", response_model=Criterion)
def read_criterion(
    criterion_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Récupérer un critère spécifique."""
    criterion = crud_scoring.criterion.get_one(db, id=criterion_id)
    if not criterion:
        raise HTTPException(status_code=404, detail="Criterion not found")
    return criterion


@router.put("/criteria/{criterion_id}", response_model=Criterion)
def update_criterion(
    *,
    db: Session = Depends(get_db),
    criterion_id: int,
    criterion_in: CriterionUpdate
):
    """
    Mettre à jour un critère.
    
    **Exemple de payload:**
    ```json
    {
        "name": "Empreinte carbone",
        "category_id": 2
    }
    ```
    """
    criterion = crud_scoring.criterion.get_one(db, id=criterion_id)
    if not criterion:
        raise HTTPException(status_code=404, detail="Critère non trouvé")
    
    # Check that the new category exists if changed
    if criterion_in.category_id and criterion_in.category_id != criterion.category_id:
        category = crud_scoring.category.get_one(db, id=criterion_in.category_id)
        if not category:
            raise HTTPException(status_code=400, detail="Catégorie non trouvée")
    
    return crud_scoring.criterion.update(db, db_obj=criterion, obj_update=criterion_in)


@router.delete("/criteria/{criterion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_criterion(
    *,
    db: Session = Depends(get_db),
    criterion_id: int
):
    """Supprimer un critère (et toutes les notes associées)."""
    criterion = crud_scoring.criterion.get_one(db, id=criterion_id)
    if not criterion:
        raise HTTPException(status_code=404, detail="Critère non trouvé")
    
    crud_scoring.criterion.delete(db, db_obj=criterion)


# Brand criterion scores endpoints
@router.post("/brands/{brand_id}/scores", response_model=BrandCriterionScore, status_code=status.HTTP_201_CREATED)
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
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Check that the criterion exists
    criterion = crud_scoring.criterion.get_one(db, id=score_in.criterion_id)
    if not criterion:
        raise HTTPException(status_code=400, detail="Critère non trouvé")
    
    return crud_scoring.brand_criterion_score.create_or_update(db, brand_id=brand_id, obj_in=score_in)


@router.get("/brands/{brand_id}/scores", response_model=List[BrandCriterionScore])
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
        raise HTTPException(status_code=404, detail="Brand not found")
    
    return crud_scoring.brand_criterion_score.get_brand_scores(db, brand_id=brand_id)


@router.get("/brands/{brand_id}/scoring-report", response_model=BrandScoringReport)
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
    report = crud_scoring.brand_criterion_score.get_brand_scoring_report(db, brand_id=brand_id)
    if not report:
        raise HTTPException(status_code=404, detail="Marque non trouvée")
    
    return report


@router.get("/brands/{brand_id}/scores/{criterion_id}", response_model=BrandCriterionScore)
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
        raise HTTPException(status_code=404, detail="Note non trouvée")
    return score


@router.put("/brands/{brand_id}/scores/{criterion_id}", response_model=BrandCriterionScore)
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
        raise HTTPException(status_code=404, detail="Note non trouvée")
    
    # Créer un objet de création pour réutiliser la logique existante
    score_create = BrandCriterionScoreCreate(
        criterion_id=criterion_id,
        score=score_in.score if score_in.score is not None else existing_score.score,
        description=score_in.description if score_in.description is not None else existing_score.description
    )
    
    return crud_scoring.brand_criterion_score.create_or_update(db, brand_id=brand_id, obj_in=score_create)


@router.delete("/brands/{brand_id}/scores/{criterion_id}", status_code=status.HTTP_204_NO_CONTENT)
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
        raise HTTPException(status_code=404, detail="Note non trouvée")
