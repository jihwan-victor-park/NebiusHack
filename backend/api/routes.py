from fastapi import APIRouter
from api.models import SearchRequest, SearchResponse
from agents.shopping_agent import ShoppingAgent

router = APIRouter()
agent = ShoppingAgent()

@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    results = await agent.run(req.query, req.filters)
    return SearchResponse(results=results)

@router.post("/call")
async def call_business(business_name: str, phone: str, question: str):
    from agents.voice_agent import VoiceAgent
    return await VoiceAgent().call(business_name, phone, question)
