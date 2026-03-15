"""
Amazon scraper using Playwright accessibility tree.
"""
from playwright.async_api import async_playwright

class AmazonScraper:
    async def search(self, keywords: str, filters: dict) -> list:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(f"https://www.amazon.com/s?k={keywords.replace(' ', '+')}")
            # Extract product cards from accessibility tree
            items = await page.query_selector_all("[data-component-type='s-search-result']")
            products = []
            for item in items[:5]:
                name = await item.query_selector("h2")
                price = await item.query_selector(".a-price-whole")
                products.append({
                    "name": await name.inner_text() if name else "",
                    "price": float(await price.inner_text().replace(",", "") if price else 0),
                    "source": "amazon",
                    "url": "",
                    "shipping_days": 2,
                    "rating": None,
                    "small_biz_score": 0.1,
                    "reasoning": "",
                })
            await browser.close()
            return products
