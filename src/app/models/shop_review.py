import enum
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, Enum, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base_class import Base


class ShopReviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ShopReview(Base):
    __tablename__ = "shop_reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_shop_review_rating"),
        UniqueConstraint("shop_id", "user_id", name="uq_shop_review_shop_user"),
    )

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    status = Column(Enum(ShopReviewStatus), nullable=False, default=ShopReviewStatus.PENDING, index=True)
    date_created = Column(DateTime, default=datetime.now, nullable=False, index=True)

    # Relationships
    user = relationship("User")
    shop = relationship("Shop", backref="reviews")
