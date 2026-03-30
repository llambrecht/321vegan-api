from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base_class import Base


class ProductNotFoundReport(Base):
    __tablename__ = "product_not_found_reports"

    id = Column(Integer, primary_key=True, index=True)
    ean = Column(String, nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    date_created = Column(DateTime, default=datetime.now, nullable=False, index=True)

    # Relationships
    user = relationship("User")
    shop = relationship("Shop", backref="not_found_reports")
