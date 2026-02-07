from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)  # Using UUID string as primary key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Context State
    current_product_context = Column(JSON, nullable=True) # Stores the current product being discussed
    session_metadata = Column(JSON, nullable=True) # Any other metadata

    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False, index=True)
    role = Column(String, nullable=False) # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Metadata for the message (e.g. tokens used, model version)
    message_metadata = Column(JSON, nullable=True)

    # Relationships
    session = relationship("Session", back_populates="messages")
