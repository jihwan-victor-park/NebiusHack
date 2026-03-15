"use client";

import { useState } from "react";
import FeedbackPanel from "../components/FeedbackPanel";
import PreferenceToggle from "../components/PreferenceToggle";
import ProductSection from "../components/ProductSection";
import SearchBar from "../components/SearchBar";

export default function Home() {
  const [feedback, setFeedback] = useState(
    "Try a more specific query like 'handmade ceramic mug' or 'small business coffee beans'."
  );
  const [largeCompanies, setLargeCompanies] = useState([]);
  const [smallCompanies, setSmallCompanies] = useState([]);
  const [preference, setPreference] = useState("neutral");

  async function handleSearch(query: string) {
    try {
      const res = await fetch("http://localhost:8000/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          preference,
        }),
      });

      const data = await res.json();

      setFeedback(data.feedback || "");
      setLargeCompanies(data.largeCompanies || []);
      setSmallCompanies(data.smallCompanies || []);
    } catch (error) {
      console.error(error);
      setFeedback("Could not connect to backend.");
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 px-6 py-10">
      <div className="mx-auto max-w-7xl">
        <div className="mb-10">
          <h1 className="text-5xl font-extrabold tracking-tight text-slate-900">
            ShopAgent
          </h1>
          <p className="mt-3 max-w-2xl text-lg text-slate-600">
            Compare recommendations from large companies and small businesses,
            with AI feedback to refine vague prompts.
          </p>
        </div>

        <div className="rounded-2xl bg-white p-6 shadow-lg ring-1 ring-slate-200">
          <SearchBar onSearch={handleSearch} />

          <div className="mt-5">
            <PreferenceToggle
              preference={preference}
              setPreference={setPreference}
            />
          </div>
        </div>

        <FeedbackPanel feedback={feedback} />

        <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <ProductSection title="Large Companies" products={largeCompanies} />
          <ProductSection title="Small Companies" products={smallCompanies} />
        </div>
      </div>
    </main>
  );
}