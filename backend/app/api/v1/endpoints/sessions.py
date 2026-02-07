from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.api import deps
from app.models.session import Session as SessionModel, Message
from app.schemas.session import SessionCreate, SessionResponse, MessageCreate, MessageResponse, SessionUpdate
from app.agent.graph import agent_app
import uuid
import logging
from typing import Dict, Any, List

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=SessionResponse)
def create_session(
    *,
    db: Session = Depends(deps.get_db),
    session_in: SessionCreate
) -> Any:
    """
    Create a new chat session.
    """
    try:
        session_id = str(uuid.uuid4())
        db_session = SessionModel(
            id=session_id,
            user_id=session_in.user_id,
            session_metadata=session_in.session_metadata
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        return db_session
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not create session")

@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    *,
    db: Session = Depends(deps.get_db),
    session_id: str
) -> Any:
    """
    Get session details and message history.
    """
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

class ChatRequest(BaseModel):
    message: str
    image: Optional[str] = None # Base64 image
    user_preferences: Optional[Dict[str, float]] = None

@router.post("/{session_id}/chat")
async def chat_message(
    *,
    db: Session = Depends(deps.get_db),
    session_id: str,
    chat_request: ChatRequest
) -> Any:
    """
    Send a message to the agent within a session.
    """
    # 1. Validate Session
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 2. Save User Message
    user_msg = Message(
        session_id=session_id,
        role="user",
        content=chat_request.message
    )
    db.add(user_msg)
    db.commit()
    
    # 3. Prepare Agent Input
    # Retrieve recent chat history from DB
    messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp).all()
    chat_history = [{"role": m.role, "content": m.content} for m in messages]
    
    # Check if this is the first interaction (Cold Start Check)
    # If using DB session, we might want to check if user has preferences manually if not passed
    # But for now we rely on what's passed or what's in the state persistence
    
    inputs = {
        "user_query": chat_request.message,
        "image_base64": chat_request.image,
        "chat_history": chat_history,
        "session_id": session_id,
        "user_preferences": chat_request.user_preferences or {} 
        # Note: In a real app, we might merge stored prefs here if not in state
    }
    
    # 4. Invoke Agent
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        # We use ainvok for async execution
        result = await agent_app.ainvoke(inputs, config=config)
        
        # 5. Extract Response
        # The agent might return different things based on the node it ended in.
        # If it ended in 'response_node' (Analysis flow), we look for 'final_recommendation'.
        # If it ended in 'chat_node', we look for 'final_recommendation' (chat_response).
        
        final_rec = result.get("final_recommendation", {})
        response_text = final_rec.get("chat_response")
        
        if not response_text:
             # Fallback if specific key is missing, try to dump the whole recommendation
             response_text = result.get("final_recommendation", {}).get("summary", "I processed your request.")
            
        # 6. Save Assistant Message
        assistant_msg = Message(
            session_id=session_id,
            role="assistant",
            content=str(response_text), # Ensure string
            message_metadata=final_rec
        )
        db.add(assistant_msg)
        db.commit()
        
        return {
            "response": response_text,
            "data": final_rec,
            "router_decision": result.get("router_decision")
        }
        
    except Exception as e:
        logger.error(f"Error in agent execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")
