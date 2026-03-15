"""
TavilyScraper — all web scraping via Tavily API (no Playwright needed for known sites).

Three modes:
  search_site(keywords, site, source)  — site-specific search (amazon, etsy, etc.)
  search_indie(keywords)               — discover + extract indie store products
  _extract_urls(urls)                  — deep extract content from specific URLs

Images: include_images=True on every call → first image matched to each product.
"""
import os
import json
import asyncio
from openai import AsyncOpenAI
from tavily import TavilyClient

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
MODEL = "meta-llama/Llama-3.3-70B-Instruct"

llm = AsyncOpenAI(
    api_key=os.getenv("NEBIUS_API_KEY", ""),
    base_url="https://api.studio.nebius.ai/v1",
)

EXTRACT_PROMPT = """Extract product listings from these search result snippets.
Return JSON: { "products": [ { name, price, url, image_url, shipping_days, rating, review_count, seller } ] }
- price: float USD (null if unknown)
- image_url: best product image URL found in the content (null if none)
- shipping_days: int estimate (null if unknown)
- rating: float 0-5 (null if unknown)
- review_count: int (null if unknown)
- seller: seller/shop name (null if unknown)
Only real products. Return ONLY valid JSON."""

INDIE_BLOCKLIST = {
    "amazon.com", "walmart.com", "etsy.com", "ebay.com",
    "target.com", "bestbuy.com", "homedepot.com", "wayfair.com",
    "google.com", "youtube.com", "facebook.com", "instagram.com",
    "pinterest.com", "reddit.com", "twitter.com",
}

SMALL_BIZ_DEFAULTS = {"amazon": 0.1, "walmart": 0.05, "etsy": 0.85, "indie": 0.9}


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
                max_tokens=1500,
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
        Search a specific retail site via Tavily.
        e.g. search_site("red dress", "amazon.com", "amazon")
        """
        resp = await self._search(f"{keywords} site:{site}", max_results=8)
        if not resp:
            return []

        results = resp.get("results", [])
        images  = resp.get("images", [])

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
            # Fall back to snippets from the search results
            content = "\n\n".join(
                f"URL: {r.get('url','')}\nTitle: {r.get('title','')}\n{r.get('content','')}"
                for r in results
            )
            images = resp.get("images", [])
            products = await self._llm_extract(content, images, keywords, "indie")
            return self._stamp(products, "indie")

        # Step 3: deep extract indie pages
        extract_resp = await self._extract(indie_urls)
        extracted = extract_resp.get("results", [])
        images = extract_resp.get("images", [])

        content = "\n\n".join(
            f"URL: {r.get('url','')}\n{r.get('raw_content','')[:1500]}"
            for r in extracted
        )

        # Step 4: LLM extracts products
        products = await self._llm_extract(content, images, keywords, "indie")
        return self._stamp(products, "indie")
