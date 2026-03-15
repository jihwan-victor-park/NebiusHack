"""
ReasoningAgent — all Nebius LLM calls in one place.

  parse_intent      → ParsedIntent         (step 2)
  plan_search       → List[SearchTask]     (step 3)
  extract_indie_urls→ List[str]            (step 6)
  plan_navigation   → actions | "done"     (step 7-8)
  score_small_biz   → {score, reasoning}   (step 10)
  score_products    → sorted products      (scoring)
  pick_best         → Pick                 (final)
"""
import os, json
from openai import AsyncOpenAI
from api.models import ParsedIntent, SearchTask, Product, Pick

client = AsyncOpenAI(
    api_key=os.getenv("NEBIUS_API_KEY"),
    base_url="https://api.studio.nebius.ai/v1",
)
MODEL = "meta-llama/Llama-3.3-70B-Instruct"

BIG_TECH  = {"amazon", "walmart"}
SMALL_BIZ = {"etsy", "shopify", "indie"}


# ── Shared LLM helper ─────────────────────────────────────────────────────────

async def _llm(system: str, user: str, max_tokens: int = 1500) -> dict:
    resp = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        response_format={"type": "json_object"},
        max_tokens=max_tokens,
    )
    return json.loads(resp.choices[0].message.content)


# ── Weight presets ─────────────────────────────────────────────────────────────

DEFAULT_W = {"price": 0.30, "shipping": 0.20, "quality": 0.30, "ethics": 0.20}
PREF_W = {
    "cheapest_first":   {"price": 0.55, "shipping": 0.10, "quality": 0.20, "ethics": 0.15},
    "fastest_shipping": {"price": 0.15, "shipping": 0.50, "quality": 0.20, "ethics": 0.15},
    "prefer_local":     {"price": 0.15, "shipping": 0.10, "quality": 0.30, "ethics": 0.45},
    "eco_friendly":     {"price": 0.15, "shipping": 0.10, "quality": 0.30, "ethics": 0.45},
}
SMALL_BIZ_W = {"price": 0.20, "shipping": 0.15, "quality": 0.25, "ethics": 0.40}

def _weights(prefs: dict) -> dict:
    if prefs.get("prioritize_small_biz"):
        return SMALL_BIZ_W
    for k, w in PREF_W.items():
        if prefs.get(k):
            return w
    return DEFAULT_W


# ── Scoring (pure math) ────────────────────────────────────────────────────────

def score_products(products: list, intent: ParsedIntent, prefs: dict) -> list:
    w = _weights(prefs)
    prices = [float(p.get("price") or 0) for p in products if (p.get("price") or 0) > 0]
    max_p = intent.max_price or (max(prices) if prices else None)
    max_d = intent.max_shipping_days

    for p in products:
        price = float(p.get("price") or 0)
        days  = p.get("shipping_days")
        rating = p.get("rating")
        ethics = p.get("small_biz_score", 0.1)

        # price score
        if price <= 0:
            ps = 0.5
        elif max_p and max_p > 0:
            ps = 0.0 if price > max_p else round(1.0 - price / max_p, 3)
        elif prices:
            ps = round(1.0 - price / max(prices), 3)
        else:
            ps = 0.5

        # shipping score
        if days is None:
            ss = 0.3
        elif max_d:
            ss = 0.0 if days > max_d else round(1.0 - days / max_d, 3)
        else:
            ss = round(max(0.0, 1.0 - days / 30), 3)

        # quality score
        qs = round(min(rating / 5.0, 1.0), 3) if rating else 0.5

        p["price_score"]    = ps
        p["shipping_score"] = ss
        p["quality_score"]  = qs
        p["ethics_score"]   = round(ethics, 3)
        p["final_score"]    = round(
            w["price"] * ps + w["shipping"] * ss + w["quality"] * qs + w["ethics"] * ethics, 4
        )

    return sorted(products, key=lambda x: x["final_score"], reverse=True)


# ── LLM methods ────────────────────────────────────────────────────────────────

