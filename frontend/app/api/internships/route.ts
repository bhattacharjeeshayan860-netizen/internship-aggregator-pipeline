/**
 * Next.js API Route — /api/internships
 * Server-side proxy to the Render FastAPI backend.
 * Reads API_URL from server env (no NEXT_PUBLIC_ needed — never exposed to browser).
 */
import { NextRequest, NextResponse } from "next/server";

const API_BASE = (process.env.API_URL ?? "http://localhost:10000").replace(/\/$/, "");

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);

  // Forward any query params (min_score, work_mode, source)
  const params = searchParams.toString();
  const backendUrl = `${API_BASE}/api/internships${params ? `?${params}` : ""}`;

  try {
    const res = await fetch(backendUrl, {
      // Revalidate every 60 min in Next.js cache
      next: { revalidate: 3600 },
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
    console.error("[proxy] /api/internships failed:", err);
    return NextResponse.json(
      { error: "Could not reach the internship backend." },
      { status: 503 }
    );
  }
}
