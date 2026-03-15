"""
ShoppingAgent — agentic pipeline (all scraping via Tavily).

  STEP 2  parse_intent    raw query → ParsedIntent
  STEP 3  parallel search (all via Tavily, ~2-4s total):
            Tavily → amazon.com   → LLM extracts products + images
            Tavily → etsy.com     → LLM extracts products + images
            Tavily → indie shops  → extract() deep scrape → LLM extracts + images
  STEP 4  score           weighted formula (price/shipping/quality/ethics)
  STEP 5  pick            top 3 big-tech + top 3 small-biz with LLM reasoning
"""
import asyncio
from agents.reasoning_agent import ReasoningAgent, score_products
from scrapers.tavily_scraper import TavilyScraper
from api.models import SearchRequest, SearchResponse, SearchContext, Pick, Product

BIG_TECH  = {"amazon", "walmart"}
SMALL_BIZ = {"etsy", "shopify", "indie"}


class ShoppingAgent:
    def __init__(self):
        self.reasoner = ReasoningAgent()
        self.tavily   = TavilyScraper()

    async def run(self, req: SearchRequest) -> SearchResponse:
        prefs = {
            "prefer_local":     req.prefer_local,
            "cheapest_first":   req.cheapest_first,
            "fastest_shipping": req.fastest_shipping,
            "eco_friendly":     req.eco_friendly,
        }

        # Step 2: parse intent
        intent = await self.reasoner.parse_intent(req.query)
        keywords = f"{intent.item} {' '.join(intent.attributes)}".strip()
        print(f"[agent] intent: {intent}")

        # Step 3: all searches in parallel via Tavily
        amazon_products, etsy_products, indie_products = await asyncio.gather(
            self.tavily.search_site(keywords, "amazon.com", "amazon"),
            self.tavily.search_site(keywords, "etsy.com",   "etsy"),
            self.tavily.search_indie(keywords),
            return_exceptions=True,
        )

        all_products = []
        for batch in (amazon_products, etsy_products, indie_products):
            if isinstance(batch, list):
                all_products.extend(batch)

        print(f"[agent] collected {len(all_products)} products")

        # Step 4: score
        scored = score_products(all_products, intent, prefs)

        # Step 5: split and pick top 3 each
        big_tech_list  = [p for p in scored if p.get("source") in BIG_TECH][:3]
        small_biz_list = [p for p in scored if p.get("source") in SMALL_BIZ][:3]

        big_tech_raw, small_biz_raw = await asyncio.gather(
            self.reasoner.pick_best(big_tech_list,  intent, "big retailer"),
            self.reasoner.pick_best(small_biz_list, intent, "small / independent business"),
        )

        return SearchResponse(
            best_big_tech  = _to_pick(big_tech_raw),
            best_small_biz = _to_pick(small_biz_raw),
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
