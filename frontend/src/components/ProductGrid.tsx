import { Product } from "@/app/page";
import ProductCard from "./ProductCard";

interface Props {
  title: string;
  accent: "blue" | "green";
  products: Product[];
  limit?: number;
}

const ACCENT = {
  blue:  { bar: "bg-black" },
  green: { bar: "bg-black" },
};

export default function ProductGrid({ title, accent, products, limit = 3 }: Props) {
  const a = ACCENT[accent];
  const visible = products.slice(0, limit === 4 ? undefined : limit);
  return (
    <div>
      {/* Header */}
      <div className="mb-4 border-b border-[#222] pb-2">
        <h2 className="text-xs font-black text-black tracking-[0.15em] uppercase">{title}</h2>
      </div>

      {visible.length === 0 ? (
        <div className="border-2 border-dashed border-[#ccc] p-8 text-center text-[#bbb] text-xs tracking-widest uppercase">
          No results
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {visible.map((p, i) => <ProductCard key={i} product={p} rank={i + 1} />)}
        </div>
      )}
    </div>
  );
}
