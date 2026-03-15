"""
SerpAPI scrapers.

  search_amazon(keywords)    → Amazon products via engine=amazon (real prices)
  search_shopping(keywords)  → Google Shopping (Etsy, Nordstrom, indie shops)
"""
import os
import asyncio
import requests

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY", "")
SERPAPI_URL = "https://serpapi.com/search.json"

BIG_TECH  = {"amazon", "nordstrom"}
SMALL_BIZ = {"etsy", "indie"}

SMALL_BIZ_SCORE = {
    "amazon":   0.10,
    "nordstrom":0.15,
    "etsy":     0.85,
    "indie":    0.90,
}


# ── Shared helpers ────────────────────────────────────────────────────────────

def _parse_shipping(delivery: str) -> int | None:
    if not delivery:
        return None
    d = delivery.lower()
    if "same day"  in d:                     return 0
    if "next day"  in d or "overnight" in d: return 1
    if "2-day"     in d or "2 day"     in d: return 2
    if "3-day"     in d or "3 day"     in d: return 3
    if "free"      in d:                     return 4
    if "standard"  in d:                     return 7
    return None

def _base(source: str) -> dict:
    return {
        "source":              source,
        "small_biz_score":     SMALL_BIZ_SCORE.get(source, 0.70),
        "reasoning":           "",
        "small_biz_reasoning": "",
        "shipping_days":       None,
        "seller":              "",
    }


# ── Amazon (engine=amazon) ────────────────────────────────────────────────────

def _parse_amazon_item(item: dict) -> dict:
    p = _base("amazon")
    p["name"]         = item.get("title") or ""
    p["price"]        = item.get("extracted_price")       # float or None
    p["url"]          = item.get("link") or ""
    p["image_url"]    = item.get("thumbnail")
    p["rating"]       = item.get("rating")
    p["review_count"] = item.get("reviews")               # int or None
    # Prime badge → 2-day shipping
    if item.get("is_prime"):
        p["shipping_days"] = 2
    return p

def _price_suffix(min_price: float | None, max_price: float | None) -> str:
    if min_price is not None and max_price is not None:
        return f" ${int(min_price)}-${int(max_price)}"
    if max_price is not None:
        return f" under ${int(max_price)}"
    if min_price is not None:
        return f" over ${int(min_price)}"
    return ""


def _do_amazon(keywords: str, num: int = 8,
               min_price: float | None = None,
               max_price: float | None = None) -> list[dict]:
    if not SERPAPI_KEY:
        return []
    k = keywords + _price_suffix(min_price, max_price)
    params: dict = {
        "engine":  "amazon",
        "k":       k,
        "api_key": SERPAPI_KEY,
    }
    # Also pass API-level price filters for Amazon engine
    if min_price is not None:
        params["low_price"]  = int(min_price)
    if max_price is not None:
        params["high_price"] = int(max_price)
    try:
        resp = requests.get(SERPAPI_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[serpapi:amazon] error: {e}")
        return []

    results  = (data.get("organic_results") or data.get("search_results") or [])[:num]
    products = [_parse_amazon_item(r) for r in results if r.get("title")]
    print(f"[serpapi:amazon] {len(products)} products")
    return products

async def search_amazon(keywords: str, num: int = 8,
                        min_price: float | None = None,
                        max_price: float | None = None) -> list[dict]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _do_amazon, keywords, num, min_price, max_price)


# ── Google Shopping (Etsy, Nordstrom, other retailers) ───────────────────────

def _detect_source_shopping(item: dict) -> str:
    s = (item.get("source") or "").lower()
    l = (item.get("link")   or "").lower()
    if "nordstrom" in s or "nordstrom.com" in l: return "nordstrom"
    if "etsy"      in s or "etsy.com"      in l: return "etsy"
    if "amazon"    in s or "amazon.com"    in l: return "amazon"   # just in case
    if "walmart"   in s or "walmart.com"   in l: return "amazon"   # lump into big tech
    return "indie"

def _parse_shopping_item(item: dict) -> dict:
    source = _detect_source_shopping(item)
    p = _base(source)
    p["name"]         = item.get("title") or ""
    p["price"]        = item.get("extracted_price")
    # Try multiple URL fields — Google Shopping may use different keys
    p["url"]          = (item.get("link")
                         or item.get("product_link")
                         or item.get("seller_link")
                         or "")
    p["image_url"]    = item.get("thumbnail")
    p["rating"]       = item.get("rating")
    p["review_count"] = item.get("reviews")
    p["shipping_days"]= _parse_shipping(item.get("delivery") or "")
    p["seller"]       = item.get("source") or ""
    return p

def _do_shopping(keywords: str, num: int = 8,
                 min_price: float | None = None,
                 max_price: float | None = None) -> list[dict]:
    if not SERPAPI_KEY:
        return []
    q = keywords + _price_suffix(min_price, max_price)
    try:
        resp = requests.get(
            SERPAPI_URL,
            params={
                "engine":  "google_shopping",
                "q":       q,
                "api_key": SERPAPI_KEY,
                "num":     num,
                "hl":      "en",
                "gl":      "us",
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[serpapi:shopping] error: {e}")
        return []

    results  = data.get("shopping_results", [])[:num]
    products = [_parse_shopping_item(r) for r in results if r.get("title")]
    print(f"[serpapi:shopping] {len(products)} products (requested {num})")
    return products

async def search_shopping(keywords: str, num: int = 8,
                          min_price: float | None = None,
                          max_price: float | None = None) -> list[dict]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _do_shopping, keywords, num, min_price, max_price)
