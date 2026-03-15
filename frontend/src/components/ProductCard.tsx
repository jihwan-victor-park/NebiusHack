import { Product } from "@/app/page";

const SOURCE_LABEL: Record<string, string> = {
  amazon: "Amazon", walmart: "Walmart",
  etsy: "Etsy", indie: "Independent", shopify: "Shopify",
  nordstrom: "Nordstrom",
};

const RANK_BADGE = [
  { bg: "bg-black",      text: "text-white",      label: "1st" },
  { bg: "bg-[#444]",     text: "text-white",      label: "2nd" },
  { bg: "bg-[#888]",     text: "text-white",      label: "3rd" },
];

function ReviewCount({ count }: { count: number }) {
  return (
    <span className="text-[#999]">
      ({count >= 1000 ? `${(count / 1000).toFixed(1)}k` : count})
    </span>
  );
}

export default function ProductCard({ product: p, rank }: { product: Product; rank: number }) {
  const badge = RANK_BADGE[rank - 1];

  return (
    <div className="group bg-white border border-[#222] rounded-none overflow-hidden w-full
                    hover:shadow-[3px_3px_0px_0px_#222] transition-shadow duration-150">

      {/* Image */}
      <div className="relative w-full h-36 bg-[#f5f5f5] border-b border-[#222] overflow-hidden">
        {p.image_url ? (
          <img
            src={p.image_url}
            alt={p.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            onError={e => {
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <span className="text-[#ccc] text-xs tracking-widest uppercase">No image</span>
          </div>
        )}

        {/* Rank badge — top-left corner */}
        {badge && (
          <div className={`absolute top-2 left-2 ${badge.bg} ${badge.text}
                          text-[10px] font-bold tracking-widest uppercase
                          px-2 py-0.5`}>
            {badge.label}
          </div>
        )}

        {/* Source tag — top-right */}
        <div className="absolute top-2 right-2 bg-white border border-black
                        text-[9px] font-semibold tracking-widest uppercase px-2 py-0.5">
          {SOURCE_LABEL[p.source] ?? p.source}
        </div>
      </div>

      {/* Content */}
      <div className="p-3 space-y-2.5">

        {/* Name + price row */}
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            {p.url ? (
              <a
                href={p.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[13px] font-semibold text-black leading-snug line-clamp-2
                           hover:underline underline-offset-2 block"
              >
                {p.name || "—"}
              </a>
            ) : (
              <p className="text-[13px] font-semibold text-black leading-snug line-clamp-2">
                {p.name || "—"}
              </p>
            )}
          </div>

          {p.price != null && p.price > 0 && (
            <span className="text-base font-black text-black shrink-0 tabular-nums">
              ${p.price.toFixed(2)}
            </span>
          )}
        </div>

        {/* Stats row */}
        <div className="flex items-center gap-0 border-t border-[#e5e5e5] pt-2.5">

          {/* Rating */}
          <div className="flex-1 flex flex-col items-center gap-0.5
                          border-r border-[#ddd] last:border-r-0 px-1">
            <span className="text-[9px] font-bold uppercase tracking-widest text-[#555]">Rating</span>
            {p.rating != null ? (
              <span className="text-xs font-bold text-black tabular-nums">
                ★ {p.rating.toFixed(1)}
                {p.review_count != null && <ReviewCount count={p.review_count} />}
              </span>
            ) : (
              <span className="text-xs text-[#bbb] font-medium">—</span>
            )}
          </div>

          {/* Shipping */}
          <div className="flex-1 flex flex-col items-center gap-0.5
                          border-r border-[#ddd] last:border-r-0 px-1">
            <span className="text-[9px] font-bold uppercase tracking-widest text-[#555]">Ships in</span>
            {p.shipping_days != null ? (
              <span className="text-xs font-bold text-black tabular-nums">
                {p.shipping_days === 0 ? "Today"
                 : p.shipping_days === 1 ? "1 day"
                 : `${p.shipping_days} days`}
              </span>
            ) : (
              <span className="text-xs text-[#bbb] font-medium">—</span>
            )}
          </div>

          {/* Price (if missing from header, shown here) */}
          {(p.price == null || p.price === 0) && (
            <div className="flex-1 flex flex-col items-center gap-0.5 px-1">
              <span className="text-[9px] font-bold uppercase tracking-widest text-[#555]">Price</span>
              <span className="text-xs text-[#bbb] font-medium">—</span>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
