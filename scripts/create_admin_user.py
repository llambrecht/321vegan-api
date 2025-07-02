from functools import partial
from sqlalchemy.orm import Session
from src.app.schemas.user import UserCreate 
from src.app.crud import user_crud
from src.app.database.session import build_sqlalchemy_database_url_from_env
from src.app.log import get_logger
from src.app.database.db import get_ctx_db
from src.app.security import get_password_hash
from src.app.config import settings

log = get_logger(__name__)

DATABASE_URL = build_sqlalchemy_database_url_from_env(settings)

def _create_first_admin_user(
    db: Session,
    role: str,
    email: str,
    nickname: str,
    password: str,
    is_active: bool = True,
):
    """Create first user"""
    # Check if admin user already exists
    existing_admin = user_crud.get_user_by_email(db, email=email)
    if existing_admin:
        log.debug("Admin user already exists")
        return existing_admin

    # Create admin user
    admin_user = UserCreate(
        role=role,
        email= email,
        nickname=nickname,
        is_active=is_active,
        password= get_password_hash(password),
    )
    user = user_crud.create(db, obj_create=admin_user)
    log.debug("Admin user created successfully: %s", user)
    return user

def create_admin_user(db):
    return _create_first_admin_user(
        db,
        role='admin', 
        email=settings.USER_ADMIN_EMAIL, 
        nickname=settings.USER_ADMIN_NICKNAME, 
        is_active=True,
        password=settings.USER_ADMIN_PASSWORD, 
    )

def populate_admin_user():
    get_db = partial(get_ctx_db, database_url=DATABASE_URL)
    with get_db() as session:
        superuser = create_admin_user(session)
        superuser_id = superuser.id


if __name__ == "__main__":
    populate_admin_user()