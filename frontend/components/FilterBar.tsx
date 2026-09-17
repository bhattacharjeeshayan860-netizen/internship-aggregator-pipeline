"use client";

import { clsx } from "clsx";
import { Search, SlidersHorizontal, X } from "lucide-react";

export interface FilterState {
  search: string;
  workMode: string;
  source: string;
  minScore: number;
  location: string;
}

interface FilterBarProps {
  filters: FilterState;
  onChange: (next: Partial<FilterState>) => void;
  resultCount: number;
  totalCount: number;
}

const WORK_MODES = ["All", "Remote", "Hybrid", "On-site"];
const SOURCES = ["All", "greenhouse", "lever", "ashby"];
const SCORE_THRESHOLDS = [0, 20, 40, 60, 80];
const LOCATIONS = [
  "All",
  "Remote",
  "Singapore",
  "India",
  "United States",
  "United Kingdom",
  "Canada",
  "Europe",
];

export default function FilterBar({
  filters,
  onChange,
  resultCount,
  totalCount,
}: FilterBarProps) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-slate-800 bg-slate-900 p-4">
      {/* Row 1: search + result count */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search company, title, or location…"
            value={filters.search}
            onChange={(e) => onChange({ search: e.target.value })}
            className={clsx(
              "w-full rounded-lg border border-slate-700 bg-slate-800 py-2 pl-9 pr-10",
              "text-sm text-slate-200 placeholder:text-slate-500",
              "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            )}
          />
          {filters.search && (
            <button
              onClick={() => onChange({ search: "" })}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        <span className="whitespace-nowrap text-sm text-slate-400">
          <span className="font-semibold text-slate-200">{resultCount}</span>
          {" / "}
          <span className="text-slate-500">{totalCount}</span>{" "}
          <span>jobs</span>
        </span>
      </div>

      {/* Row 2: dropdown filters */}
      <div className="flex flex-wrap items-center gap-3">
        <SlidersHorizontal className="h-4 w-4 shrink-0 text-slate-500" />

        {/* Work mode */}
        <select
          value={filters.workMode}
          onChange={(e) => onChange({ workMode: e.target.value })}
          className={clsx(
            "rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-slate-200",
            "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          )}
        >
          {WORK_MODES.map((m) => (
            <option key={m} value={m}>
              {m === "All" ? "All modes" : m}
            </option>
          ))}
        </select>

        {/* ATS source */}
        <select
          value={filters.source}
          onChange={(e) => onChange({ source: e.target.value })}
          className={clsx(
            "rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-slate-200",
            "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          )}
        >
          {SOURCES.map((s) => (
            <option key={s} value={s}>
              {s === "All" ? "All sources" : s.charAt(0).toUpperCase() + s.slice(1)}
            </option>
          ))}
        </select>

        {/* Min score */}
        <select
          value={filters.minScore}
          onChange={(e) => onChange({ minScore: Number(e.target.value) })}
          className={clsx(
            "rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-slate-200",
            "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          )}
        >
          {SCORE_THRESHOLDS.map((s) => (
            <option key={s} value={s}>
              {s === 0 ? "Any score" : `Score ≥ ${s}`}
            </option>
          ))}
        </select>

        {/* Location */}
        <select
          value={filters.location}
          onChange={(e) => onChange({ location: e.target.value })}
          className={clsx(
            "rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-slate-200",
            "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          )}
        >
          {LOCATIONS.map((l) => (
            <option key={l} value={l}>
              {l === "All" ? "All locations" : l}
            </option>
          ))}
        </select>

        {/* Active filter chips */}
        {(filters.workMode !== "All" ||
          filters.source !== "All" ||
          filters.minScore > 0 ||
          filters.location !== "All" ||
          filters.search) && (
          <button
            onClick={() =>
              onChange({ search: "", workMode: "All", source: "All", minScore: 0, location: "All" })
            }
            className="ml-auto flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-400 hover:border-slate-500 hover:text-slate-200"
          >
            <X className="h-3 w-3" />
            Clear filters
          </button>
        )}
      </div>
    </div>
  );
}
