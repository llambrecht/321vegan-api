from app.crud.base import CRUDRepository
from app.models.partner import Partner

partner_crud = CRUDRepository(model=Partner)
