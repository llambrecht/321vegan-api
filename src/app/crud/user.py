from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.crud.base import CRUDRepository
from app.models.user import User, UserRole
from app.security import verify_password, get_password_hash, generate_reset_token
from app.config import settings


class UserCRUDRepository(CRUDRepository):
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Get a user by email.

        Parameters:
            db (Session): The database session.
            email (str): The email of the user.

        Returns:
            Optional[User]: The user found by email, or None if not found.
        """
        return self.get_one(db, self._model.email == email)

    @staticmethod
    def is_super_user(user: User) -> bool:
        """
        Check if the given user is a super user (admin).

        Parameters:
            user (User): The user to check.

        Returns:
            bool: True if the user is a super user, False otherwise.
        """
        return user.role == UserRole.ADMIN

    @staticmethod
    def is_active_user(user: User) -> bool:
        """
        Check if a user is active.

        Parameters:
            user (User): The user object to check.

        Returns:
            bool: True if the user is active, False otherwise.
        """
        return user.is_active

    @staticmethod
    def deactivate_user(db: Session, user: User) -> User:
        """Deactivates a user by setting their `is_active` flag to `False`.

        Parameters:
            db (Session): The database session object.
            user (User): The user to deactivate.

        Returns:
            User: The deactivated user object.
        """
        user.is_active = False
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def authenticate_user(
        self, db: Session, email: str, password: str
    ) -> Optional[User]:
        """
        Authenticates a user with the given email and password.

        Parameters:
            db (Session): The database session object.
            email (str): The email of the user.
            password (str): The password of the user.

        Returns:
            Optional[User]: The authenticated user if successful, None otherwise.
        """
        user = self.get_user_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user
    
    def create_password_reset_token(self, db: Session, email: str) -> Optional[str]:
        """
        Create a password reset token for a user with the given email.

        Parameters:
            db (Session): The database session object.
            email (str): The email of the user.

        Returns:
            Optional[str]: The reset token if user exists, None otherwise.
        """
        user = self.get_user_by_email(db, email)
        if not user:
            return None
        
        # Generate reset token
        reset_token = generate_reset_token()
        
        # Set token and expiration
        user.reset_token = reset_token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=settings.RESET_TOKEN_EXPIRE_HOURS)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return reset_token
    
    def verify_reset_token(self, db: Session, token: str) -> Optional[User]:
        """
        Verify a password reset token and return the associated user.

        Parameters:
            db (Session): The database session object.
            token (str): The reset token to verify.

        Returns:
            Optional[User]: The user if token is valid, None otherwise.
        """
        user = self.get_one(db, User.reset_token == token)
        if not user:
            return None
        
        # Check if token has expired
        if not user.reset_token_expires or user.reset_token_expires < datetime.now():
            return None
            
        return user
    
    def reset_password(self, db: Session, token: str, new_password: str) -> Optional[User]:
        """
        Reset a user's password using a reset token.

        Parameters:
            db (Session): The database session object.
            token (str): The reset token.
            new_password (str): The new password.

        Returns:
            Optional[User]: The user if password was reset successfully, None otherwise.
        """
        user = self.verify_reset_token(db, token)
        if not user:
            return None
        
        # Update password and clear reset token
        user.password = get_password_hash(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    def clear_reset_token(self, db: Session, user: User) -> User:
        """
        Clear the password reset token for a user.

        Parameters:
            db (Session): The database session object.
            user (User): The user object.

        Returns:
            User: The updated user object.
        """
        user.reset_token = None
        user.reset_token_expires = None
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user


user_crud = UserCRUDRepository(model=User)