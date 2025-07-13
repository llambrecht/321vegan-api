from app.crud.base import CRUDRepository
from app.models.cosmetic import Cosmetic

cosmetic_crud = CRUDRepository(model=Cosmetic)