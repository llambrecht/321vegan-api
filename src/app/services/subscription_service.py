import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.crud.subscription import subscription_crud
from app.models.subscription import (
    Subscription,
    SubscriptionPlatform,
    SubscriptionStatus,
    SubscriptionEventType,
)
from app.log import get_logger

log = get_logger(__name__)


class SubscriptionService:
    """Service for handling in-app purchase subscription verification and webhooks."""

    # ──────────────────────────────────────────────
    # Apple App Store Server API v2
    # ──────────────────────────────────────────────

    def verify_apple_transaction(self, transaction_id: str) -> Optional[dict]:
        """
        Verify a transaction with Apple App Store Server API v2.
        Uses the appstoreserverlibrary package.

        Returns decoded transaction info dict or None if invalid.
        """
        try:
            from appstoreserverlibrary.api_client import AppStoreServerAPIClient
            from appstoreserverlibrary.models.Environment import Environment

            private_key = self._read_apple_private_key()
            if not private_key:
                log.error("Apple private key not configured")
                return None

            environment = Environment.PRODUCTION
            if settings.ENV in ("local", "test", "dev"):
                environment = Environment.SANDBOX

            client = AppStoreServerAPIClient(
                signing_key=private_key,
                key_id=settings.APPLE_KEY_ID,
                issuer_id=settings.APPLE_ISSUER_ID,
                bundle_id=settings.APPLE_BUNDLE_ID,
                environment=environment,
            )

            transaction_info = client.get_transaction_info(transaction_id)

            from appstoreserverlibrary.signed_data_verifier import SignedDataVerifier
            from appstoreserverlibrary.models.Environment import Environment as Env

            verifier = SignedDataVerifier(
                root_certificates=[],  # Apple root certs are bundled in the library
                enable_online_checks=True,
                environment=environment,
                bundle_id=settings.APPLE_BUNDLE_ID,
                app_apple_id=None,
            )

            decoded = verifier.verify_and_decode_transaction(
                transaction_info.signedTransactionInfo
            )

            return {
                "original_transaction_id": decoded.originalTransactionId,
                "transaction_id": decoded.transactionId,
                "product_id": decoded.productId,
                "expires_date": datetime.fromtimestamp(
                    decoded.expiresDate / 1000, tz=timezone.utc
                ) if decoded.expiresDate else None,
                "raw": transaction_info.__dict__,
            }

        except Exception as e:
            log.error(f"Apple transaction verification failed: {str(e)}")
            return None

    def process_apple_webhook(self, signed_payload: str, db: Session) -> bool:
        """
        Process an Apple App Store Server Notification V2.
        The payload is a signed JWS that we decode and verify.
        """
        try:
            from appstoreserverlibrary.signed_data_verifier import SignedDataVerifier
            from appstoreserverlibrary.models.Environment import Environment

            environment = Environment.PRODUCTION
            if settings.ENV in ("local", "test", "dev"):
                environment = Environment.SANDBOX

            verifier = SignedDataVerifier(
                root_certificates=[],
                enable_online_checks=True,
                environment=environment,
                bundle_id=settings.APPLE_BUNDLE_ID,
                app_apple_id=None,
            )

            notification = verifier.verify_and_decode_notification(signed_payload)
            notification_type = notification.notificationType
            transaction_info = verifier.verify_and_decode_transaction(
                notification.data.signedTransactionInfo
            )

            original_tx_id = transaction_info.originalTransactionId
            subscription = subscription_crud.get_by_original_transaction_id(db, original_tx_id)
            if not subscription:
                log.warning(f"Apple webhook: subscription not found for {original_tx_id}")
                return False

            event_type, new_status = self._map_apple_notification(notification_type)

            if new_status:
                expires_at = None
                if transaction_info.expiresDate:
                    expires_at = datetime.fromtimestamp(
                        transaction_info.expiresDate / 1000, tz=timezone.utc
                    )
                subscription_crud.update_status(
                    db, subscription, new_status,
                    expires_at=expires_at,
                    transaction_id=transaction_info.transactionId,
                )

            if event_type:
                subscription_crud.create_event(
                    db, subscription.id, event_type,
                    platform_event_data={"notification_type": notification_type},
                )

            return True

        except Exception as e:
            log.error(f"Apple webhook processing failed: {str(e)}")
            return False

    # ──────────────────────────────────────────────
    # Google Play Developer API
    # ──────────────────────────────────────────────

    def verify_google_purchase(self, purchase_token: str, product_id: str) -> Optional[dict]:
        """
        Verify a subscription purchase with Google Play Developer API.
        Uses google-api-python-client with a service account.

        Returns subscription info dict or None if invalid.
        """
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            credentials = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_SERVICE_ACCOUNT_PATH,
                scopes=["https://www.googleapis.com/auth/androidpublisher"],
            )

            service = build("androidpublisher", "v3", credentials=credentials)

            result = service.purchases().subscriptionsv2().get(
                packageName=settings.GOOGLE_PLAY_PACKAGE_NAME,
                token=purchase_token,
            ).execute()

            # Extract the latest line item for expiry info
            line_items = result.get("lineItems", [])
            expiry_time = None
            if line_items:
                expiry_str = line_items[0].get("expiryTime")
                if expiry_str:
                    expiry_time = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))

            return {
                "original_transaction_id": result.get("linkedPurchaseToken", purchase_token),
                "purchase_token": purchase_token,
                "product_id": product_id,
                "expires_date": expiry_time,
                "subscription_state": result.get("subscriptionState"),
                "raw": result,
            }

        except Exception as e:
            log.error(f"Google purchase verification failed: {str(e)}")
            return None

    def process_google_webhook(self, message_data: dict, db: Session) -> bool:
        """
        Process a Google Real-Time Developer Notification.
        message_data is the decoded Pub/Sub message data.
        """
        try:
            notification = message_data.get("subscriptionNotification")
            if not notification:
                log.warning("Google webhook: no subscriptionNotification in payload")
                return False

            purchase_token = notification.get("purchaseToken")
            notification_type = notification.get("notificationType")

            # Call Google API to get current subscription state
            product_id = notification.get("subscriptionId", "")
            verified = self.verify_google_purchase(purchase_token, product_id)
            if not verified:
                log.error("Google webhook: could not verify purchase token")
                return False

            original_tx_id = verified["original_transaction_id"]
            subscription = subscription_crud.get_by_original_transaction_id(db, original_tx_id)
            if not subscription:
                log.warning(f"Google webhook: subscription not found for {original_tx_id}")
                return False

            event_type, new_status = self._map_google_notification(notification_type)

            if new_status:
                subscription_crud.update_status(
                    db, subscription, new_status,
                    expires_at=verified.get("expires_date"),
                )

            if event_type:
                subscription_crud.create_event(
                    db, subscription.id, event_type,
                    platform_event_data={"notification_type": notification_type, "raw": verified.get("raw")},
                )

            return True

        except Exception as e:
            log.error(f"Google webhook processing failed: {str(e)}")
            return False

    # ──────────────────────────────────────────────
    # Shared verification flow
    # ──────────────────────────────────────────────

    def process_verification(
        self,
        db: Session,
        user_id: int,
        platform: str,
        transaction_id: Optional[str],
        purchase_token: Optional[str],
        product_id: str,
    ) -> Optional[Subscription]:
        """
        Main verification flow called from the /subscriptions/verify endpoint.
        Validates with Apple/Google, upserts subscription, logs event, grants badge.
        """
        if platform == SubscriptionPlatform.APPLE:
            if not transaction_id:
                log.error("Apple verification requires transaction_id")
                return None
            verified = self.verify_apple_transaction(transaction_id)
        elif platform == SubscriptionPlatform.GOOGLE:
            if not purchase_token:
                log.error("Google verification requires purchase_token")
                return None
            verified = self.verify_google_purchase(purchase_token, product_id)
        else:
            log.error(f"Unknown platform: {platform}")
            return None

        if not verified:
            return None

        original_tx_id = verified["original_transaction_id"]

        # Upsert subscription
        subscription = subscription_crud.get_by_original_transaction_id(db, original_tx_id)
        if subscription:
            subscription_crud.update_status(
                db, subscription, SubscriptionStatus.ACTIVE,
                expires_at=verified.get("expires_date"),
                transaction_id=verified.get("transaction_id"),
            )
            event_type = SubscriptionEventType.RENEWAL
        else:
            subscription = Subscription(
                user_id=user_id,
                platform=platform,
                original_transaction_id=original_tx_id,
                transaction_id=verified.get("transaction_id"),
                purchase_token=verified.get("purchase_token"),
                product_id=verified.get("product_id", product_id),
                status=SubscriptionStatus.ACTIVE,
                expires_at=verified.get("expires_date"),
            )
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
            event_type = SubscriptionEventType.INITIAL_PURCHASE

        # Log event
        subscription_crud.create_event(
            db, subscription.id, event_type,
            platform_event_data=verified.get("raw"),
        )

        # Grant permanent supporter badge
        subscription_crud.grant_supporter_badge(db, user_id)

        return subscription

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _read_apple_private_key(self) -> Optional[str]:
        try:
            with open(settings.APPLE_PRIVATE_KEY_PATH, "r") as f:
                return f.read()
        except Exception as e:
            log.error(f"Could not read Apple private key: {str(e)}")
            return None

    @staticmethod
    def _map_apple_notification(notification_type: str) -> tuple[Optional[SubscriptionEventType], Optional[SubscriptionStatus]]:
        """Map Apple notification type to our event type and subscription status."""
        mapping = {
            "DID_RENEW": (SubscriptionEventType.RENEWAL, SubscriptionStatus.ACTIVE),
            "DID_CHANGE_RENEWAL_STATUS": (SubscriptionEventType.CANCELLATION, None),  # auto-renew toggled off, still active until expires_at
            "EXPIRED": (SubscriptionEventType.EXPIRY, SubscriptionStatus.EXPIRED),
            "GRACE_PERIOD_EXPIRED": (SubscriptionEventType.EXPIRY, SubscriptionStatus.EXPIRED),
            "DID_FAIL_TO_RENEW": (SubscriptionEventType.GRACE_PERIOD, SubscriptionStatus.GRACE_PERIOD),
            "REFUND": (SubscriptionEventType.REFUND, SubscriptionStatus.CANCELLED),
            "SUBSCRIBED": (SubscriptionEventType.INITIAL_PURCHASE, SubscriptionStatus.ACTIVE),
        }
        return mapping.get(notification_type, (None, None))

    @staticmethod
    def _map_google_notification(notification_type: int) -> tuple[Optional[SubscriptionEventType], Optional[SubscriptionStatus]]:
        """Map Google RTDN notification type (int) to our event type and subscription status."""
        # Google notification types: https://developer.android.com/google/play/billing/rtdn-reference
        mapping = {
            1: (SubscriptionEventType.RENEWAL, SubscriptionStatus.ACTIVE),           # SUBSCRIPTION_RECOVERED
            2: (SubscriptionEventType.RENEWAL, SubscriptionStatus.ACTIVE),           # SUBSCRIPTION_RENEWED
            3: (SubscriptionEventType.CANCELLATION, None),                           # SUBSCRIPTION_CANCELED (still active until period end)
            4: (SubscriptionEventType.INITIAL_PURCHASE, SubscriptionStatus.ACTIVE),  # SUBSCRIPTION_PURCHASED
            5: (SubscriptionEventType.GRACE_PERIOD, SubscriptionStatus.GRACE_PERIOD),# SUBSCRIPTION_ON_HOLD
            6: (SubscriptionEventType.GRACE_PERIOD, SubscriptionStatus.GRACE_PERIOD),# SUBSCRIPTION_IN_GRACE_PERIOD
            7: (SubscriptionEventType.RENEWAL, SubscriptionStatus.ACTIVE),           # SUBSCRIPTION_RESTARTED
            12: (SubscriptionEventType.REFUND, SubscriptionStatus.CANCELLED),        # SUBSCRIPTION_REVOKED
            13: (SubscriptionEventType.EXPIRY, SubscriptionStatus.EXPIRED),          # SUBSCRIPTION_EXPIRED
        }
        return mapping.get(notification_type, (None, None))


subscription_service = SubscriptionService()
