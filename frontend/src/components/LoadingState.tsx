"use client";
import { useEffect, useState } from "react";

const STEPS = [
  "Parsing your intent…",
  "Searching Amazon…",
  "Searching Etsy…",
  "Finding indie shops…",
  "Extracting product data…",
  "Scoring results…",
  "Ranking picks…",
];

export default function LoadingState() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setStep(s => (s + 1 < STEPS.length ? s + 1 : s));
    }, 2000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="flex flex-col items-center gap-5 pt-20">
      {/* Thin progress bar */}
      <div className="w-48 h-0.5 bg-[#e8e6e3] rounded-full overflow-hidden">
        <div
          className="h-full bg-[#111] rounded-full transition-all duration-700 ease-out"
          style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
        />
      </div>

      {/* Step label */}
      <p className="text-xs text-[#aaa] tracking-wide">{STEPS[step]}</p>

      {/* Step dots */}
      <div className="flex gap-1">
        {STEPS.map((_, i) => (
          <div key={i} className={`rounded-full transition-all duration-500 ${
            i < step  ? "w-1.5 h-1.5 bg-[#ccc]" :
            i === step ? "w-3 h-1.5 bg-[#888]" :
                        "w-1.5 h-1.5 bg-[#e0dedd]"
          }`} />
        ))}
      </div>
    </div>
  );
}
