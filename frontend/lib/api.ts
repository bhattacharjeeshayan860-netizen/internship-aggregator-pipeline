/**
 * SWR data-fetching hook + typed interfaces.
 *
 * All requests go to the local Next.js API routes (/api/internships, /api/internships/refresh),
 * which proxy to the Render backend server-side. This means:
 *  - No NEXT_PUBLIC_ env var needed — API_URL stays server-only
 *  - The Render URL is never shipped to the browser bundle
 *  - CORS is a non-issue (same-origin requests from client to Next.js)
 */

import useSWR from "swr";
import type { CandidateProfile } from "@/lib/matcher";

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

const fetcher = (url: string) =>
  fetch(url).then((res) => {
    if (!res.ok) throw new Error(`API error ${res.status}`);
    return res.json() as Promise<ScrapeResult>;
  });

/**
 * Hook that polls /api/internships (local Next.js proxy) every 5 minutes.
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

  // Calls the local Next.js API route — no hardcoded Render URL in client code
  const url = `/api/internships${query.size ? `?${query}` : ""}`;

  return useSWR<ScrapeResult>(url, fetcher, {
    refreshInterval: 5 * 60 * 1000, // 5 min
    revalidateOnFocus: false,
    dedupingInterval: 60_000,
  });
}

export async function triggerRefresh(): Promise<ScrapeResult> {
  const res = await fetch("/api/internships/refresh");
  if (!res.ok) throw new Error(`Refresh failed: ${res.status}`);
  return res.json();
}

/**
 * Upload a PDF resume and return the structured CandidateProfile.
 * Throws on network error or non-2xx response.
 */
export async function uploadResume(file: File): Promise<CandidateProfile> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch("/api/resume", { method: "POST", body: form });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail ?? `Upload failed (${res.status})`);
  }
  return res.json();
}

