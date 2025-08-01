"""
This module contains the base interface for CRUD 
(Create, Read, Update, Delete) operations.
"""
from typing import List, Optional, Type, TypeVar, Tuple

from pydantic import BaseModel
from sqlalchemy import desc, asc
from sqlalchemy.orm import Session, RelationshipProperty, aliased
from app.models import Base
from app.security import get_password_hash
from app.log import get_logger
from app.crud.filters import buildQueryFilters

ORMModel = TypeVar("ORMModel")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

log = get_logger(__name__)


class CRUDRepository:
    """Base interface for CRUD operations."""

    def __init__(self, model: Type[ORMModel]) -> None:
        """Initialize the CRUD repository.

        Parameters:
            model (Type[ORMModel]): The ORM model to use for CRUD operations.
            To see models go to app.models module.
        """
        self._model = model
        self._name = model.__name__

    def count(self, db: Session, *args, **kwargs) -> int: 
        """
        Retrieves total records from the database.

        Parameters:
            db (Session): The database session object.
        Returns:
            Optional[ORMModel]: The total num of rows.
        """
        log.debug(
            "retrieving total records for %s",
            self._model.__name__,
        )
        query = db.query(self._model)
        # filters
        query = buildQueryFilters(self._model, query, kwargs)

        return query.count()

    def get_one(self, db: Session, *args, **kwargs) -> Optional[ORMModel]:
        """
        Retrieves one record from the database.

        Parameters:
            db (Session): The database session object.
            *args: Variable length argument list used for filter
                e.g. filter(MyClass.name == 'some name')
            **kwargs: Keyword arguments used for filter_by e.g.
                filter_by(name='some name')

        Returns:
            Optional[ORMModel]: The retrieved record, if found.
        """
        log.debug(
            "retrieving one record for %s",
            self._model.__name__,
        )
        return db.query(self._model).filter(*args).filter_by(**kwargs).first()

    def get_all(self, db: Session, *args, **kwargs) -> List[ORMModel]:
        """
        Retrieves all records from the database.

        Parameters:
            db (Session): The database session.
        Returns:
            List[ORMModel]: List of retrieved records.
        """
        log.debug(
            "retrieving all records for %s",
            self._model.__name__
        )
        return db.query(self._model).all()

    def get_many(
        self, db: Session, *args, skip: int = 0, limit: int = 100, order_by: str = 'created_at', descending: bool = False, **kwargs
    ) -> Tuple[List[ORMModel], int]:
        """
        Retrieves multiple records from the database.

        Parameters:
            db (Session): The database session.
            *args: Variable number of arguments. For example: filter
                db.query(MyClass).filter(MyClass.name == 'some name', MyClass.id > 5)
            skip (int, optional): Number of records to skip. Defaults to 0.
            limit (int, optional): Maximum number of records to retrieve.
                Defaults to 100.
            order_by (str, optional): Field name to order by. Default to 'created_at'.
            descending (bool, optional): Sort direction. Default to False.
            **kwargs: Variable number of keyword arguments. For example: filter_by
                db.query(MyClass).filter_by(name='some name', id > 5)

        Returns:
            Tuple[List[ORMModel], int]: List of retrieved records and number of records.
        """
        log.debug(
            "retrieving many records for %s ordered by %s %s with pagination skip %s and limit %s",
            self._model.__name__,
            order_by,
            'desc' if descending else 'asc',
            skip,
            limit,
        )

        query = db.query(self._model)

        # filters
        query = buildQueryFilters(self._model, query, kwargs)

        total = query.count()

        # sort by
        model_attribute = getattr(self._model, order_by, 'created_at')
        
        items = query.\
            order_by(desc(model_attribute) if descending else asc(model_attribute)).\
            offset(skip).\
            limit(limit).all()
        return (
            items,
            total
        )

    def create(self, db: Session, obj_create: CreateSchemaType) -> ORMModel:
        """
        Create a new record in the database.

        Parameters:
            db (Session): The database session.
            obj_create (CreateModelType): The data for creating the new record.
            It's a pydantic BaseModel

        Returns:
            ORMModel: The newly created record.
        """
        log.debug(
            "creating record for %s with data %s",
            str(self._model.__name__),
            obj_create.model_dump(),
        )
        obj_create_data = obj_create.model_dump(exclude_none=True, exclude_unset=True)
        db_obj = self._model(**obj_create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        db_obj: ORMModel,
        obj_update: UpdateSchemaType,
    ) -> ORMModel:
        """
        Updates a record in the database.

        Parameters:
            db (Session): The database session.
            db_obj (ORMModel): The database object to be updated.
            obj_update (UpdateModelType): The updated data for the object
                - it's a pydantic BaseModel.

        Returns:
            ORMModel: The updated database object.
        """
        log.debug(
            "updating record for %s with data %s",
            self._model.__name__,
            obj_update.model_dump(),
        )
        obj_update_data = obj_update.model_dump(
            exclude_unset=True
        )  # exclude_unset=True -
        # do not update fields with None
        for field, value in obj_update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, db_obj: ORMModel) -> ORMModel:
        """
        Deletes a record from the database.

        Parameters:
            db (Session): The database session.
            db_obj (ORMModel): The object to be deleted from the database.

        Returns:
            ORMModel: The deleted object.

        """
        log.debug("deleting record for %s with id %s", self._model.__name__, db_obj.id)
        db.delete(db_obj)
        db.commit()
        return db_obj
