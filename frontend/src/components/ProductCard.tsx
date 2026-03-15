export default function ProductCard({ product }) {
  return (
    <div className="border p-3 mb-3 rounded">
      <h3 className="font-semibold">{product.name}</h3>

      <a href={product.url} target="_blank" className="text-blue-600 block">
        {product.url}
      </a>

      <p className="text-sm mt-2">{product.description}</p>

      <div className="flex gap-2 mt-3">
        {product.email && (
          <a href={`mailto:${product.email}`} className="bg-green-600 text-white px-3 py-1 rounded">
            Email
          </a>
        )}

        {product.phone && (
          <a href={`tel:${product.phone}`} className="bg-purple-600 text-white px-3 py-1 rounded">
            Call
          </a>
        )}
      </div>
    </div>
  );
}