class ReasoningAgent:

    # Step 2 — parse intent
    async def parse_intent(self, query: str) -> ParsedIntent:
        data = await _llm(
            system=(
                "Extract structured shopping intent from the user query.\n"
                "Return JSON with keys:\n"
                "  item               (string — core product)\n"
                "  attributes         (array of strings — material, style, use case, etc.)\n"
                "  min_price          (float or null — lower bound, e.g. 30 from '$30-$60')\n"
                "  max_price          (float or null — upper bound, e.g. 60 from '$30-$60' or 'under $60')\n"
                "  max_shipping_days  (int or null)\n"
                "  preference         (string — one sentence on what matters most to the user)\n"
                "Return ONLY valid JSON."
            ),
            user=query,
        )
        return ParsedIntent(**data)

    # Step 3 — search plan
    async def plan_search(self, intent: ParsedIntent, user_location: str | None) -> list[SearchTask]:
        loc = user_location or "nearby"
        data = await _llm(
            system=(
                "You are planning search tasks for a shopping agent.\n"
                "Given a parsed intent, return a JSON object with key 'tasks': array of search tasks.\n"
                "Each task: { source, method, query }\n"
                "  source: one of amazon | etsy | google | google_maps | instagram\n"
                "  method: 'api' for amazon/etsy, 'discover' for google/maps/instagram\n"
                "  query:  the exact search string to use\n"
                "Include 5-7 tasks covering major retailers AND indie discovery.\n"
                "Return ONLY valid JSON."
            ),
            user=(
                f"Item: {intent.item}\n"
                f"Attributes: {', '.join(intent.attributes)}\n"
                f"Max price: {intent.max_price}\n"
                f"Preference: {intent.preference}\n"
                f"User location: {loc}"
            ),
        )
        return [SearchTask(**t) for t in data.get("tasks", [])]

    # Step 6 — extract indie URLs from a Google/Maps/Instagram AX tree
    async def extract_indie_urls(self, ax_text: str) -> list[str]:
        data = await _llm(
            system=(
                "You are reading the accessibility tree of a Google search results page.\n"
                "Extract all non-marketplace URLs — ignore amazon.com, walmart.com, etsy.com, ebay.com.\n"
                "Focus on small shop websites, studio sites, Shopify stores, artisan pages.\n"
                "Return JSON: { urls: [string, ...] } (up to 5 URLs)."
            ),
            user=ax_text[:10_000],
        )
        return data.get("urls", [])

    # Step 7-8 — decide: extract products now, or navigate first
    async def plan_navigation(self, ax_text: str, intent: ParsedIntent) -> dict:
        """
        Returns one of:
          { action: "extract", products: [...] }
          { action: "navigate", steps: [{action, target, value?}, ...] }
          { action: "done" }
        """
        data = await _llm(
            system=(
                "You are controlling a browser to find products on an indie shop website.\n"
                "You receive the accessibility tree of the current page.\n\n"
                "Decide what to do next. Return JSON with key 'action':\n"
                "  'extract'  — products are visible. Include key 'products': array of\n"
                "               {name, price, url, shipping_days, rating} objects.\n"
                "  'navigate' — need to navigate to find products. Include key 'steps': array of\n"
                "               {action: click|fill|scroll, target: descriptive label, value?: string}\n"
                "  'done'     — no products found and no useful navigation possible.\n\n"
                "Use 'navigate' sparingly — only if products are clearly one click away.\n"
                "Return ONLY valid JSON."
            ),
            user=(
                f"Looking for: {intent.item} ({', '.join(intent.attributes)})\n"
                f"Max price: {intent.max_price}\n\n"
                f"--- PAGE AX TREE ---\n{ax_text[:10_000]}"
            ),
            max_tokens=2000,
        )
        return data

    # Step 10 — small biz scoring
    async def score_small_biz(self, ax_text: str) -> dict:
        data = await _llm(
            system=(
                "Rate this seller on a small business / ethical sourcing scale.\n"
                "Score 0-100 based on:\n"
                "  - Solo maker or small team vs factory/corporation\n"
                "  - Handmade / artisan claims with specific details\n"
                "  - Location specificity (named studio, city, region)\n"
                "  - Years in business / personal story\n"
                "  - Materials sourcing transparency\n"
                "Return JSON: { score: int, reasoning: string (1-2 sentences) }"
            ),
            user=ax_text[:6_000],
        )
        return data

    # Final pick — choose and explain the best in a category
    async def pick_best(self, products: list, intent: ParsedIntent, category: str) -> dict | None:
        if not products:
            return None
        best = products[0]
        data = await _llm(
            system=(
                f"You are explaining why a product is the best {category} choice for a shopper.\n"
                "Write 2-3 sentences covering price value, shipping speed, quality/reviews, "
                "and ethical sourcing. Be specific and concrete.\n"
                "Return JSON: { why_best: string }"
            ),
            user=(
                f"Shopper intent: {intent.preference}\n"
                f"Chosen product: {json.dumps(best)}"
            ),
        )
        return {"product": best, "why_best": data.get("why_best", "")}
