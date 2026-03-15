"""
ShoppingAgent — fast pipeline using only SerpAPI (no LLM on the search path).

  STEP 1  regex price extraction  — instant, no LLM
  STEP 2  parallel SerpAPI calls  — Amazon + Google Shopping (~3-5s total)
  STEP 3  score                   — weighted formula
"""
import re
import asyncio
from agents.reasoning_agent import score_products
from scrapers.serpapi_scraper import search_amazon, search_shopping
from api.models import SearchRequest, SearchResponse, SearchContext, Pick, Product, ParsedIntent

# ── Fast regex price extraction (replaces LLM parse_intent) ──────────────────

_RANGE_RE = re.compile(
    r'\$?\s*(\d+(?:\.\d+)?)\s*[-–to]+\s*\$?\s*(\d+(?:\.\d+)?)', re.I
)
_MAX_RE = re.compile(
    r'(?:under|below|max|within|less\s+than)\s*\$?\s*(\d+(?:\.\d+)?)', re.I
)
_MIN_RE = re.compile(
    r'(?:over|above|min|at\s+least|more\s+than)\s*\$?\s*(\d+(?:\.\d+)?)', re.I
)

def _parse_price(query: str) -> tuple[float | None, float | None, str]:
    """Returns (min_price, max_price, clean_keywords)."""
    m = _RANGE_RE.search(query)
    if m:
        return float(m.group(1)), float(m.group(2)), _RANGE_RE.sub("", query).strip()
    min_m = _MIN_RE.search(query)
    max_m = _MAX_RE.search(query)
    clean = query
    if min_m: clean = _MIN_RE.sub("", clean, count=1)
    if max_m: clean = _MAX_RE.sub("", clean, count=1)
    return (
        float(min_m.group(1)) if min_m else None,
        float(max_m.group(1)) if max_m else None,
        clean.strip(),
    )


# ── Agent ─────────────────────────────────────────────────────────────────────

class ShoppingAgent:
    async def run(self, req: SearchRequest) -> SearchResponse:
        prefs = {
            "prefer_local":     req.prefer_local,
            "cheapest_first":   req.cheapest_first,
            "fastest_shipping": req.fastest_shipping,
            "eco_friendly":     req.eco_friendly,
        }

        # Step 1: instant price extraction (no LLM)
        min_price, max_price, keywords = _parse_price(req.query)
        intent = ParsedIntent(
            item=keywords or req.query,
            min_price=min_price,
            max_price=max_price,
            preference=req.query,
        )
        print(f"[agent] keywords='{keywords}' price={min_price}-{max_price}")

        # fetch_n: how many results to pull per source
        fetch_n = {1: 4, 2: 6, 3: 8}.get(req.result_count, 12)

        # Step 2: two parallel SerpAPI calls only — no Tavily, no LLM
        amazon_products, shopping_products = await asyncio.gather(
            search_amazon(keywords or req.query,
                          num=fetch_n, min_price=min_price, max_price=max_price),
            search_shopping(keywords or req.query,
                            num=fetch_n, min_price=min_price, max_price=max_price),
            return_exceptions=True,
        )

        all_products: list[dict] = []
        seen_urls:   set[str]   = set()
        for batch in (amazon_products, shopping_products):
            if not isinstance(batch, list):
                continue
            for p in batch:
                url = p.get("url") or ""
                if url and url in seen_urls:
                    continue
                seen_urls.add(url)
                all_products.append(p)

        print(f"[agent] collected {len(all_products)} products")

        # Step 3: score
        scored = score_products(all_products, intent, prefs)

        return SearchResponse(
            best_big_tech  = None,
            best_small_biz = None,
            all_results    = [_to_product(p) for p in scored],
            context        = SearchContext(
                intent      = intent,
                iterations  = 1,
                total_found = len(all_products),
            ),
        )


def _to_product(d: dict) -> Product:
    return Product(
        name             = str(d.get("name") or ""),
        price            = float(d.get("price") or 0),
        source           = str(d.get("source") or ""),
        url              = str(d.get("url") or ""),
        image_url        = d.get("image_url"),
        shipping_days    = d.get("shipping_days"),
        rating           = d.get("rating"),
        review_count     = d.get("review_count"),
        small_biz_score  = float(d.get("small_biz_score") or 0),
        small_biz_reasoning = str(d.get("small_biz_reasoning") or ""),
        reasoning        = str(d.get("reasoning") or ""),
        final_score      = float(d.get("final_score") or 0),
        price_score      = float(d.get("price_score") or 0),
        shipping_score   = float(d.get("shipping_score") or 0),
        quality_score    = float(d.get("quality_score") or 0),
        ethics_score     = float(d.get("ethics_score") or 0),
    )


def _to_pick(raw: dict | None) -> Pick | None:
    if not raw or not raw.get("product"):
        return None
    return Pick(product=_to_product(raw["product"]), why_best=raw.get("why_best", ""))
