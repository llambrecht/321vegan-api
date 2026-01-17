from app.crud.base import CRUDRepository
from app.models.household_cleaner import HouseholdCleaner

household_cleaner_crud = CRUDRepository(model=HouseholdCleaner)
