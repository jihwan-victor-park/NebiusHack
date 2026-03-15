"use client";
import { useState, useRef } from "react";
import ProductGrid from "@/components/ProductGrid";
import LoadingState from "@/components/LoadingState";

const DEMO_USER = "team";
const DEMO_PASS = "shopagent2024";

export interface Product {
  name: string;
  price: number;
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

export default function Home() {
  // ── Auth ──────────────────────────────────────────────────────────────────
  const [authed, setAuthed]       = useState(false);
  const [loginUser, setLoginUser] = useState("");
  const [loginPass, setLoginPass] = useState("");
  const [loginErr, setLoginErr]   = useState(false);

  // ── App ───────────────────────────────────────────────────────────────────
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [query, setQuery]         = useState("");
  const [agentMsg, setAgentMsg]   = useState<string | null>(null);
  const [action, setAction]       = useState<string | null>(null);
  const [bigTech, setBigTech]     = useState<Product[]>([]);
  const [smallBiz, setSmallBiz]   = useState<Product[]>([]);
  const [history, setHistory]     = useState<string[]>([]);
  const [loading, setLoading]     = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // ── Auth handlers ─────────────────────────────────────────────────────────
  function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    if (loginUser.trim() === DEMO_USER && loginPass === DEMO_PASS) {
      setAuthed(true);
      setLoginErr(false);
    } else {
      setLoginErr(true);
    }
  }

  function handleLogout() {
    setAuthed(false);
    setLoginUser("");
    setLoginPass("");
    setLoginErr(false);
    // clear app state
    setSessionId(null);
    setQuery("");
    setAgentMsg(null);
    setAction(null);
    setBigTech([]);
    setSmallBiz([]);
    setHistory([]);
  }

  // ── Search handlers ───────────────────────────────────────────────────────
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
    setAction(null);

    const sid = await ensureSession();

