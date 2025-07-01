from app.crud.base import CRUDRepository
from app.models.product import Product

product_crud = CRUDRepository(model=Product)