from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base_class import Base


class Partner(Base):
    __tablename__ = "partners"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    name = Column(String, unique=True, index=True, nullable=False)
    url = Column(String, nullable=False)
    logo_path = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    discount_text = Column(String, nullable=True)
    discount_code = Column(String, nullable=True)
    is_affiliate = Column(Boolean, default=False, nullable=False)
    show_code_in_website = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    category_id = Column(Integer, ForeignKey("partner_categories.id"), nullable=True)

    # Relationship with category
    category = relationship("PartnerCategory", back_populates="partners")
