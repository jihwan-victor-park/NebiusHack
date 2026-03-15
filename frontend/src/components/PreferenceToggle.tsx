type PreferenceToggleProps = {
  preference: string;
  setPreference: (value: string) => void;
};

export default function PreferenceToggle({
  preference,
  setPreference,
}: PreferenceToggleProps) {
  return (
    <div>
      <p className="mb-3 text-sm font-medium text-slate-700">
        Company preference
      </p>

      <div className="flex w-full max-w-md overflow-hidden rounded-2xl border border-slate-200 bg-slate-100">
        <button
          onClick={() => setPreference("small")}
          className={`flex-1 px-4 py-3 text-sm font-semibold transition ${
            preference === "small"
              ? "bg-blue-600 text-white"
              : "bg-transparent text-slate-700 hover:bg-blue-50"
          }`}
        >
          Favor Small
        </button>

        <button
          onClick={() => setPreference("neutral")}
          className={`flex-1 px-4 py-3 text-sm font-semibold transition ${
            preference === "neutral"
              ? "bg-slate-700 text-white"
              : "bg-transparent text-slate-700 hover:bg-slate-200"
          }`}
        >
          Balanced
        </button>

        <button
          onClick={() => setPreference("large")}
          className={`flex-1 px-4 py-3 text-sm font-semibold transition ${
            preference === "large"
              ? "bg-red-600 text-white"
              : "bg-transparent text-slate-700 hover:bg-red-50"
          }`}
        >
          Favor Large
        </button>
      </div>
    </div>
  );
}