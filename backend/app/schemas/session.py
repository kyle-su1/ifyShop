from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class MessageBase(BaseModel):
    role: str
    content: str
    message_metadata: Optional[Dict[str, Any]] = None

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    session_id: str
    timestamp: datetime

    class Config:
        from_attributes = True

class SessionBase(BaseModel):
    user_id: Optional[int] = None
    session_metadata: Optional[Dict[str, Any]] = None

class SessionCreate(SessionBase):
    pass

class SessionUpdate(BaseModel):
    current_product_context: Optional[Dict[str, Any]] = None
    session_metadata: Optional[Dict[str, Any]] = None

class SessionResponse(SessionBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    current_product_context: Optional[Dict[str, Any]] = None
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True
