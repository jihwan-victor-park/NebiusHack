from pydantic import BaseModel
from typing import Optional, List

class SearchRequest(BaseModel):
    query: str
    filters: Optional[dict] = {}

class Product(BaseModel):
    name: str
    price: float
    source: str          # amazon | walmart | etsy | shopify
    url: str
    shipping_days: Optional[int]
    rating: Optional[float]
    small_biz_score: float   # 0-1, higher = more independent seller
    reasoning: str

class SearchResponse(BaseModel):
    results: List[Product]
