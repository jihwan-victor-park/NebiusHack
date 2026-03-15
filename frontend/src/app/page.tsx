"use client";
import { useState, useRef } from "react";
import ProductGrid from "@/components/ProductGrid";
import LoadingState from "@/components/LoadingState";

export interface Product {
  name: string;
  price: number | null;
  source: string;
  url: string;
  image_url: string | null;
  shipping_days: number | null;
  rating: number | null;
  review_count: number | null;
  small_biz_score: number;
  reasoning: string;
  final_score: number;
  price_score: number;
  shipping_score: number;
  quality_score: number;
  ethics_score: number;
}

const API = "http://localhost:8000";

const EXAMPLES = [
  "Handmade ceramic mug under $40",
  "Organic cotton tote bag",
  "Vintage leather wallet",
  "Red dress under $60",
];

export default function Home() {
  const [sessionId, setSessionId]           = useState<string | null>(null);
  const [query, setQuery]                   = useState("");
  const [agentMsg, setAgentMsg]             = useState<string | null>(null);
  const [action, setAction]                 = useState<string | null>(null);
  const [bigTech, setBigTech]               = useState<Product[]>([]);
  const [smallBiz, setSmallBiz]             = useState<Product[]>([]);
  const [history, setHistory]               = useState<string[]>([]);
  const [loading, setLoading]               = useState(false);
  const [resultCount, setResultCount]       = useState<number>(3);
  const [prioritizeSmallBiz, setPrioritize] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const hasResults = bigTech.length > 0 || smallBiz.length > 0;

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res  = await fetch(`${API}/session`, { method: "POST" });
    const data = await res.json();
    setSessionId(data.session_id);
    return data.session_id;
  }

  async function handleSend(override?: string) {
    const text = (override ?? query).trim();
    if (!text || loading) return;
    setLoading(true);
    setAgentMsg(null);
    const sid = await ensureSession();
    try {
      const res  = await fetch(`${API}/session/${sid}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, prioritize_small_biz: prioritizeSmallBiz, result_count: resultCount }),
      });
      const data = await res.json();
      setAgentMsg(data.response ?? null);
      setAction(data.action ?? null);
      if (data.big_tech?.length || data.small_biz?.length) {
        setBigTech(data.big_tech  ?? []);
        setSmallBiz(data.small_biz ?? []);
      }
      setHistory(prev => [...prev, text]);
      setQuery("");
      inputRef.current?.focus();
    } catch {
      setAgentMsg("Something went wrong — please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col">

      {/* ── Header ───────────────────────────────────────────────── */}
      <header className="sticky top-0 z-20 bg-white/80 backdrop-blur border-b border-[#ebebeb]">
        <div className="max-w-5xl mx-auto px-6 py-4 space-y-3">

          {/* Brand row */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold tracking-tight text-[#111]">ShopAgent</span>
              <span className="text-[10px] text-[#999] border border-[#ddd] rounded-full px-2 py-0.5 tracking-wide">
                NEBIUS AI
              </span>
            </div>
            {sessionId && (
              <span className="text-[10px] text-[#bbb] font-mono">#{sessionId}</span>
            )}
          </div>

          {/* Search bar */}
          <div className="flex gap-2">
            <input
              ref={inputRef}
              className="flex-1 bg-white border border-[#e2e0dc] rounded-lg px-4 py-2.5 text-sm
                         text-[#111] placeholder:text-[#bbb]
                         focus:outline-none focus:border-[#bbb] shadow-sm transition-all"
              placeholder={
                hasResults
                  ? 'Refine: "under $40" · "fastest shipping" · "more handmade"'
                  : 'What are you looking for? e.g. "handmade ceramic mug under $40"'
              }
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSend()}
              disabled={loading}
            />
            <button
              onClick={() => handleSend()}
              disabled={!query.trim() || loading}
              className="bg-[#111] text-white text-sm font-medium px-5 py-2.5 rounded-lg
                         hover:bg-[#333] active:scale-95 transition-all
                         disabled:opacity-30 disabled:cursor-not-allowed shadow-sm"
            >
              {loading ? "…" : hasResults ? "Refine" : "Search"}
            </button>
          </div>

          {/* Controls row: result count + small biz toggle */}
          <div className="flex items-center gap-4">
            {/* How many results */}
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-[#bbb] tracking-wide uppercase">Show</span>
              {[1, 2, 3, 4].map(n => (
                <button
                  key={n}
                  onClick={() => setResultCount(n)}
                  className={`text-[11px] rounded-full px-2.5 py-0.5 border transition-all ${
                    resultCount === n
                      ? "bg-[#111] text-white border-[#111]"
                      : "bg-white text-[#888] border-[#ddd] hover:border-[#bbb]"
                  }`}
                >
                  {n === 4 ? "4+" : n}
                </button>
              ))}
            </div>

            <div className="w-px h-3 bg-[#e0dedd]" />

            {/* Prioritize small biz */}
            <label className="flex items-center gap-1.5 cursor-pointer select-none">
              <div
                onClick={() => setPrioritize(v => !v)}
                className={`w-3.5 h-3.5 rounded border flex items-center justify-center transition-all ${
                  prioritizeSmallBiz
                    ? "bg-emerald-500 border-emerald-500"
                    : "bg-white border-[#ddd]"
                }`}
              >
                {prioritizeSmallBiz && (
                  <svg width="8" height="6" viewBox="0 0 8 6" fill="none">
                    <path d="M1 3l2 2 4-4" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                )}
              </div>
              <span
                onClick={() => setPrioritize(v => !v)}
                className={`text-[11px] transition-colors ${prioritizeSmallBiz ? "text-emerald-600 font-medium" : "text-[#888]"}`}
              >
                Prioritize small businesses
              </span>
            </label>
          </div>

          {/* Refinement chips */}
          {history.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {history.map((h, i) => (
                <span key={i}
                  className="text-[11px] bg-white border border-[#e2e0dc] rounded-full px-2.5 py-0.5 text-[#888]">
                  {h}
                </span>
              ))}
            </div>
          )}

          {/* Agent status */}
          {agentMsg && !loading && (
            <div className="flex items-center gap-1.5">
              {action === "search" && <span className="text-[10px] text-[#888] tracking-wide uppercase">New search</span>}
              {action === "rerank" && <span className="text-[10px] text-[#888] tracking-wide uppercase">Re-ranked</span>}
              <span className="text-[10px] text-[#aaa]">·</span>
              <p className="text-xs text-[#888]">{agentMsg}</p>
            </div>
          )}
        </div>
      </header>

      {/* ── Body ─────────────────────────────────────────────────── */}
      <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-8">

        {/* Empty state */}
        {!hasResults && !loading && (
          <div className="flex flex-col items-center gap-5 pt-20 text-center">
            <p className="text-2xl font-semibold text-[#111] tracking-tight">
              Find the best product — big or indie
            </p>
            <p className="text-sm text-[#999] max-w-sm leading-relaxed">
              Searches Amazon, Etsy & independent shops. Ranks by price,
              shipping speed, quality and ethical sourcing.
            </p>
            <div className="flex flex-wrap justify-center gap-2 mt-1">
              {EXAMPLES.map(ex => (
                <button key={ex} onClick={() => handleSend(ex)}
                  className="text-xs border border-[#ddd] bg-white rounded-full px-3.5 py-1.5
                             text-[#666] hover:border-[#bbb] hover:text-[#333] transition-all shadow-sm">
                  {ex}
                </button>
              ))}
            </div>
          </div>
        )}

        {loading && <LoadingState />}

        {/* Results */}
        {hasResults && !loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
            <ProductGrid
              title="Amazon · Nordstrom"
              accent="blue"
              products={bigTech}
              limit={resultCount}
            />
            <ProductGrid
              title="Small & Independent"
              accent="green"
              products={smallBiz}
              limit={resultCount}
            />
          </div>
        )}
      </main>
    </div>
  );
}
