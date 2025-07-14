from app.routes.auth import router as auth_router
from app.routes.account import router as account_router
from app.routes.user import router as user_router
from app.routes.brand import router as brand_router
from app.routes.product import router as product_router
from app.routes.cosmetic import router as cosmetic_router
from app.routes.apiclient import router as apiclient_router
from app.routes.external import router as external_router


__all__ = [
    "auth_router",
    "account_router",
    "user_router",
    "brand_router",
    "product_router",
    "cosmetic_router",
    "apiclient_router",
    "external_router",
]