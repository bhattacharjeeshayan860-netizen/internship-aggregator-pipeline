/**
 * SWR data-fetching hook + typed interfaces for the FastAPI backend.
 */

import useSWR from "swr";

export interface JobListing {
  id: string;
  company: string;
  title: string;
  location: string;
  work_mode: "Remote" | "Hybrid" | "On-site";
  tech_score: number; // 0–100
  matched_keywords: string[];
  stipend_estimate: string;
  apply_url: string;
  source: "greenhouse" | "lever" | "ashby";
  posted_date: string | null;
}

export interface ScrapeResult {
  jobs: JobListing[];
  total: number;
  scraped_at: string;
  cache_hit: boolean;
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://localhost:10000";

const fetcher = (url: string) =>
  fetch(url).then((res) => {
    if (!res.ok) throw new Error(`API error ${res.status}`);
    return res.json() as Promise<ScrapeResult>;
  });

/**
 * Hook that polls /api/internships every 5 minutes.
 * Supports optional server-side filter params.
 */
export function useInternships(params?: {
  min_score?: number;
  work_mode?: string;
  source?: string;
}) {
  const query = new URLSearchParams();
  if (params?.min_score) query.set("min_score", String(params.min_score));
  if (params?.work_mode) query.set("work_mode", params.work_mode);
  if (params?.source) query.set("source", params.source);

  const url = `${API_BASE}/api/internships${query.size ? `?${query}` : ""}`;

  return useSWR<ScrapeResult>(url, fetcher, {
    refreshInterval: 5 * 60 * 1000, // 5 min
    revalidateOnFocus: false,
    dedupingInterval: 60_000,
  });
}

export async function triggerRefresh(): Promise<ScrapeResult> {
  const res = await fetch(`${API_BASE}/api/internships/refresh`);
  if (!res.ok) throw new Error(`Refresh failed: ${res.status}`);
  return res.json();
}
