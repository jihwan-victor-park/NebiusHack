"""
ShoppingAgent — orchestrates the full search pipeline.
1. Parse user query via ReasoningAgent
2. Run scrapers in parallel
3. Rank and score results
"""
from agents.reasoning_agent import ReasoningAgent
from scrapers.amazon_scraper import AmazonScraper
from scrapers.walmart_scraper import WalmartScraper
from scrapers.etsy_scraper import EtsyScraper
import asyncio

class ShoppingAgent:
    def __init__(self):
        self.reasoner = ReasoningAgent()
        self.scrapers = [AmazonScraper(), WalmartScraper(), EtsyScraper()]

    async def run(self, query: str, filters: dict) -> list:
        parsed = await self.reasoner.parse_query(query)
        tasks = [s.search(parsed["keywords"], filters) for s in self.scrapers]
        results = await asyncio.gather(*tasks)
        products = [p for batch in results for p in batch]
        return await self.reasoner.rank(products, parsed)
