"use client";
import { useState } from "react";

export default function SearchBar({ onSearch }: { onSearch: (q: string) => void }) {
  const [query, setQuery] = useState("");
  return (
    <div className="flex gap-2">
      <input
        className="flex-1 border rounded-lg px-4 py-2 text-sm"
        placeholder='e.g. "handmade ceramic mug under $40, ships in a week"'
        value={query}
        onChange={e => setQuery(e.target.value)}
        onKeyDown={e => e.key === "Enter" && onSearch(query)}
      />
      <button
        className="bg-blue-600 text-white px-6 py-2 rounded-lg text-sm hover:bg-blue-700"
        onClick={() => onSearch(query)}
      >
        Search
      </button>
    </div>
  );
}
