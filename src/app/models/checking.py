import enum
from datetime import datetime
from sqlalchemy import Column, Integer, Text, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from app.database.base_class import Base


class CheckingStatus(str, enum.Enum):
    PENDING = "PENDING"
    VEGAN = "VEGAN"
    NON_VEGAN = "NON_VEGAN"

class Checking(Base):
    __tablename__ = "checkings"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    requested_on = Column(DateTime, default=datetime.now)
    responded_on = Column(DateTime, nullable=True)
    status = Column(Enum(CheckingStatus), default=CheckingStatus.PENDING)
    response = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="checkings")
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    product = relationship("Product", back_populates="checkings")