"""
TavilyScraper — all web scraping via Tavily API (no Playwright needed for known sites).

Three modes:
  search_site(keywords, site, source)  — site-specific search (amazon, etsy, etc.)
  search_indie(keywords)               — discover + extract indie store products
  _extract_urls(urls)                  — deep extract content from specific URLs

Images: include_images=True on every call → first image matched to each product.
"""
import os
import re
import json
import asyncio
from openai import AsyncOpenAI
from tavily import TavilyClient

IMG_RE = re.compile(
    r'https?://[^\s"\'<>\]]+\.(?:jpg|jpeg|png|webp|gif)(?:\?[^\s"\'<>\]]*)?',
    re.IGNORECASE,
)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
MODEL = "meta-llama/Llama-3.3-70B-Instruct"

llm = AsyncOpenAI(
    api_key=os.getenv("NEBIUS_API_KEY", ""),
    base_url="https://api.studio.nebius.ai/v1",
)

EXTRACT_PROMPT = """Extract individual product listings from the content below.
Each content block starts with "URL: <url>" — use that exact URL for the product's url field.
Return JSON: { "products": [ { name, price, url, image_url, shipping_days, rating, review_count, seller } ] }

Field rules:
- name: product title
- price: float USD — scan for "$29.99", "29.99", "USD 29.99", "Price: 30" patterns (null only if truly absent)
- url: copy the URL from the "URL:" line at the start of that product's content block — never use a search page URL
- image_url: pick the best matching product image from the Available images list (null if none)
- shipping_days: int — "2-day"→2, "Prime"→2, "standard"→5, "ships in X days"→X, null if unknown
- rating: float 0-5 — look for "4.5 out of 5", "★4.2", "4.5 stars" (null if absent)
- review_count: int — look for "(1,234 reviews)", "1234 ratings" (null if absent)
- seller: seller/shop name (null if unknown)

One product per URL block. Return ONLY valid JSON."""

INDIE_BLOCKLIST = {
    "amazon.com", "walmart.com", "etsy.com", "ebay.com",
    "target.com", "bestbuy.com", "homedepot.com", "wayfair.com",
    "google.com", "youtube.com", "facebook.com", "instagram.com",
    "pinterest.com", "reddit.com", "twitter.com",
}

SMALL_BIZ_DEFAULTS = {"amazon": 0.1, "walmart": 0.05, "etsy": 0.85, "indie": 0.9}

# site: query scoped to product-page paths → every result is a real product
SITE_PRODUCT_QUERY = {
    "amazon":  "site:amazon.com/dp/",
    "etsy":    "site:etsy.com/listing/",
    "walmart": "site:walmart.com/ip/",
}

def _dedup(images: list[str], limit: int = 15) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for img in images:
        if img not in seen:
            seen.add(img)
            out.append(img)
        if len(out) >= limit:
            break
    return out

def _fill_images(products: list[dict], images: list[str]) -> None:
    """Assign unused Tavily images to products that the LLM left without one."""
    used = {p.get("image_url") for p in products if p.get("image_url")}
    spare = [img for img in images if img not in used]
    spare_iter = iter(spare)
    for p in products:
        if not p.get("image_url"):
            p["image_url"] = next(spare_iter, None)


