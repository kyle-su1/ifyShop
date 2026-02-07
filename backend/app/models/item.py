from sqlalchemy import Column, Integer, String, Float, Text
from app.db.session import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    image_url = Column(String)
    price = Column(Float, nullable=True)
    currency = Column(String, default="USD")
