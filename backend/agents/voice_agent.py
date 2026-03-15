"""
VoiceAgent — calls a small business via Pokulab voice AI API.
"""
import os, httpx

POKULAB_API_KEY = os.getenv("POKULAB_API_KEY")
POKULAB_URL = "https://api.pokulab.com/v1/call"  # placeholder

class VoiceAgent:
    async def call(self, business_name: str, phone: str, question: str) -> dict:
        payload = {
            "to": phone,
            "script": f"Hi, I'm calling on behalf of a customer interested in {business_name}. {question}",
            "record": True,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(POKULAB_URL, json=payload, headers={"Authorization": f"Bearer {POKULAB_API_KEY}"})
            return resp.json()
