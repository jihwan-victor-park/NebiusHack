"""
ConversationAgent — the agentic loop on top of ShoppingAgent.

Each turn:
  1. LLM sees conversation history + user message → decides action:
       "search"  — run fresh Tavily search with refined query
       "rerank"  — re-score existing results with new weights (user said "cheaper", etc.)
       "answer"  — just reply (user asked a question about results)
  2. Execute the action
  3. Return agent response text + updated product list

This lets users refine searches conversationally:
  "find me a red dress" → results
  "make it under $50"   → rerank / re-search with price filter
  "show more handmade"  → re-search with updated keywords
  "why is #1 ranked highest?" → answer from existing results
"""
import json
import os
from openai import AsyncOpenAI
from agents.shopping_agent import ShoppingAgent, _to_product
from agents.reasoning_agent import score_products
from api.models import ParsedIntent, SearchRequest
from api.session_store import SessionData

llm = AsyncOpenAI(
    api_key=os.getenv("NEBIUS_API_KEY", ""),
    base_url="https://api.studio.nebius.ai/v1",
)
MODEL = "meta-llama/Llama-3.3-70B-Instruct"

_shopper = ShoppingAgent()

DECISION_PROMPT = """You are ShopAgent, an AI shopping assistant.
You have conversation history and a new user message.
The user may be giving feedback on search results or asking a question.

Decide what action to take. Return JSON with:
{
  "action": "search" | "rerank" | "answer",
  "refined_query": "...",      // if action=search: the improved search query
  "prefs": {                   // if action=rerank: updated scoring preferences
    "prefer_local": bool,
    "cheapest_first": bool,
    "fastest_shipping": bool,
    "eco_friendly": bool
  },
  "response": "..."            // always: a short friendly message to the user (1-2 sentences)
}

Rules:
- Use "search" when the user changes what they want (different item, new constraints, more specific)
- Use "rerank" when the user changes HOW they want to rank (cheaper, faster, more ethical)
- Use "answer" when the user asks a question about existing results or gives simple feedback
- "response" should sound natural, confirm what you're doing
Return ONLY valid JSON."""


class ConversationAgent:

    async def chat(self, session: SessionData, user_message: str, prioritize_small_biz: bool = False, result_count: int = 3) -> dict:
        """
        Process one turn. Returns:
          { response, products, action, big_tech, small_biz }
        """
        # Append user message to history
        session.messages.append({"role": "user", "content": user_message})

        # First-ever search: skip LLM decision, always search immediately
        if not session.products:
            action   = "search"
            response = "Searching for the best options…"
            decision = {"refined_query": user_message}
        else:
            # Subsequent turns: LLM decides (rerank / search / answer)
            history_text = "\n".join(
                f"{m['role'].upper()}: {m['content']}"
                for m in session.messages[-8:]
            )
            tops = session.products[:6]
            products_summary = "\nCurrent top results:\n" + "\n".join(
                f"  {i+1}. {p.get('name','?')} — ${p.get('price',0)} ({p.get('source','?')})"
                for i, p in enumerate(tops)
            )
            resp = await llm.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": DECISION_PROMPT},
                    {"role": "user", "content": f"CONVERSATION:\n{history_text}{products_summary}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=300,
            )
            decision = json.loads(resp.choices[0].message.content)
            action   = decision.get("action", "answer")
            response = decision.get("response", "Got it!")

        # Step 2: execute
        updated_products = session.products  # default: keep existing

        if action == "search":
            query = decision.get("refined_query") or user_message
            print(f"[conv] re-searching: '{query}' result_count={result_count}")
            req = SearchRequest(query=query, result_count=result_count)
            sr  = await _shopper.run(req)
            updated_products = [p.model_dump() for p in sr.all_results]
            if prioritize_small_biz and session.intent:
                intent = ParsedIntent(**session.intent) if isinstance(session.intent, dict) else session.intent
                updated_products = score_products(updated_products, intent, {"prioritize_small_biz": True})
            session.products = updated_products
            if sr.best_big_tech:
                session.intent = sr.context.intent.model_dump()

        elif action == "rerank":
            prefs = decision.get("prefs", {})
            if prioritize_small_biz:
                prefs["prioritize_small_biz"] = True
            print(f"[conv] reranking with prefs: {prefs}")
            if session.products and session.intent:
                intent = ParsedIntent(**session.intent)
                rescored = score_products(list(session.products), intent, prefs)
                updated_products = rescored
                session.products = rescored

        # Step 3: split into big-tech / small-biz, capped by result_count
        _BIG   = {"amazon", "nordstrom", "walmart"}
        _SMOL  = {"etsy", "shopify", "indie"}
        limit  = 6 if result_count >= 4 else result_count
        big_tech  = [p for p in updated_products if p.get("source") in _BIG][:limit]
        small_biz = [p for p in updated_products if p.get("source") in _SMOL][:limit]

        # Append agent response to history
        session.messages.append({"role": "assistant", "content": response})

        return {
            "action":    action,
            "response":  response,
            "big_tech":  [_to_product(p).model_dump() for p in big_tech],
            "small_biz": [_to_product(p).model_dump() for p in small_biz],
            "all":       [_to_product(p).model_dump() for p in updated_products],
        }
