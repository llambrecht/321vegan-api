from app.crud.base import CRUDRepository
from app.models.apiclient import ApiClient

apiclient_crud = CRUDRepository(model=ApiClient)