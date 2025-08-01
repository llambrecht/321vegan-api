from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, select
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from app.database.base_class import Base

class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    name = Column(String, unique=True, index=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("brands.id"), nullable=True)
    children = relationship("Brand", back_populates="parent")
    parent = relationship("Brand", back_populates="children", remote_side=[id])
    products = relationship("Product", back_populates="brand")


    @hybrid_property
    def parent_name(self):
        if self.parent:
            return self.parent.name
        else:
            return None

    @parent_name.inplace.expression
    @classmethod
    def _parent_name_expression(cls):
        return Brand.parent