class TavilyScraper:
    def __init__(self):
        self._client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

    # ── Internal sync wrappers (Tavily SDK is sync) ───────────────────────────

    def _do_search(self, query: str, max_results: int = 8) -> dict:
        if not self._client:
            return {}
        try:
            return self._client.search(
                query=query,
                search_depth="basic",
                max_results=max_results,
                include_images=True,
                include_raw_content=False,
            )
        except Exception as e:
            print(f"[tavily] search error '{query}': {e}")
            return {}

    def _do_search_advanced(self, query: str, max_results: int = 8) -> dict:
        """Advanced depth — Tavily crawls each result page, content includes prices."""
        if not self._client:
            return {}
        try:
            return self._client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_images=True,
                include_raw_content=False,
            )
        except Exception as e:
            print(f"[tavily] advanced search error '{query}': {e}")
            return {}

    def _do_extract(self, urls: list[str]) -> dict:
        if not self._client or not urls:
            return {}
        try:
            return self._client.extract(
                urls=urls,
                include_images=True,
            )
        except Exception as e:
            print(f"[tavily] extract error: {e}")
            return {}

    async def _search(self, query: str, max_results: int = 8) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._do_search, query, max_results)

    async def _search_advanced(self, query: str, max_results: int = 8) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._do_search_advanced, query, max_results)

    async def _extract(self, urls: list[str]) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._do_extract, urls)

    # ── LLM product extraction ────────────────────────────────────────────────

    async def _llm_extract(self, content: str, images: list[str], keywords: str, source: str) -> list[dict]:
        image_hint = "\n".join(f"Image: {img}" for img in images[:10])
        try:
            resp = await llm.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": EXTRACT_PROMPT},
                    {"role": "user", "content": (
                        f"Query: {keywords}\nSource: {source}\n\n"
                        f"{content[:7000]}\n\n"
                        f"Available images (match to products):\n{image_hint}"
                    )},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=900,
            )
            data = json.loads(resp.choices[0].message.content)
            return data.get("products", [])
        except Exception as e:
            print(f"[tavily:{source}] LLM error: {e}")
            return []

    def _stamp(self, products: list[dict], source: str) -> list[dict]:
        """Stamp source + small_biz_score + default nulls onto every product."""
        for p in products:
            p["source"] = source
            p["small_biz_score"] = SMALL_BIZ_DEFAULTS.get(source, 0.5)
            p.setdefault("reasoning", "")
            p.setdefault("small_biz_reasoning", "")
            for f in ("price", "shipping_days", "rating", "review_count", "seller", "url", "image_url"):
                p.setdefault(f, None)
        return products

    # ── Public API ────────────────────────────────────────────────────────────

    async def search_site(self, keywords: str, site: str, source: str) -> list[dict]:
        """
        Uses a path-scoped site: query (e.g. site:amazon.com/dp/) so every
        result is a real product page — no search/category pages slip through.
        """
        site_q = SITE_PRODUCT_QUERY.get(source, f"site:{site}")
        query  = f"{keywords} {site_q}"
        resp   = await self._search(query, max_results=8)
        if not resp:
            return []

        results = resp.get("results", [])
        images  = _dedup(resp.get("images", []))

        print(f"[tavily:{source}] '{query}' → {len(results)} results")

        content = "\n\n".join(
            f"URL: {r.get('url','')}\nTitle: {r.get('title','')}\n{r.get('content','')}"
            for r in results
        )
        products = await self._llm_extract(content, images, keywords, source)
        return self._stamp(products, source)

    async def search_indie(self, keywords: str) -> list[dict]:
        """
        1. Tavily search for indie/small shop results
        2. Filter out marketplace domains
        3. Tavily extract() on the indie URLs for deeper content + images
        4. LLM extracts products from extracted content
        """
        # Step 1: discover indie URLs via search
        resp = await self._search(
            f"{keywords} buy small shop independent handmade",
            max_results=10,
        )
        if not resp:
            return []

        results = resp.get("results", [])

        # Step 2: filter to indie URLs only
        indie_urls = []
        for r in results:
            url = r.get("url", "")
            domain = url.split("/")[2].replace("www.", "") if "://" in url else ""
            if domain and not any(b in domain for b in INDIE_BLOCKLIST):
                indie_urls.append(url)

        indie_urls = indie_urls[:5]
        print(f"[tavily] {len(indie_urls)} indie URLs found")

        if not indie_urls:
            content  = "\n\n".join(
                f"URL: {r.get('url','')}\nTitle: {r.get('title','')}\n{r.get('content','')}"
                for r in results
            )
            images   = _dedup(resp.get("images", []))
            products = await self._llm_extract(content, images, keywords, "indie")
            stamped  = self._stamp(products, "indie")
            _fill_images(stamped, images)
            return [p for p in stamped if p.get("image_url")]

        # Step 3: deep extract indie pages
        extract_resp = await self._extract(indie_urls)
        extracted = extract_resp.get("results", [])

        # Collect images: from Tavily response + scraped from raw_content
        images: list[str] = list(extract_resp.get("images", []))
        content_parts = []
        for r in extracted:
            raw = r.get("raw_content", "") or ""
            content_parts.append(f"URL: {r.get('url','')}\n{raw[:1500]}")
            # parse any image URLs embedded in the raw content
            found = IMG_RE.findall(raw)
            images.extend(found[:8])

        # Deduplicate images, keep first 15
        seen: set[str] = set()
        unique_images: list[str] = []
        for img in images:
            if img not in seen:
                seen.add(img)
                unique_images.append(img)
            if len(unique_images) >= 15:
                break

        content = "\n\n".join(content_parts)

        # Step 4: LLM extracts products — fill missing images, then filter
        products = await self._llm_extract(content, unique_images, keywords, "indie")
        stamped  = self._stamp(products, "indie")
        _fill_images(stamped, unique_images)
        return [p for p in stamped if p.get("image_url")]
