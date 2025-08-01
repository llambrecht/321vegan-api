from app.crud.base import CRUDRepository
from app.models.checking import Checking

checking_crud = CRUDRepository(model=Checking)