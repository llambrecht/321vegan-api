from typing import Annotated, List, Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException, status, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.routes.dependencies import get_current_active_user, get_pagination_params, get_sort_by_params, RoleChecker
from app.crud import scan_event_crud
from app.database.db import get_db
from app.log import get_logger
from app.models import ScanEvent, User
from app.schemas.scan_event import ScanEventCreate, ScanEventOut, ScanEventUpdate, ScanEventOutPaginated

log = get_logger(__name__)

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get(
    "/", response_model=List[Optional[ScanEventOut]], status_code=status.HTTP_200_OK
)
def fetch_all_scan_events(db: Session = Depends(get_db)) -> List[Optional[ScanEventOut]]:
    """
    Fetch all scan events.

    This function fetches all scan events from the database.

    Parameters:
        db (Session): The database session.

    Returns:
        List[Optional[ScanEventOut]]: The list of scan events fetched from the database.
    """
    return scan_event_crud.get_all(db)


@router.get(
    "/search", response_model=Optional[ScanEventOutPaginated], status_code=status.HTTP_200_OK
)
def fetch_paginated_scan_events(
    db: Session = Depends(get_db),
    pagination_params: Tuple[int, int] = Depends(get_pagination_params),
    orderby_params: Tuple[str, bool] = Depends(get_sort_by_params),
) -> Optional[ScanEventOutPaginated]:
    """
    Fetch many scan events with pagination.

    Parameters:
        db (Session): The database session.
        pagination_params (Tuple[int, int]): The pagination parameters (skip, limit).
        orderby_params (Tuple[str, bool]): The order by parameters (sortby, descending).

    Returns:
        ScanEventOutPaginated: The list of scan events with pagination data.
    """
    page, size = pagination_params
    sortby, descending = orderby_params
    events, total = scan_event_crud.get_many(
        db, 
        skip=page, 
        limit=size, 
        order_by=sortby, 
        descending=descending
    )
    pages = (total + size - 1) // size
    return {
        "items": events,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get(
    "/by-ean/{ean}", response_model=List[Optional[ScanEventOut]], status_code=status.HTTP_200_OK
)
def fetch_scan_events_by_ean(
    ean: str, 
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
) -> List[Optional[ScanEventOut]]:
    """
    Fetch scan events by EAN.

    Parameters:
        ean (str): The EAN of the product.
        limit (int): Maximum number of results to return (default 100, max 1000).
        db (Session): The database session.

    Returns:
        List[Optional[ScanEventOut]]: The list of scan events for the given EAN.
    """
    return scan_event_crud.get_by_ean(db, ean, limit)


@router.get(
    "/by-user/{user_id}", response_model=List[Optional[ScanEventOut]], status_code=status.HTTP_200_OK
)
def fetch_scan_events_by_user(
    user_id: int, 
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
) -> List[Optional[ScanEventOut]]:
    """
    Fetch scan events by user ID.

    Parameters:
        user_id (int): The ID of the user.
        limit (int): Maximum number of results to return (default 100, max 1000).
        db (Session): The database session.

    Returns:
        List[Optional[ScanEventOut]]: The list of scan events for the given user.
    """
    return scan_event_crud.get_by_user(db, user_id, limit)

@router.get(
    "/{id}",
    response_model=Optional[ScanEventOut],
    status_code=status.HTTP_200_OK,
)
def fetch_scan_event_by_id(
    id: int, db: Session = Depends(get_db)
) -> ScanEventOut:
    """
    Fetches a scan event by its ID.

    Parameters:
        id (int): The ID of the scan event.
        db (Session): The database session.

    Returns:
        ScanEventOut: The fetched scan event.

    Raises:
        HTTPException: If the scan event is not found.
    """
    event = scan_event_crud.get_one(db, ScanEvent.id == id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan event with id {id} not found",
        )
    return event


@router.post(
    "/",
    response_model=ScanEventOut,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def create_scan_event(
    event_create: Annotated[
        ScanEventCreate,
        Body(
            examples=[
                {
                    "ean": "1234567890123",
                    "latitude": 48.8566,
                    "longitude": 2.3522,
                    "shop_name": "Carrefour",
                    "lookup_api_response": '{"status": "success"}',
                    "user_id": 1
                }
            ]
        ),
    ],
    db: Session = Depends(get_db),
    active_user: User = Depends(get_current_active_user),
):
    """
    Create a scan event.

    Parameters:
        event_create (ScanEventCreate): The scan event data to be created.
        db (Session): The database session.
        active_user (User): The current active user.

    Returns:
        ScanEventOut: The created scan event.

    Raises:
        HTTPException: If the user does not exist.
        HTTPException: If there is an error creating the scan event.
    """
    try:
        event = scan_event_crud.create(db, event_create)
    except IntegrityError as e:
        error_message = str(e.orig)
        if "foreign key constraint" in error_message.lower() and "user_id" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with id {event_create.user_id} does not exist",
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data integrity error: {error_message}",
            ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't create scan event. Error: {str(e)}",
        ) from e 
    return event


@router.put(
    "/{id}",
    response_model=ScanEventOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RoleChecker(["admin"]))]
)
def update_scan_event(
    id: int,
    event_update: ScanEventUpdate,
    db: Session = Depends(get_db),
    active_user: User = Depends(get_current_active_user),
):
    """
    Update a scan event by its ID.
    Only admins can update scan events.

    Parameters:
        id (int): The ID of the scan event to be updated.
        event_update (ScanEventUpdate): The updated scan event data.
        db (Session): The database session.
        active_user (User): The current active user.

    Returns:
        ScanEventOut: The updated scan event.

    Raises:
        HTTPException: If the scan event does not exist.
        HTTPException: If there is an error updating the scan event.
    """
    event = scan_event_crud.get_one(db, ScanEvent.id == id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan event with id {id} not found",
        )
    
    try:
        event = scan_event_crud.update(db, event, event_update)
    except IntegrityError as e:
        error_message = str(e.orig)
        if "foreign key constraint" in error_message.lower() and "user_id" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with id {event_update.user_id} does not exist",
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data integrity error: {error_message}",
            ) from e
    except Exception as e:  
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't update scan event with id {id}. Error: {str(e)}",
        ) from e  
    return event


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker(["admin"]))])
def delete_scan_event(
    id: int,
    db: Session = Depends(get_db),
    active_user: User = Depends(get_current_active_user),
):
    """
    Deletes a scan event by its ID.
    Only admins can delete scan events.

    Parameters:
        id (int): The ID of the scan event to delete.
        db (Session): The database session.
        active_user (User): The current active user.

    Raises:
        HTTPException: If the scan event is not found.
        HTTPException: If there is an error while deleting the scan event.
    """
    event = scan_event_crud.get_one(db, ScanEvent.id == id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan event with id {id} not found. Cannot delete.",
        )
    try:
        scan_event_crud.delete(db, event)
    except Exception as e:  
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't delete scan event with id {id}. Error: {str(e)}",
        ) from e
