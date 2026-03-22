import json
from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.crud.base import CRUDRepository
from app.models.subscription import (
    Subscription,
    SubscriptionEvent,
    SubscriptionStatus,
    SubscriptionEventType,
)
from app.models.user import User
from app.log import get_logger

log = get_logger(__name__)


class SubscriptionCRUDRepository(CRUDRepository):
    def get_active_by_user_id(self, db: Session, user_id: int) -> Optional[Subscription]:
        return db.query(self._model).filter(
            self._model.user_id == user_id,
            self._model.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.GRACE_PERIOD])
        ).first()

    def get_by_user_id(self, db: Session, user_id: int) -> Optional[Subscription]:
        return db.query(self._model).filter(
            self._model.user_id == user_id
        ).order_by(self._model.created_at.desc()).first()

    def get_by_original_transaction_id(self, db: Session, original_transaction_id: str) -> Optional[Subscription]:
        return self.get_one(db, self._model.original_transaction_id == original_transaction_id)

    def create_event(
        self,
        db: Session,
        subscription_id: int,
        event_type: SubscriptionEventType,
        platform_event_data: Optional[dict] = None,
    ) -> SubscriptionEvent:
        event = SubscriptionEvent(
            subscription_id=subscription_id,
            event_type=event_type,
            platform_event_data=json.dumps(platform_event_data) if platform_event_data else None,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def get_events_by_subscription_id(
        self, db: Session, subscription_id: int, skip: int = 0, limit: int = 50
    ) -> tuple[list[SubscriptionEvent], int]:
        query = db.query(SubscriptionEvent).filter(
            SubscriptionEvent.subscription_id == subscription_id
        )
        total = query.count()
        items = query.order_by(SubscriptionEvent.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def update_status(
        self,
        db: Session,
        subscription: Subscription,
        status: SubscriptionStatus,
        expires_at: Optional[datetime] = None,
        transaction_id: Optional[str] = None,
    ) -> Subscription:
        subscription.status = status
        if expires_at is not None:
            subscription.expires_at = expires_at
        if transaction_id is not None:
            subscription.transaction_id = transaction_id
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        return subscription

    def count_active(self, db: Session) -> int:
        return db.query(self._model).filter(
            self._model.status == SubscriptionStatus.ACTIVE
        ).count()

    def grant_supporter_badge(self, db: Session, user_id: int) -> None:
        """Set the supporter badge permanently. Once granted, never revoked."""
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.supporter == 0:
            user.supporter = 1
            db.add(user)
            db.commit()


subscription_crud = SubscriptionCRUDRepository(model=Subscription)
