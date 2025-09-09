from app.crud.base import CRUDRepository
from app.models.brand import Brand

brand_crud = CRUDRepository(model=Brand)