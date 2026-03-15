"""
AX Tree Converter — universal DOM-to-semantics layer for ShopAgent.

Pipeline:
  Playwright Page → AX snapshot → flattened semantic text → Nebius LLM → product list

Interface with teammates:
  - Input:  playwright.Page object (from Jihwan)
  - Output: list of product dicts + optional action dict (to Lucas)
  - Schema: { name, price, shipping_cost, shipping_days, seller,
              rating, review_count, url, source, small_biz_score, reasoning }
"""
import json
import os
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=os.getenv("NEBIUS_API_KEY"),
    base_url="https://api.studio.nebius.ai/v1",
)
MODEL = "meta-llama/Meta-Llama-3.1-70B-Instruct"

USEFUL_ROLES = {
    "heading", "text", "link", "button", "img",
    "listitem", "article", "label", "group",
    "StaticText", "generic",
}


def flatten_ax_tree(node: dict, depth: int = 0, max_depth: int = 12) -> list[str]:
    """Recursively flatten AX tree to semantic lines, dropping noise nodes."""
    if depth > max_depth or not node:
        return []

    lines = []
    role = node.get("role", "")
    name = node.get("name", "").strip()
    value = node.get("value", "")

    if value:
        value = str(value).strip()

    # Only emit nodes that carry meaningful content
    if role in USEFUL_ROLES and (name or value):
        content = name or value
        # Skip purely whitespace or single-char noise
        if len(content) > 1:
            indent = "  " * depth
            lines.append(f"{indent}[{role}] {content}")

    for child in node.get("children", []):
        lines.extend(flatten_ax_tree(child, depth + 1, max_depth))

    return lines


async def get_ax_text(page) -> str:
    """
    Snapshot the Playwright accessibility tree and return lean semantic text.
    Typically reduces 500KB+ HTML to under 10KB.
    """
    snapshot = await page.accessibility.snapshot()
    if not snapshot:
        return ""
    lines = flatten_ax_tree(snapshot)
    return "\n".join(lines)


async def extract_products(page, query: str, source: str, max_results: int = 5) -> tuple[list[dict], dict | None]:
    """
    Main entry point. Takes a Playwright page, returns:
      - products: list of structured product dicts
      - action: { action, selector, description } if LLM needs navigation, else None

    Usage:
        products, action = await extract_products(page, query, "amazon")
        if action:
            # send action back to Jihwan/Lucas for execution
    """
    ax_text = await get_ax_text(page)

    if not ax_text.strip():
        return [], None

    prompt = _build_prompt(ax_text, query, source, max_results)

    resp = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    raw = resp.choices[0].message.content
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        return [], None

    products = _normalize_products(result.get("products", []), source)
    action = result.get("action")  # e.g. { "action": "click", "selector": "...", "description": "..." }

    return products, action


def _normalize_products(raw_products: list, source: str) -> list[dict]:
    """Ensure every product matches the agreed schema regardless of LLM output variation."""
    normalized = []
    small_biz_defaults = {"amazon": 0.1, "walmart": 0.05, "etsy": 0.9}

    for p in raw_products:
        normalized.append({
            "name": str(p.get("name", "")).strip(),
            "price": _safe_float(p.get("price")),
            "shipping_cost": _safe_float(p.get("shipping_cost")),
            "shipping_days": _safe_int(p.get("shipping_days")),
            "seller": str(p.get("seller", "")).strip(),
            "rating": _safe_float(p.get("rating")),
            "review_count": _safe_int(p.get("review_count")),
            "url": str(p.get("url", "")).strip(),
            "source": source,
            "small_biz_score": small_biz_defaults.get(source, 0.5),
            "reasoning": "",
        })

    return normalized


def _safe_float(val) -> float | None:
    if val is None:
        return None
    try:
        return float(str(val).replace("$", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> int | None:
    if val is None:
        return None
    try:
        return int(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


SYSTEM_PROMPT = """You are a product data extractor. Given a semantic accessibility tree of a shopping page, extract product listings.

Return a JSON object with:
- "products": array of product objects, each with:
    name, price (number), shipping_cost (number or null), shipping_days (number or null),
    seller (string), rating (number or null), review_count (number or null), url (string)
- "action": if you need more data (e.g. next page, expand filter), include:
    { "action": "click", "selector": "<aria-label or link text>", "description": "why" }
  Otherwise omit "action" or set to null.

Extract only real product listings. Skip ads, banners, and nav elements."""


def _build_prompt(ax_text: str, query: str, source: str, max_results: int) -> str:
    return f"""User query: "{query}"
Source site: {source}
Extract up to {max_results} products.

PAGE ACCESSIBILITY TREE:
{ax_text}"""
