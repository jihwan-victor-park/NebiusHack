# ShopAgent

> AI-powered shopping assistant that finds the best deal across big retailers and indie shops — powered by Nebius LLM.

---

## What it does

You describe what you want in plain English. ShopAgent searches Amazon, Etsy, and independent shops in parallel, ranks results by price, shipping, quality, and ethical sourcing, then presents a side-by-side comparison. You can refine conversationally — "make it under $40", "fastest shipping", "more handmade" — and the agent re-searches or re-ranks without starting over.

---

## Architecture

### Full system flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     BROWSER  (localhost:3000)                    │
│                                                                  │
│   ┌──────────────┐   wrong creds   ┌──────────────────────┐    │
│   │  Login Page  │ ◄─────────────  │    Error message      │    │
│   └──────┬───────┘                 └──────────────────────┘    │
│          │ correct creds                                         │
│          ▼                                                       │
│   ┌──────────────────────────────────────────────────────┐      │
│   │                     Main App UI                       │      │
│   │   Search bar → user types query → Enter / Search      │      │
│   │   [Sign out] → clears state → back to Login Page      │      │
│   └──────────────────────┬───────────────────────────────┘      │
└─────────────────────────-│───────────────────────────────────────┘
                           │  POST /session/{id}/chat
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND  (:8000)                       │
│                                                                  │
│   POST /session            →  session_store.create()            │
│   POST /session/{id}/chat  →  ConversationAgent.chat()          │
│   POST /search             →  ShoppingAgent.run()  (direct)     │
│   POST /call               →  VoiceAgent.call()                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ConversationAgent                            │
│                                                                  │
│   1. Appends user message to session history                    │
│   2. Nebius LLM decides action:                                 │
│                                                                  │
│      "search"  ──►  ShoppingAgent.run(refined_query)           │
│      "rerank"  ──►  score_products() with new pref weights      │
│      "answer"  ──►  reply from existing results (no new search) │
│                                                                  │
│   3. Splits results  →  big_tech  /  small_biz                  │
│   4. Returns { action, response, big_tech, small_biz }          │
└──────────────────────────┬──────────────────────────────────────┘
                           │  on "search"
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ShoppingAgent                               │
│                                                                  │
│   1. ReasoningAgent.parse_intent()  →  ParsedIntent             │
│      { item, attributes, max_price, max_shipping_days }         │
│                                                                  │
│   2. Parallel Tavily searches                                    │
│                                                                  │
│      ┌──────────────┬──────────────┬─────────────────┐         │
│      │ Amazon       │ Etsy         │ Indie shops      │         │
│      │ (Tavily API) │ (Tavily API) │ (Tavily API)     │         │
│      └──────┬───────┴──────┬───────┴───────┬──────────┘         │
│             └──────────────┴───────────────┘                    │
│                            │                                     │
│               TavilyScraper._llm_extract()                       │
│               Nebius LLM reads snippets                          │
│               → [{ name, price, url, image_url, … }]            │
│                            │                                     │
│   3. score_products()  →  price / shipping / quality / ethics   │
│   4. pick_best() × 2  →  Nebius LLM writes why_best explanation │
│   5. →  SearchResponse                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

### Universal web scraping — AX Tree layer

```
┌─────────────────────────────────────────────────────────────────┐
│              AX Tree Converter  (ax_converter.py)                │
│                                                                  │
│   Raw HTML / DOM  (500 KB+)                                     │
│          │                                                       │
│          ▼                                                       │
│   page.accessibility.snapshot()   ←  Playwright built-in        │
│          │                                                       │
│          ▼                                                       │
│   flatten_ax_tree()                                             │
│   keeps: heading · text · link · button · article · label       │
│   drops: scripts · styles · nav boilerplate · tracking          │
│          │                                                       │
│          ▼                                                       │
│   Clean semantic text  (~8 KB)   ~95% token reduction           │
│          │                                                       │
│          ▼                                                       │
│   Nebius LLM  →  { name, price, shipping_cost, shipping_days,   │
│                    seller, rating, review_count, url }           │
└─────────────────────────────────────────────────────────────────┘
```

---

### Indie shop deep-scrape loop

```
┌─────────────────────────────────────────────────────────────────┐
│            PlaywrightIndieScraper  (playwright_indie_scraper.py) │
│                                                                  │
│   Tavily discovers indie URL                                    │
│          │                                                       │
│          ▼                                                       │
│   Playwright opens page                                         │
│          │                                                       │
│          ▼                                                       │
│   ax_converter.get_ax_text()  →  semantic tree                  │
│          │                                                       │
│          ▼                                                       │
│   ReasoningAgent.plan_navigation()                              │
│          │                                                       │
│     ┌────┴──────────────────────┐                               │
│     │                           │                               │
│  "extract"                  "navigate"              "done"      │
│     │                           │                    │          │
│     ▼                    click / scroll              ▼          │
│  Products                 reload page            No results     │
│  returned            ◄────────────── (max 3 iterations)        │
└─────────────────────────────────────────────────────────────────┘
```

---

### Conversational refinement loop

```
  User: "find me a handmade ceramic mug under $40"
        │
        ▼
  ConversationAgent  →  action: "search"
        │
        ▼
  ShoppingAgent searches  →  results displayed
        │
  User: "make it faster shipping"
        │
        ▼
  ConversationAgent  →  action: "rerank"
        │                 (no new search — re-scores existing results
        ▼                  with fastest_shipping weight boosted)
  Updated ranking displayed
        │
  User: "why is #1 ranked highest?"
        │
        ▼
  ConversationAgent  →  action: "answer"
                        (Nebius LLM answers from existing results,
                         no search or rerank)
```

---

### Data flow back to the UI

```
  ShoppingAgent / ConversationAgent
        │
        ▼
  { big_tech: Product[], small_biz: Product[] }
        │                       │
        ▼                       ▼
  ProductGrid             ProductGrid
  "Big Retailers"         "Small & Independent"
  Amazon · Walmart        Etsy · Indie shops
        │                       │
        └───────────┬───────────┘
                    ▼
              ProductCard × N
         name · price · image
         ┌─────────────────────┐
         │ Price     ████░░  72│
         │ Shipping  ██░░░░  41│
         │ Quality   █████░  89│
         │ Ethics    ███░░░  60│
         └─────────────────────┘
```

---

## Product schema

Every scraper outputs this shape — guaranteed by `_normalize_products()`:

```json
{
  "name":               "Handmade Ceramic Mug, Ocean Blue",
  "price":              32.00,
  "shipping_cost":      0.00,
  "shipping_days":      5,
  "seller":             "CeramicsByJane",
  "rating":             4.8,
  "review_count":       847,
  "url":                "https://...",
  "image_url":          "https://...",
  "source":             "etsy",
  "small_biz_score":    0.9,
  "final_score":        0.81,
  "price_score":        0.75,
  "shipping_score":     0.60,
  "quality_score":      0.96,
  "ethics_score":       0.90
}
```

---

## Running locally

**1. Add your API keys to `.env`:**

```
NEBIUS_API_KEY=...
TAVILY_API_KEY=...
```

**2. Backend:**

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**3. Frontend:**

```bash
cd frontend
npm install
npm run dev
```

**4. Open** http://localhost:3000

Login: `team` / `shopagent2024`

---

## Team

| Module | Owner |
|---|---|
| AX Tree Converter + Playwright indie scraper | dvila |
| Tavily scraper + Playwright setup | Jihwan |
| Scoring + conversation agent | Lucas |
| Frontend UI | Alex |
