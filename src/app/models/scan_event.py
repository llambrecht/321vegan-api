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
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    lookup_api_response = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    user = relationship("User")
    shop = relationship("Shop", backref="scan_events")
    
    @property
    def shop_name(self) -> str:
        """Get shop name from relationship."""
        return self.shop.name if self.shop else None