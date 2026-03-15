"""
Etsy scraper using Playwright — surfaces independent makers.
"""
from playwright.async_api import async_playwright

class EtsyScraper:
    async def search(self, keywords: str, filters: dict) -> list:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(f"https://www.etsy.com/search?q={keywords.replace(' ', '+')}")
            items = await page.query_selector_all(".listing-link")
            products = []
            for item in items[:5]:
                name = await item.get_attribute("aria-label") or ""
                products.append({
                    "name": name,
                    "price": 0.0,
                    "source": "etsy",
                    "url": await item.get_attribute("href") or "",
                    "shipping_days": 7,
                    "rating": None,
                    "small_biz_score": 0.9,
                    "reasoning": "",
                })
            await browser.close()
            return products
