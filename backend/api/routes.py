from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.models import SearchRequest, SearchResponse
from api.session_store import create, get
from agents.shopping_agent import ShoppingAgent
from agents.conversation_agent import ConversationAgent

router = APIRouter()
shopper  = ShoppingAgent()
conv     = ConversationAgent()


# ── One-shot search (kept for backwards compat) ───────────────────────────────

@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    return await shopper.run(req)


# ── Session: create ───────────────────────────────────────────────────────────

@router.post("/session")
async def create_session():
    s = create()
    return {"session_id": s.id}


# ── Session: chat turn ────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str

@router.post("/session/{session_id}/chat")
async def chat(session_id: str, req: ChatRequest):
    session = get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    result = await conv.chat(session, req.message)
    return result


# ── Session: get history ──────────────────────────────────────────────────────

@router.get("/session/{session_id}")
async def get_session(session_id: str):
    session = get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session.id,
        "messages":   session.messages,
        "products":   session.products[:6],
    }


# ── Voice call ────────────────────────────────────────────────────────────────

@router.post("/call")
async def call_business(business_name: str, phone: str, question: str):
    from agents.voice_agent import VoiceAgent
    return await VoiceAgent().call(business_name, phone, question)
