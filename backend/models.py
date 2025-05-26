# backend/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func # for server-side defaults like NOW()
from .db_setup import Base # Use relative import if models.py is in the same directory as db_setup.py

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    is_active = Column(Boolean, default=True) # Optional: for soft deletes or deactivation
    # is_verified = Column(Boolean, default=False) # Optional: for email verification

    # Timestamps
    # For created_at, using server_default ensures the DB handles it.
    # For updated_at, server_onupdate is more DB-specific; func.now() on update is common.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships (can be added later if UserConfiguration model is defined)
    # configurations = relationship("UserConfiguration", back_populates="user", uselist=False) # Example one-to-one
