/**
 * Next.js API Route — POST /api/resume
 * Server-side proxy for the resume upload endpoint on the Render backend.
 *
 * The browser POSTs multipart/form-data here (same-origin).
 * This route forwards the file to the FastAPI backend using API_URL (server-only env var).
 * The resume bytes never touch the browser's network tab pointing to Render directly.
 */
import { NextRequest, NextResponse } from "next/server";

const API_BASE = (process.env.API_URL ?? "http://localhost:10000").replace(/\/$/, "");

// Allow up to 4 MB uploads (matches backend MAX_PDF_BYTES)
export const maxDuration = 30;

export async function POST(request: NextRequest) {
  let formData: FormData;
  try {
    formData = await request.formData();
  } catch {
    return NextResponse.json({ error: "Invalid form data." }, { status: 400 });
  }

  const file = formData.get("file");
  if (!file || !(file instanceof Blob)) {
    return NextResponse.json({ error: "No file provided." }, { status: 400 });
  }

  // Re-build a clean FormData to forward to the backend
  const backendForm = new FormData();
  backendForm.append("file", file, (file as File).name ?? "resume.pdf");

  try {
    const res = await fetch(`${API_BASE}/resume/upload`, {
      method: "POST",
      body: backendForm,
      // Do NOT set Content-Type — let fetch set the boundary automatically
    });

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err) {
    console.error("[resume proxy] upload failed:", err);
    return NextResponse.json(
      { error: "Could not reach the backend. Please try again." },
      { status: 503 }
    );
  }
}
