from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base_class import Base


class ScanEvent(Base):
    __tablename__ = "scan_events"

    id = Column(Integer, primary_key=True, index=True)
    date_created = Column(DateTime, default=datetime.now, nullable=False)
    ean = Column(String, nullable=False, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    shop_name = Column(String, nullable=True)
    lookup_api_response = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationship with user
    user = relationship("User")