export default function ComparisonTable({ products }: { products: any[] }) {
  return (
    <table className="w-full text-sm mt-6 border rounded-xl overflow-hidden">
      <thead className="bg-gray-100">
        <tr>
          <th className="text-left p-3">Product</th>
          <th className="p-3">Source</th>
          <th className="p-3">Price</th>
          <th className="p-3">Ships in</th>
          <th className="p-3">Indie Score</th>
        </tr>
      </thead>
      <tbody>
        {products.map((p, i) => (
          <tr key={i} className="border-t hover:bg-gray-50">
            <td className="p-3">{p.name}</td>
            <td className="p-3 text-center">{p.source}</td>
            <td className="p-3 text-center">${p.price}</td>
            <td className="p-3 text-center">{p.shipping_days}d</td>
            <td className="p-3 text-center">{(p.small_biz_score * 100).toFixed(0)}%</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
