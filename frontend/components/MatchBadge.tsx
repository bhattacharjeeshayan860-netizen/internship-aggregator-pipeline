import { clsx } from "clsx";
import type { MatchScore } from "@/lib/matcher";

interface MatchBadgeProps {
  score: MatchScore;
}

export default function MatchBadge({ score }: MatchBadgeProps) {
  const { bg, text, ring } =
    score.overall >= 70
      ? { bg: "bg-emerald-950", text: "text-emerald-300", ring: "ring-emerald-700" }
      : score.overall >= 40
      ? { bg: "bg-amber-950", text: "text-amber-300", ring: "ring-amber-700" }
      : { bg: "bg-rose-950", text: "text-rose-300", ring: "ring-rose-800" };

  return (
    <div className="group relative inline-flex">
      <span
        className={clsx(
          "inline-flex items-center justify-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1",
          bg, text, ring
        )}
      >
        {score.overall}%
      </span>

      {/* Breakdown tooltip on hover */}
      <div
        className={clsx(
          "pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 w-52 -translate-x-1/2",
          "rounded-lg border border-slate-700 bg-slate-900 p-3 opacity-0 shadow-xl",
          "transition-opacity duration-150 group-hover:opacity-100"
        )}
      >
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-slate-400">
          Match breakdown
        </p>
        <div className="space-y-1.5">
          <ScoreRow label="Skills" value={score.skill_match} weight="40%" />
          <ScoreRow label="Role" value={score.role_match} weight="30%" />
          <ScoreRow label="Work mode" value={score.work_mode_match} weight="20%" />
        </div>

        {score.matched_skills.length > 0 && (
          <>
            <p className="mb-1 mt-2.5 text-[10px] font-semibold uppercase tracking-widest text-slate-400">
              Your skills found
            </p>
            <div className="flex flex-wrap gap-1">
              {score.matched_skills.map((s) => (
                <span
                  key={s}
                  className="rounded bg-emerald-950 px-1.5 py-0.5 text-[10px] text-emerald-300"
                >
                  {s}
                </span>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function ScoreRow({ label, value, weight }: { label: string; value: number; weight: string }) {
  const color =
    value >= 70 ? "bg-emerald-500" : value >= 40 ? "bg-amber-500" : "bg-rose-500";
  return (
    <div className="flex items-center gap-2">
      <span className="w-16 shrink-0 text-[10px] text-slate-400">{label}</span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-800">
        <div className={clsx("h-full rounded-full", color)} style={{ width: `${value}%` }} />
      </div>
      <span className="w-6 text-right text-[10px] text-slate-400">{value}</span>
      <span className="text-[9px] text-slate-600">{weight}</span>
    </div>
  );
}
