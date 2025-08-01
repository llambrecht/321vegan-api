from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from app.database.base_class import Base

class ErrorReport(Base):
    __tablename__ = "error_reports"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    ean = Column(String, unique=False, index=True, nullable=False)
    comment = Column(String, nullable=False)
    contact = Column(String, nullable=True)
    handled = Column(Boolean, default=False)
    # orm only foreignkey
    product = relationship(
        'Product', 
        primaryjoin="foreign(ErrorReport.ean) == Product.ean"
    )

