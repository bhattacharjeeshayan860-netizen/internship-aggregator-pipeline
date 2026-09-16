"use client";

import { useState, useMemo, useCallback } from "react";
import { RefreshCw, Radar, AlertCircle, Wifi, WifiOff } from "lucide-react";
import { clsx } from "clsx";
import { useInternships, triggerRefresh } from "@/lib/api";
import type { JobListing } from "@/lib/api";
import JobTable from "@/components/JobTable";
import FilterBar, { type FilterState } from "@/components/FilterBar";

// ── Loading skeleton ──────────────────────────────────────────────────────────
function Skeleton() {
  return (
    <div className="space-y-2 rounded-xl border border-slate-800 overflow-hidden">
      {Array.from({ length: 8 }).map((_, i) => (
        <div
          key={i}
          className="h-12 animate-pulse bg-slate-800/60"
          style={{ opacity: 1 - i * 0.08 }}
        />
      ))}
    </div>
  );
}

// ── Source pill stats ─────────────────────────────────────────────────────────
function SourceStat({ label, count, color }: { label: string; count: number; color: string }) {
  return (
    <div className={clsx("flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium", color)}>
      <span className="font-semibold">{count}</span>
      <span className="opacity-70">{label}</span>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function Home() {
  const { data, error, isLoading, isValidating, mutate } = useInternships();
  const [refreshing, setRefreshing] = useState(false);

  const [filters, setFilters] = useState<FilterState>({
    search: "",
    workMode: "All",
    source: "All",
    minScore: 0,
  });

  const handleFilterChange = useCallback((next: Partial<FilterState>) => {
    setFilters((prev) => ({ ...prev, ...next }));
  }, []);

  // Client-side filter application
  const filteredJobs = useMemo((): JobListing[] => {
    if (!data?.jobs) return [];
    let jobs = data.jobs;

    if (filters.search) {
      const q = filters.search.toLowerCase();
      jobs = jobs.filter(
        (j) =>
          j.company.toLowerCase().includes(q) ||
          j.title.toLowerCase().includes(q) ||
          j.location.toLowerCase().includes(q)
      );
    }
    if (filters.workMode !== "All") {
      jobs = jobs.filter((j) => j.work_mode === filters.workMode);
    }
    if (filters.source !== "All") {
      jobs = jobs.filter((j) => j.source === filters.source);
    }
    if (filters.minScore > 0) {
      jobs = jobs.filter((j) => j.tech_score >= filters.minScore);
    }

    return jobs;
  }, [data, filters]);

  // Stats by source
  const sourceCounts = useMemo(() => {
    const jobs = data?.jobs ?? [];
    return {
      greenhouse: jobs.filter((j) => j.source === "greenhouse").length,
      lever: jobs.filter((j) => j.source === "lever").length,
      ashby: jobs.filter((j) => j.source === "ashby").length,
    };
  }, [data]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await triggerRefresh();
      await mutate();
    } catch (err) {
      console.error("Refresh failed:", err);
    } finally {
      setRefreshing(false);
    }
  };

  const scrapedAt = data?.scraped_at
    ? new Date(data.scraped_at).toLocaleTimeString()
    : null;

  return (
    <main className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      {/* ── Header ── */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <Radar className="h-7 w-7 text-blue-400" />
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">
              Internship Radar
            </h1>
            {isValidating && !isLoading && (
              <span className="rounded-full bg-blue-950 px-2 py-0.5 text-xs text-blue-300 ring-1 ring-blue-800">
                updating…
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Paid DS / ML / SWE internships · Greenhouse · Lever · Ashby
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Cache + connection status */}
          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            {error ? (
              <WifiOff className="h-3.5 w-3.5 text-rose-400" />
            ) : (
              <Wifi className="h-3.5 w-3.5 text-emerald-400" />
            )}
            {scrapedAt && <span>Updated {scrapedAt}</span>}
            {data?.cache_hit && (
              <span className="rounded-full bg-slate-800 px-1.5 py-0.5 text-slate-400">
                cached
              </span>
            )}
          </div>

          {/* Refresh button */}
          <button
            onClick={handleRefresh}
            disabled={refreshing || isLoading}
            className={clsx(
              "flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2",
              "text-sm font-medium text-slate-300",
              "hover:border-slate-600 hover:bg-slate-700 hover:text-slate-100",
              "disabled:cursor-not-allowed disabled:opacity-40",
              "transition-colors"
            )}
          >
            <RefreshCw
              className={clsx("h-4 w-4", (refreshing || isValidating) && "animate-spin")}
            />
            Refresh
          </button>
        </div>
      </div>

      {/* ── Source stats bar ── */}
      {data && (
        <div className="flex flex-wrap gap-2">
          <SourceStat
            label="Greenhouse"
            count={sourceCounts.greenhouse}
            color="bg-green-950 text-green-300"
          />
          <SourceStat
            label="Lever"
            count={sourceCounts.lever}
            color="bg-purple-950 text-purple-300"
          />
          <SourceStat
            label="Ashby"
            count={sourceCounts.ashby}
            color="bg-sky-950 text-sky-300"
          />
          <div className="ml-auto flex items-center gap-1.5 text-sm text-slate-500">
            <span className="font-semibold text-slate-300">{data.total}</span>
            internships total
          </div>
        </div>
      )}

      {/* ── Error state ── */}
      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-rose-900 bg-rose-950/50 px-4 py-3 text-sm text-rose-300">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>
            Could not reach the API. Make sure your backend is running and the{" "}
            <code className="rounded bg-rose-900/50 px-1 font-mono text-xs">
              API_URL
            </code>{" "}
            environment variable is set in Vercel.
          </span>
        </div>
      )}

      {/* ── Filter bar ── */}
      <FilterBar
        filters={filters}
        onChange={handleFilterChange}
        resultCount={filteredJobs.length}
        totalCount={data?.jobs.length ?? 0}
      />

      {/* ── Content ── */}
      {isLoading ? (
        <Skeleton />
      ) : data ? (
        <JobTable data={filteredJobs} globalFilter={filters.search} />
      ) : null}

      {/* ── Footer ── */}
      <p className="text-center text-xs text-slate-600">
        Data refreshes every 5 minutes · Powered by Greenhouse, Lever, and Ashby public APIs
      </p>
    </main>
  );
}
