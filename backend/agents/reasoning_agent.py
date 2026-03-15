"""
ReasoningAgent — uses Nebius-hosted LLM to:
- Parse natural language query into structured search params
- Rank + score products with explanation
"""
import os, json
from openai import AsyncOpenAI  # Nebius API is OpenAI-compatible

client = AsyncOpenAI(
    api_key=os.getenv("NEBIUS_API_KEY"),
    base_url="https://api.studio.nebius.ai/v1",
)
MODEL = "meta-llama/Meta-Llama-3.1-70B-Instruct"

class ReasoningAgent:
    async def parse_query(self, query: str) -> dict:
        resp = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Extract search keywords, max_price, max_shipping_days from the user query. Return JSON."},
                {"role": "user", "content": query},
            ],
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)

    async def rank(self, products: list, parsed: dict) -> list:
        summary = json.dumps([{"name": p["name"], "price": p["price"], "source": p["source"]} for p in products])
        resp = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Rank these products for the user. Add a 'reasoning' field and 'small_biz_score' (0-1). Return JSON array."},
                {"role": "user", "content": f"Query context: {parsed}\nProducts: {summary}"},
            ],
            response_format={"type": "json_object"},
        )
        ranked = json.loads(resp.choices[0].message.content)
        return ranked.get("products", products)
