"use client";
import { useState } from "react";
import SearchBar from "@/components/SearchBar";
import ProductCard from "@/components/ProductCard";
import ComparisonTable from "@/components/ComparisonTable";

export default function Home() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  async function handleSearch(query: string) {
    setLoading(true);
    const res = await fetch("http://localhost:8000/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    const data = await res.json();
    setResults(data.results);
    setLoading(false);
  }

  return (
    <main className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-6">ShopAgent</h1>
      <SearchBar onSearch={handleSearch} />
      {loading && <p className="mt-4 text-gray-500">Searching...</p>}
      {results.length > 0 && (
        <>
          <ComparisonTable products={results} />
          <div className="grid grid-cols-1 gap-4 mt-6">
            {results.map((p: any, i) => <ProductCard key={i} product={p} />)}
          </div>
        </>
      )}
    </main>
  );
}
