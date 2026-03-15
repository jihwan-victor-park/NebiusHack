export default function ProductCard({ product }: { product: any }) {
  return (
    <div className="border rounded-xl p-4 bg-white shadow-sm">
      <div className="flex justify-between items-start">
        <div>
          <p className="font-semibold">{product.name}</p>
          <p className="text-xs text-gray-500 mt-1">{product.source} · ships in {product.shipping_days}d</p>
          <p className="text-xs text-gray-400 mt-2 italic">{product.reasoning}</p>
        </div>
        <div className="text-right shrink-0 ml-4">
          <p className="text-lg font-bold">${product.price}</p>
          <p className="text-xs text-green-600">indie score: {(product.small_biz_score * 100).toFixed(0)}%</p>
        </div>
      </div>
    </div>
  );
}
