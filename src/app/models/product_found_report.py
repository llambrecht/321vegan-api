from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base_class import Base


class ProductFoundReport(Base):
    __tablename__ = "product_found_reports"

    id = Column(Integer, primary_key=True, index=True)
    ean = Column(String, nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"),
                     nullable=False, index=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.now,
                        nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="found_reports")
    shop = relationship("Shop", back_populates="found_reports")
