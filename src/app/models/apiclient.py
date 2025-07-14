from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from datetime import datetime
from app.database.base_class import Base
from app.security import generate_api_key

class ApiClient(Base):
    __tablename__ = "api_clients"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    name = Column(String, unique=True, nullable=False)
    api_key = Column(String, nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=False)
