"use client";
import { useEffect, useState } from "react";

const STEPS = [
  "Parsing your intent with Nebius LLM...",
  "Planning search tasks...",
  "Launching Playwright scrapers in parallel...",
  "Reading accessibility trees...",
  "Extracting product data via LLM...",
  "Scoring on price, shipping, quality & ethics...",
  "Picking top results...",
];

export default function LoadingState() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setStep(s => (s + 1 < STEPS.length ? s + 1 : s));
    }, 2200);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="mt-12 flex flex-col items-center gap-4">
      {/* Spinner */}
      <div className="w-8 h-8 rounded-full border-2 border-white/10 border-t-white/60 animate-spin" />

      {/* Step label */}
      <p className="text-sm text-white/50 text-center transition-all">{STEPS[step]}</p>

      {/* Progress dots */}
      <div className="flex gap-1.5 mt-1">
        {STEPS.map((_, i) => (
          <div
            key={i}
            className={`h-1 rounded-full transition-all duration-500 ${
              i <= step ? "w-4 bg-white/50" : "w-1 bg-white/15"
            }`}
          />
        ))}
      </div>
    </div>
  );
}
