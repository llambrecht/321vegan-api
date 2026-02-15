from app.crud.base import CRUDRepository
from app.models.partner_category import PartnerCategory

partner_category_crud = CRUDRepository(model=PartnerCategory)
