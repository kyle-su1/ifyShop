from sqlalchemy import Column, Integer, String, JSON
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    auth0_id = Column(String, unique=True, index=True)
    preferences = Column(JSON, default={}) # Stores: cost_weight, quality_weight, environment_weight
