"""
PlaywrightIndieScraper — deep scrape of indie shop URLs via Playwright + AX converter.

Plugs into ReasoningAgent.plan_navigation / extract_indie_urls flow:
  1. Receive indie URLs discovered by TavilyScraper.search_indie
  2. Open each in Playwright
  3. Feed AX tree text to ReasoningAgent.plan_navigation
  4. Execute any navigation steps the LLM requests
  5. Return structured products + small biz scores

Interface with teammates:
  - Input:  list of URLs (from TavilyScraper) + ParsedIntent (from ReasoningAgent)
  - Output: list of product dicts matching the agreed schema
"""
from playwright.async_api import async_playwright
from scrapers.ax_converter import get_ax_text
from agents.reasoning_agent import ReasoningAgent
from api.models import ParsedIntent


MAX_NAV_STEPS = 3  # max clicks per page before giving up


async def scrape_indie_urls(urls: list[str], intent: ParsedIntent) -> list[dict]:
    """
    Deep scrape a list of indie shop URLs using Playwright + AX tree + LLM navigation.
    Returns flat list of product dicts.
    """
    reasoner = ReasoningAgent()
    all_products = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for url in urls:
            try:
                products = await _scrape_one(browser, url, intent, reasoner)
                all_products.extend(products)
            except Exception as e:
                print(f"[playwright_indie] failed on {url}: {e}")

        await browser.close()

    return all_products


async def _scrape_one(browser, url: str, intent: ParsedIntent, reasoner: ReasoningAgent) -> list[dict]:
    page = await browser.new_page()
    await page.goto(url, wait_until="domcontentloaded", timeout=15_000)

    products = []

    for _ in range(MAX_NAV_STEPS):
        ax_text = await get_ax_text(page)
        if not ax_text.strip():
            break

        decision = await reasoner.plan_navigation(ax_text, intent)
        action = decision.get("action")

        if action == "extract":
            raw = decision.get("products", [])
            products = _stamp(raw, url)
            break

        elif action == "navigate":
            steps = decision.get("steps", [])
            navigated = await _execute_steps(page, steps)
            if not navigated:
                break  # couldn't navigate, give up

        else:  # "done" or unexpected
            break

    await page.close()
    return products


async def _execute_steps(page, steps: list[dict]) -> bool:
    """Execute navigation steps from plan_navigation. Returns True if any step succeeded."""
    success = False
    for step in steps:
        act = step.get("action")
        target = step.get("target", "")
        value = step.get("value", "")
        try:
            if act == "click":
                await page.get_by_label(target).first.click(timeout=5_000)
                await page.wait_for_load_state("domcontentloaded", timeout=8_000)
                success = True
            elif act == "fill":
                await page.get_by_label(target).first.fill(value, timeout=5_000)
                success = True
            elif act == "scroll":
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                success = True
        except Exception as e:
            print(f"[playwright_indie] step failed ({act} '{target}'): {e}")
    return success


def _stamp(products: list[dict], source_url: str) -> list[dict]:
    """Normalize product schema to match the agreed interface with Alex's frontend."""
    stamped = []
    for p in products:
        stamped.append({
            "name":              str(p.get("name") or "").strip(),
            "price":             _safe_float(p.get("price")),
            "shipping_cost":     _safe_float(p.get("shipping_cost")),
            "shipping_days":     _safe_int(p.get("shipping_days")),
            "seller":            str(p.get("seller") or "").strip(),
            "rating":            _safe_float(p.get("rating")),
            "review_count":      _safe_int(p.get("review_count")),
            "url":               str(p.get("url") or source_url).strip(),
            "image_url":         p.get("image_url"),
            "source":            "indie",
            "small_biz_score":   0.9,
            "small_biz_reasoning": "",
            "reasoning":         "",
        })
    return stamped


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