    try {
      const res = await fetch(`${API}/session/${sid}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
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

  const hasResults = bigTech.length > 0 || smallBiz.length > 0;

  // ── Login screen ──────────────────────────────────────────────────────────
  if (!authed) return (
    <div className="min-h-screen bg-[#0f0f0f] text-white flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-8">

        {/* Brand */}
        <div className="text-center space-y-1">
          <p className="font-bold text-xl tracking-tight">ShopAgent</p>
          <p className="text-white/35 text-sm">powered by Nebius</p>
        </div>

        {/* Card */}
        <div className="bg-white/5 border border-white/10 rounded-2xl px-8 py-8 space-y-5">
          <p className="text-sm text-white/50">Sign in to continue</p>
          <form onSubmit={handleLogin} className="space-y-3">
            <input
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm
                         placeholder:text-white/25 focus:outline-none focus:border-white/30 transition-all"
              placeholder="Username"
              value={loginUser}
              onChange={e => { setLoginUser(e.target.value); setLoginErr(false); }}
              autoComplete="username"
              autoFocus
            />
            <input
              type="password"
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm
                         placeholder:text-white/25 focus:outline-none focus:border-white/30 transition-all"
              placeholder="Password"
              value={loginPass}
              onChange={e => { setLoginPass(e.target.value); setLoginErr(false); }}
              autoComplete="current-password"
            />
            {loginErr && (
              <p className="text-red-400/70 text-xs">Incorrect username or password.</p>
            )}
            <button
              type="submit"
              disabled={!loginUser.trim() || !loginPass}
              className="w-full bg-white text-black font-medium py-3 rounded-xl text-sm
                         hover:bg-white/90 active:scale-[0.98] transition-all
                         disabled:opacity-30 disabled:cursor-not-allowed mt-1"
            >
              Sign in
            </button>
          </form>
        </div>
      </div>
    </div>
  );

  // ── Main app (only rendered when authed) ──────────────────────────────────
  return (
    <div className="min-h-screen bg-[#0f0f0f] text-white flex flex-col">

      {/* ── Sticky top bar ─────────────────────────────────────────────── */}
      <div className="sticky top-0 z-20 bg-[#0f0f0f]/95 backdrop-blur border-b border-white/10">
        <div className="max-w-5xl mx-auto px-6 py-4 space-y-3">

          {/* Brand row + sign out */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-bold tracking-tight">ShopAgent</span>
              <span className="text-xs text-white/35 border border-white/10 rounded-full px-2 py-0.5">
                powered by Nebius
              </span>
            </div>
            <button
              onClick={handleLogout}
              className="text-xs text-white/30 hover:text-white/60 transition-colors"
            >
              Sign out
            </button>
          </div>

          {/* Search bar */}
          <div className="flex gap-2">
            <input
              ref={inputRef}
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm
                         placeholder:text-white/25 focus:outline-none focus:border-white/30 transition-all"
              placeholder={
                hasResults
                  ? 'Refine: "under $40", "fastest shipping", "more handmade"…'
                  : 'e.g. "red dress under $60, ships in a week"'
              }
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSend()}
              disabled={loading}
            />
            <button
              onClick={() => handleSend()}
              disabled={!query.trim() || loading}
              className="bg-white text-black font-medium px-6 py-3 rounded-xl text-sm
                         hover:bg-white/90 active:scale-95 transition-all
                         disabled:opacity-30 disabled:cursor-not-allowed"
            >
              {loading ? "…" : hasResults ? "Refine" : "Search"}
            </button>
          </div>

          {/* Refinement history chips */}
          {history.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {history.map((h, i) => (
                <span
                  key={i}
                  className="text-xs bg-white/5 border border-white/10 rounded-full px-2.5 py-0.5 text-white/40"
                >
                  {h}
                </span>
              ))}
            </div>
          )}

          {/* Agent response / action label */}
          {agentMsg && (
            <div className="flex items-center gap-2">
              {action === "search"  && <span className="text-xs text-blue-400/70">🔍 New search</span>}
              {action === "rerank"  && <span className="text-xs text-purple-400/70">↕ Re-ranked</span>}
              {action === "answer"  && <span className="text-xs text-white/30">💬</span>}
              <p className="text-sm text-white/50">{agentMsg}</p>
            </div>
          )}
        </div>
      </div>

      {/* ── Body ───────────────────────────────────────────────────────── */}
      <div className="flex-1 max-w-5xl mx-auto w-full px-6 py-8">

        {/* Empty state */}
        {!hasResults && !loading && (
          <div className="flex flex-col items-center justify-center gap-4 pt-24 text-center">
            <p className="text-3xl font-bold">Find the best deal — big or indie</p>
            <p className="text-white/40 text-sm max-w-md">
              Describe what you want. We search Amazon, Etsy & indie shops,
              then rank by price, shipping, quality and ethics.
            </p>
            <div className="flex flex-wrap justify-center gap-2 mt-2">
              {[
                "Red dress under $60",
                "Handmade ceramic mug under $40",
                "Organic cotton tote bag",
                "Vintage leather wallet, ethically made",
              ].map(ex => (
                <button
                  key={ex}
                  onClick={() => handleSend(ex)}
                  className="text-xs border border-white/10 rounded-full px-3 py-1.5
                             text-white/40 hover:text-white/70 hover:border-white/25 transition-all"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        )}

        {loading && <LoadingState />}

        {/* Results */}
        {hasResults && !loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <ProductGrid
              title="Big Retailers"
              badge="Amazon · Walmart"
              badgeColor="bg-blue-500/10 text-blue-400 border-blue-500/20"
              products={bigTech}
            />
            <ProductGrid
              title="Small & Independent"
              badge="Etsy · Indie shops"
              badgeColor="bg-green-500/10 text-green-400 border-green-500/20"
              products={smallBiz}
            />
          </div>
        )}
      </div>
    </div>
  );
}
