"use client";

import { useCallback, useRef, useState } from "react";
import { Upload, FileText, X, Loader2, ChevronRight } from "lucide-react";
import { clsx } from "clsx";
import type { CandidateProfile } from "@/lib/matcher";

interface ResumeUploadProps {
  onUpload: (profile: CandidateProfile) => void;
  onSkip: () => void;
}

type UploadState = "idle" | "uploading" | "error";

const STEPS = [
  "Reading resume…",
  "Extracting skills…",
  "Identifying target roles…",
  "Building your profile…",
];

export default function ResumeUpload({ onUpload, onSkip }: ResumeUploadProps) {
  const [state, setState] = useState<UploadState>("idle");
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [stepIdx, setStepIdx] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const processFile = useCallback(
    async (file: File) => {
      // Validate client-side before sending
      if (!file.name.toLowerCase().endsWith(".pdf") && file.type !== "application/pdf") {
        setErrorMsg("Please upload a PDF file.");
        setState("error");
        return;
      }
      if (file.size > 4 * 1024 * 1024) {
        setErrorMsg("File too large. Maximum size is 4 MB.");
        setState("error");
        return;
      }

      setState("uploading");
      setStepIdx(0);
      setErrorMsg("");

      // Animate steps while uploading
      const stepTimer = setInterval(() => {
        setStepIdx((i) => Math.min(i + 1, STEPS.length - 1));
      }, 700);

      const form = new FormData();
      form.append("file", file);

      try {
        const res = await fetch("/api/resume", { method: "POST", body: form });
        clearInterval(stepTimer);

        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body?.detail ?? `Upload failed (${res.status})`);
        }

        const profile: CandidateProfile = await res.json();
        onUpload(profile);
      } catch (err) {
        clearInterval(stepTimer);
        setErrorMsg(err instanceof Error ? err.message : "Upload failed. Please try again.");
        setState("error");
      }
    },
    [onUpload]
  );

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
    e.target.value = "";
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  };

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900 p-6">
      <div className="mb-4">
        <h2 className="text-base font-semibold text-slate-100">
          Find internships that match <span className="text-blue-400">you</span>
        </h2>
        <p className="mt-0.5 text-sm text-slate-500">
          Upload your resume and we&apos;ll score every listing against your skills and target roles.
        </p>
      </div>

      {/* Drop zone */}
      <div
        role="button"
        tabIndex={0}
        onClick={() => state !== "uploading" && inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={clsx(
          "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed py-8 transition-colors",
          state === "uploading" && "cursor-default",
          dragOver
            ? "border-blue-500 bg-blue-950/30"
            : state === "error"
            ? "border-rose-700 bg-rose-950/20"
            : "border-slate-700 hover:border-slate-500 hover:bg-slate-800/50"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="hidden"
          onChange={handleFileInput}
          disabled={state === "uploading"}
        />

        {state === "uploading" ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-blue-400" />
            <div className="space-y-1 text-center">
              {STEPS.map((step, i) => (
                <p
                  key={step}
                  className={clsx(
                    "text-sm transition-colors",
                    i < stepIdx
                      ? "text-emerald-400"
                      : i === stepIdx
                      ? "text-slate-200"
                      : "text-slate-600"
                  )}
                >
                  {i < stepIdx ? "✓ " : i === stepIdx ? "○ " : "  "}
                  {step}
                </p>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 text-center">
            {state === "error" ? (
              <X className="h-8 w-8 text-rose-400" />
            ) : (
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-950">
                <Upload className="h-5 w-5 text-blue-400" />
              </div>
            )}
            <div>
              <p className="text-sm font-medium text-slate-200">
                {state === "error" ? "Try another file" : "Drop your resume here"}
              </p>
              <p className="text-xs text-slate-500">PDF · max 4 MB</p>
            </div>
            {state === "error" && (
              <p className="mt-1 rounded-lg bg-rose-950/50 px-3 py-1.5 text-xs text-rose-300">
                {errorMsg}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-slate-600">
          <FileText className="h-3.5 w-3.5" />
          Resume is processed in memory and never stored.
        </div>
        <button
          onClick={onSkip}
          disabled={state === "uploading"}
          className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-300 disabled:opacity-40"
        >
          Continue without resume <ChevronRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
