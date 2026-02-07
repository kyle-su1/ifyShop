from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    content = Column(Text)
    rating = Column(Float)
    source = Column(String) # e.g. "Reddit", "Amazon"
    sentiment_score = Column(Float, nullable=True)

    item = relationship("Item", backref="reviews")
