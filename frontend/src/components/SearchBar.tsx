"use client";

import { useState } from "react";

export default function SearchBar({ onSearch }) {
  const [query, setQuery] = useState("");

  return (
    <div className="flex gap-3">
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="e.g. handmade ceramic mug"
        className="border px-4 py-2 rounded"
      />
      <button
        onClick={() => onSearch(query)}
        className="bg-blue-600 text-white px-4 py-2 rounded"
      >
        Search
      </button>
    </div>
  );
}
