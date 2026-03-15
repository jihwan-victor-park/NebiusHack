"""
Amazon scraper using AX Tree Converter.
"""
from playwright.async_api import async_playwright
from scrapers.ax_converter import extract_products


class AmazonScraper:
    async def search(self, keywords: str, filters: dict) -> list:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(f"https://www.amazon.com/s?k={keywords.replace(' ', '+')}")
            products, action = await extract_products(page, keywords, "amazon")
            # TODO: pass action to Lucas for navigation if needed
            await browser.close()
            return products
