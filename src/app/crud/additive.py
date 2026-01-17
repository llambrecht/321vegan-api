from app.crud.base import CRUDRepository
from app.models.additive import Additive

additive_crud = CRUDRepository(model=Additive)
