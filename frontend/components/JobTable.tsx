"use client";

import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  createColumnHelper,
  type SortingState,
  type ColumnFiltersState,
} from "@tanstack/react-table";
import { useState, useMemo } from "react";
import { ExternalLink, ChevronUp, ChevronDown, ChevronsUpDown } from "lucide-react";
import { clsx } from "clsx";
import type { JobListing } from "@/lib/api";
import ScoreBadge from "./ScoreBadge";

interface JobTableProps {
  data: JobListing[];
  globalFilter: string;
}

const columnHelper = createColumnHelper<JobListing>();

const SOURCE_COLORS: Record<string, string> = {
  greenhouse: "bg-green-950 text-green-300 ring-green-800",
  lever:      "bg-purple-950 text-purple-300 ring-purple-800",
  ashby:      "bg-sky-950 text-sky-300 ring-sky-800",
};

const WORK_MODE_COLORS: Record<string, string> = {
  Remote:   "bg-blue-950 text-blue-300",
  Hybrid:   "bg-violet-950 text-violet-300",
  "On-site": "bg-slate-800 text-slate-300",
};

function SortIcon({ isSorted }: { isSorted: false | "asc" | "desc" }) {
  if (isSorted === "asc") return <ChevronUp className="ml-1 inline h-3.5 w-3.5" />;
  if (isSorted === "desc") return <ChevronDown className="ml-1 inline h-3.5 w-3.5" />;
  return <ChevronsUpDown className="ml-1 inline h-3.5 w-3.5 opacity-30" />;
}

export default function JobTable({ data, globalFilter }: JobTableProps) {
  const [sorting, setSorting] = useState<SortingState>([
    { id: "tech_score", desc: true },
  ]);
  const [columnFilters] = useState<ColumnFiltersState>([]);

  const columns = useMemo(
    () => [
      columnHelper.accessor("company", {
        header: "Company",
        cell: (info) => (
          <span className="font-medium text-slate-200">{info.getValue()}</span>
        ),
      }),

      columnHelper.accessor("title", {
        header: "Role",
        cell: (info) => (
          <span className="text-slate-300">{info.getValue()}</span>
        ),
      }),

      columnHelper.accessor("tech_score", {
        header: "Score",
        cell: (info) => (
          <ScoreBadge
            score={info.getValue()}
            keywords={info.row.original.matched_keywords}
          />
        ),
      }),

      columnHelper.accessor("stipend_estimate", {
        header: "Stipend",
        cell: (info) => (
          <span className="font-mono text-xs text-slate-400">
            {info.getValue()}
          </span>
        ),
      }),

      columnHelper.accessor("location", {
        header: "Location",
        cell: (info) => (
          <span className="text-sm text-slate-400">{info.getValue() || "—"}</span>
        ),
      }),

      columnHelper.accessor("work_mode", {
        header: "Mode",
        cell: (info) => {
          const mode = info.getValue();
          return (
            <span
              className={clsx(
                "rounded-full px-2 py-0.5 text-xs font-medium",
                WORK_MODE_COLORS[mode] ?? "bg-slate-800 text-slate-300"
              )}
            >
              {mode}
            </span>
          );
        },
      }),

      columnHelper.accessor("source", {
        header: "ATS",
        cell: (info) => {
          const src = info.getValue();
          return (
            <span
              className={clsx(
                "rounded-full px-2 py-0.5 text-xs font-medium ring-1",
                SOURCE_COLORS[src] ?? "bg-slate-800 text-slate-300 ring-slate-700"
              )}
            >
              {src}
            </span>
          );
        },
      }),

      columnHelper.accessor("apply_url", {
        header: "Apply",
        enableSorting: false,
        cell: (info) => (
          <a
            href={info.getValue()}
            target="_blank"
            rel="noopener noreferrer"
            className={clsx(
              "inline-flex items-center gap-1 rounded-lg border border-blue-700 px-3 py-1",
              "text-xs font-medium text-blue-400",
              "hover:border-blue-500 hover:bg-blue-950 hover:text-blue-200 transition-colors"
            )}
          >
            Apply <ExternalLink className="h-3 w-3" />
          </a>
        ),
      }),
    ],
    []
  );

  const table = useReactTable({
    data,
    columns,
    state: { sorting, columnFilters, globalFilter },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    globalFilterFn: "includesString",
  });

  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-slate-800 bg-slate-900 py-20 text-slate-500">
        <span className="text-4xl">🔍</span>
        <p className="mt-3 text-sm">No internships match your current filters.</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-900">
              {table.getHeaderGroups().flatMap((hg) =>
                hg.headers.map((header) => (
                  <th
                    key={header.id}
                    className={clsx(
                      "px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500",
                      header.column.getCanSort() && "cursor-pointer select-none hover:text-slate-300"
                    )}
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {header.column.getCanSort() && (
                      <SortIcon isSorted={header.column.getIsSorted()} />
                    )}
                  </th>
                ))
              )}
            </tr>
          </thead>

          <tbody>
            {table.getRowModel().rows.map((row, i) => (
              <tr
                key={row.id}
                className={clsx(
                  "job-row border-b border-slate-800/50 last:border-0",
                  i % 2 === 0 ? "bg-slate-950" : "bg-slate-900/50"
                )}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-3">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="border-t border-slate-800 bg-slate-900 px-4 py-2.5 text-xs text-slate-500">
        Showing {table.getRowModel().rows.length} of {data.length} internships
      </div>
    </div>
  );
}
