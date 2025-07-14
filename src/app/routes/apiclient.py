from typing import Annotated, List, Optional, Tuple

from fastapi import APIRouter, Request, Body, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.routes.dependencies import get_current_superuser, get_pagination_params, get_sort_by_params, RoleChecker
from app.crud import apiclient_crud
from app.database.db import get_db
from app.log import get_logger
from app.models import ApiClient, User
from app.schemas.apiclient import ApiClientCreate, ApiClientOut, ApiClientUpdate, ApiClientOutPaginated, ApiClientFilters

log = get_logger(__name__)

router = APIRouter(dependencies=[Depends(get_current_superuser)])


@router.get(
    "/", response_model=List[Optional[ApiClientOut]], status_code=status.HTTP_200_OK
)
def fetch_all_api_clients(db: Session = Depends(get_db)) -> List[Optional[ApiClientOut]]:
    """
    Fetch all api clients.

    This function fetches all api clients from the
    database.

    Parameters:
        db (Session): The database session.

    Raises:
        HTTPException: If the user does not have enough
            permissions to fetch the api client.

    Returns:
        List[Optional[ApiClientOut]]: The list of api clients fetched from the database.
    """
    
    return apiclient_crud.get_all(db)


@router.get(
    "/search", response_model=Optional[ApiClientOutPaginated], status_code=status.HTTP_200_OK
)
def fetch_paginated_api_clients(
    db: Session = Depends(get_db),
    pagination_params: Tuple[int, int] = Depends(get_pagination_params),
    orderby_params: Tuple[str, bool] = Depends(get_sort_by_params),
    filter_params: ApiClientFilters = Depends()
) -> Optional[ApiClientOutPaginated]:
    """
    Fetch many api clients.

    This function fetches all api clients from the
    database based on the pagination parameters.

    Parameters:
        db (Session): The database session.
        pagination_params (Tuple[int, int]): The pagination parameters (skip, limit).
        orderby_params (Tuple[str, bool]): The order by parameters (sortby, descending).
    
    Raises:
        HTTPException: If the user does not have enough
            permissions to fetch the api client.

    Returns:
        ApiClientOutPaginated: The list of api clients fetched from the database with pagination datas.
    """
    page, size = pagination_params
    sortby, descending = orderby_params
    clients, total = apiclient_crud.get_many(
        db, 
        skip=page, 
        limit=size, 
        order_by=sortby, 
        descending=descending, 
        **filter_params.model_dump(exclude_none=True)
    )
    pages = (total + size - 1) // size
    return {
        "items": clients,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get(
    "/{id}",
    response_model=Optional[ApiClientOut],
    status_code=status.HTTP_200_OK,
)
def fetch_api_client_by_id(
    id: int, db: Session = Depends(get_db)
) -> ApiClientOut:
    """
    Fetches an api client by its ID.

    Parameters:
        id (int): The ID of the api client.
        db (Session): The database session.

    Returns:
        ApiClientOut: The fetched api client.

    Raises:
        HTTPException: If the user does not have enough
            permissions to fetch the api client.
        HTTPException: If the api client is not found.
    """
    client = apiclient_crud.get_one(db, ApiClient.id == id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ApiClient with id {id} not found",
        )
    return client


@router.post(
    "/",
    response_model=ApiClientOut,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def create_api_client(
    client_create: Annotated[
        ApiClientCreate,
        Body(
            examples=[
                {
                    "name": "Client name",
                    "api_key": "generated api key",
                    "is_active": True,
                }
            ]
        ),
    ],
    db: Session = Depends(get_db),
):
    """
    Create a api client.

    Parameters:
        client_create (ApiClientCreate): The api client data to be created.
        db (Session, optional): The database session.
            Defaults to Depends(get_db).


    Returns:
        ApiClientOut: The created api client.

    Raises:
        HTTPException: If the user does not have enough
            permissions to create the api client.
        HTTPException: If an api client with same api key provided exists.
        HTTPException: If an api client with same name provided exists.
        HTTPException: If there is an error creating
            the api client in the database.
    """
    try:
        client = apiclient_crud.create(
            db, client_create
        )
    except IntegrityError as e:
        error_message = str(e.orig)
        if "unique constraint" in error_message.lower():
            if "api_key" in error_message.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Api client with KEY {client_create.api_key} already exists",
                ) from e
            if "name" in error_message.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Api client with NAME {client_create.name} already exists",
                ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data integrity error: {error_message}",
            ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't create product. Error: {str(e)}",
        ) from e 
    return client


@router.put(
    "/{id}",
    response_model=ApiClientOut,
    status_code=status.HTTP_200_OK,
)
def update_api_client(
    id: int,
    client_update: ApiClientUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an api client by its ID.

    Parameters:
        id (int): The ID of the api client to be updated.
        client_update (ApiClientUpdate): The updated api client data.
        db (Session, optional): The database session.
            Defaults to Depends(get_db).

    Returns:
        ApiClientOut: The updated api client.

    Raises:
        HTTPException: If the user does not have enough
            permissions to update the api client.
        HTTPException: If the api client does not exist.
        HTTPException: If there is an error updating
            the api client in the database.
    """
    client = apiclient_crud.get_one(db, ApiClient.id == id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ApiClient with id {id} not found",
        )

    try:
        client = apiclient_crud.update(db, client, client_update)
    except Exception as e:  
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't update api client with id {id}. Error: {str(e)}",
        ) from e  
    return client


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api_client(
    id: int,
    db: Session = Depends(get_db),
):
    """
    Deletes a api client by its ID.

    Parameters:
        id (int): The ID of the api client to delete.
        db (Session): The database session.

    Raises:
        HTTPException: If the api client with the given ID is not found.
        HTTPException: If the user does not have enough
            permissions to delete the api client.
        HTTPException: If there is an error while
            deleting the api client from the database.
    """
    client = apiclient_crud.get_one(db, ApiClient.id == id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ApiClient with id {id} not found. Cannot delete.",
        )
    try:
        apiclient_crud.delete(db, client)
    except Exception as e:  
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't delete api client with id {id}. Error: {str(e)}",
        ) from e