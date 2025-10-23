import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_method
from app.database.base_class import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    CONTRIBUTOR = "contributor"
    USER = "user"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    role = Column(Enum(UserRole), default=UserRole.USER)
    nickname = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    avatar = Column(String, nullable=True)
    vegan_since = Column(DateTime, nullable=True)
    nb_products_sent = Column(Integer, default=0)
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    checkings = relationship("Checking", 
        back_populates="user",
        cascade="all, delete",
        passive_deletes=True,)

    @property
    def roles(self) -> list:
        roles = list(UserRole)
        index = roles.index(self.role)
        return roles[index:]

    @hybrid_method
    def is_user_active(self) -> bool:
        return self.is_active
    
    @hybrid_method
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
    
    @hybrid_method
    def is_contributor(self) -> bool:
        return self.role == UserRole.CONTRIBUTOR
    
    @hybrid_method
    def has_role(self, role) -> bool:
        return role in self.roles()
    