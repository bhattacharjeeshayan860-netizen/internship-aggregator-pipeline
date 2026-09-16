/**
 * Next.js API Route — /api/internships/refresh
 * Proxies the forced re-scrape endpoint on the Render backend.
 */
import { NextResponse } from "next/server";

const API_BASE = (process.env.API_URL ?? "http://localhost:10000").replace(/\/$/, "");

export async function GET() {
  try {
    const res = await fetch(`${API_BASE}/api/internships/refresh`, {
      // Never cache the refresh endpoint
      cache: "no-store",
    });

    if (!res.ok) {
      return NextResponse.json(
        { error: `Backend error: ${res.status}` },
        { status: res.status }
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    console.error("[proxy] /api/internships/refresh failed:", err);
    return NextResponse.json(
      { error: "Refresh failed — backend unreachable." },
      { status: 503 }
    );
  }
}
