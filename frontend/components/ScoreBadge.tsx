import { clsx } from "clsx";

interface ScoreBadgeProps {
  score: number;
  keywords?: string[];
}

export default function ScoreBadge({ score, keywords = [] }: ScoreBadgeProps) {
  const { bg, text, ring } =
    score >= 70
      ? { bg: "bg-emerald-950", text: "text-emerald-300", ring: "ring-emerald-700" }
      : score >= 40
      ? { bg: "bg-amber-950", text: "text-amber-300", ring: "ring-amber-700" }
      : { bg: "bg-rose-950", text: "text-rose-300", ring: "ring-rose-800" };

  return (
    <div className="group relative inline-flex">
      <span
        className={clsx(
          "inline-flex items-center justify-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1",
          bg,
          text,
          ring
        )}
      >
        {score}
      </span>

      {/* Tooltip — keyword list on hover */}
      {keywords.length > 0 && (
        <div
          className={clsx(
            "pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 w-48 -translate-x-1/2",
            "rounded-lg border border-slate-700 bg-slate-900 p-2.5 opacity-0 shadow-xl",
            "transition-opacity duration-150 group-hover:opacity-100"
          )}
        >
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-widest text-slate-400">
            Matched skills
          </p>
          <div className="flex flex-wrap gap-1">
            {keywords.map((kw) => (
              <span
                key={kw}
                className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-300"
              >
                {kw}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
