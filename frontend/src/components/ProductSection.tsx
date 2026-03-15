import ProductCard from "./ProductCard";

export default function ProductSection({ title, products }) {
  return (
    <div className="border rounded p-4">
      <h2 className="text-xl font-semibold mb-4">{title}</h2>

      {products?.map((p, i) => (
        <ProductCard key={i} product={p} />
      ))}
    </div>
  );
}
