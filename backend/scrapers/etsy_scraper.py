"""
Etsy scraper using AX Tree Converter — surfaces independent makers.
"""
from playwright.async_api import async_playwright
from scrapers.ax_converter import extract_products


class EtsyScraper:
    async def search(self, keywords: str, filters: dict) -> list:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(f"https://www.etsy.com/search?q={keywords.replace(' ', '+')}")
            products, action = await extract_products(page, keywords, "etsy")
            # TODO: pass action to Lucas for navigation if needed
            await browser.close()
            return products
