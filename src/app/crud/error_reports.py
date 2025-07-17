from app.crud.base import CRUDRepository
from app.models.error_report import ErrorReport

error_report_crud = CRUDRepository(model=ErrorReport)