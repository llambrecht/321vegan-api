import enum
from sqlalchemy import Column, Integer, String, Text, Boolean, Enum, DateTime
from datetime import datetime
from app.database.base_class import Base


class AdditiveStatus(str, enum.Enum):
    VEGAN = "VEGAN"
    NON_VEGAN = "NON_VEGAN"
    MAYBE_VEGAN = "MAYBE_VEGAN"


class Additive(Base):
    __tablename__ = "additives"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    e_number = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(AdditiveStatus), default=AdditiveStatus.MAYBE_VEGAN)
    source = Column(String, nullable=True)
