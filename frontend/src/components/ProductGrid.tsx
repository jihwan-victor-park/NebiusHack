import { Product } from "@/app/page";
import ProductCard from "./ProductCard";

interface Props {
  title: string;
  badge: string;
  badgeColor: string;
  products: Product[];
}

export default function ProductGrid({ title, badge, badgeColor, products }: Props) {
  return (
    <div>
      {/* Column header */}
      <div className="flex items-center gap-3 mb-4">
        <h2 className="font-semibold text-sm">{title}</h2>
        <span className={`text-xs border rounded-full px-2.5 py-0.5 ${badgeColor}`}>
          {badge}
        </span>
      </div>

      {products.length === 0 ? (
        <div className="border border-white/10 rounded-xl p-6 text-center text-white/30 text-sm">
          No results found
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {products.map((p, i) => (
            <ProductCard key={i} product={p} rank={i + 1} />
          ))}
        </div>
      )}
    </div>
  );
}
