import { Product } from "@/app/page";

const SOURCE_LABELS: Record<string, string> = {
  amazon: "Amazon",
  walmart: "Walmart",
  etsy: "Etsy",
  indie: "Indie shop",
  shopify: "Shopify",
};

const RANK_COLORS = ["text-yellow-400", "text-white/50", "text-orange-700"];

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-white/35 w-16 shrink-0 text-right text-xs">{label}</span>
      <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${value * 100}%` }} />
      </div>
      <span className="text-white/40 w-7 text-right text-xs">{(value * 100).toFixed(0)}</span>
    </div>
  );
}

export default function ProductCard({ product: p, rank }: { product: Product; rank: number }) {
  const rankColor = RANK_COLORS[rank - 1] ?? "text-white/30";

  return (
    <div className="border border-white/10 rounded-xl overflow-hidden bg-white/3 hover:bg-white/5 transition-all">
      {/* Product image */}
      {p.image_url && (
        <div className="w-full h-40 bg-white/5 overflow-hidden">
          <img
            src={p.image_url}
            alt={p.name}
            className="w-full h-full object-contain p-2"
            onError={e => { (e.target as HTMLImageElement).style.display = "none"; }}
          />
        </div>
      )}

      <div className="p-4">
        {/* Top row: rank + name + price */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-2.5 min-w-0">
            <span className={`font-bold text-sm mt-0.5 shrink-0 ${rankColor}`}>#{rank}</span>
            <div className="min-w-0">
              <p className="font-medium text-sm leading-snug line-clamp-2">
                {p.url ? (
                  <a href={p.url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                    {p.name || "Unknown product"}
                  </a>
                ) : (
                  p.name || "Unknown product"
                )}
              </p>
              <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 mt-1">
                <span className="text-xs text-white/35">{SOURCE_LABELS[p.source] ?? p.source}</span>
                {p.rating != null && (
                  <span className="text-xs text-yellow-400/80">
                    ★ {p.rating.toFixed(1)}
                    {p.review_count != null && (
                      <span className="text-white/30"> ({p.review_count.toLocaleString()})</span>
                    )}
                  </span>
                )}
                {p.shipping_days != null && (
                  <span className="text-xs text-white/30">· {p.shipping_days}d shipping</span>
                )}
              </div>
            </div>
          </div>

          {/* Price + score */}
          <div className="text-right shrink-0">
            <p className="font-bold text-base">{p.price > 0 ? `$${p.price.toFixed(2)}` : "—"}</p>
            <p className="text-xs text-white/35 mt-0.5">score {(p.final_score * 100).toFixed(0)}</p>
          </div>
        </div>

        {/* Score bars */}
        <div className="mt-3 space-y-1.5">
          <ScoreBar label="Price"    value={p.price_score}    color="bg-blue-400" />
          <ScoreBar label="Shipping" value={p.shipping_score} color="bg-purple-400" />
          <ScoreBar label="Quality"  value={p.quality_score}  color="bg-yellow-400" />
          <ScoreBar label="Ethics"   value={p.ethics_score}   color="bg-green-400" />
        </div>

        {/* Reasoning */}
        {p.reasoning && (
          <p className="mt-3 text-xs text-white/35 italic leading-relaxed border-t border-white/5 pt-3">
            {p.reasoning}
          </p>
        )}
      </div>
    </div>
  );
}
