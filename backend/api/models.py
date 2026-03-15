from pydantic import BaseModel, Field
from typing import Optional, List


# ── Step 2: Intent parse output ──────────────────────────────────────────────

class ParsedIntent(BaseModel):
    item: str                          # core item, e.g. "ceramic mug"
    attributes: List[str] = []         # ["handmade", "hand-thrown", "stoneware"]
    max_price: Optional[float] = None
    max_shipping_days: Optional[int] = None
    preference: str = ""               # free-text user preference summary


# ── Step 3: Search plan ───────────────────────────────────────────────────────

class SearchTask(BaseModel):
    source: str    # amazon | etsy | google | google_maps | instagram
    method: str    # api | discover
    query: str


# ── Core product ──────────────────────────────────────────────────────────────

class Product(BaseModel):
    name: str
    price: float = 0.0
    source: str
    url: str = ""
    image_url: Optional[str] = None    # product image
    shipping_days: Optional[int] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    small_biz_score: float = 0.1       # 0-1, higher = more independent
    small_biz_reasoning: str = ""
    reasoning: str = ""
    # scoring breakdown (filled by score_products)
    final_score: float = 0.0
    price_score: float = 0.0
    shipping_score: float = 0.0
    quality_score: float = 0.0
    ethics_score: float = 0.0


# ── Final picks ───────────────────────────────────────────────────────────────

class Pick(BaseModel):
    product: Product
    why_best: str     # LLM explanation of why this is the top choice


# ── Search context (returned for transparency) ────────────────────────────────

class SearchContext(BaseModel):
    intent: ParsedIntent
    search_tasks: List[SearchTask] = []
    iterations: int = 1
    total_found: int = 0


# ── Request / Response ────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    user_location: Optional[str] = None   # for Google Maps local search
    prefer_local: bool = False
    cheapest_first: bool = False
    fastest_shipping: bool = False
    eco_friendly: bool = False


class SearchResponse(BaseModel):
    best_big_tech: Optional[Pick] = None    # top from amazon / walmart
    best_small_biz: Optional[Pick] = None   # top from etsy / indie sites
    all_results: List[Product] = []
    context: SearchContext
