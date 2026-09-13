"use client";

import {
  recommendationApi,
  type Recommendation,
} from "@/services/api/recommendations";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

export function EvidencePanel({
  runId,
  item,
}: {
  runId: string;
  item: Recommendation;
}) {
  const [source, setSource] = useState(item.evidence[0]?.source ?? "");
  const [offset, setOffset] = useState(0);
  const rows = useQuery({
    queryKey: ["recommendation-evidence", runId, item.key, source, offset],
    queryFn: () => recommendationApi.evidence(runId, item.key, source, offset),
    retry: 1,
  });
  return (
    <div className="space-y-3 text-sm">
      <div>
        <h4 className="font-medium text-text-primary">Why we flagged this</h4>
        <p className="mt-1 leading-6 text-text-secondary">{item.why}</p>
      </div>
      <ul className="space-y-2">
        {item.evidence.map((e, index) => (
          <li
            key={`${e.source}-${index}`}
            className="leading-6 text-text-secondary"
          >
            <span className="font-medium text-text-primary">
              {e.calculation}.
            </span>{" "}
            {Object.entries(e.values).map(([key, value], valueIndex) => (
              <span key={key}>
                {valueIndex ? " · " : ""}
                {key.replaceAll("_", " ")}: {showValue(value)}
              </span>
            ))}
          </li>
        ))}
      </ul>
      <p className="text-xs leading-5 text-text-tertiary">{item.limitation}</p>
      <details className="border-t border-card-border pt-3">
        <summary className="min-h-11 cursor-pointer py-3 font-medium text-text-secondary underline-offset-4 hover:text-text-primary hover:underline focus-visible:outline-primary-500">
          View source records
        </summary>
        <div className="space-y-3 pb-2">
          <p className="text-xs leading-5 text-text-tertiary">
            {item.confidence_reason}
          </p>
          <label className="block text-sm text-text-secondary">
            Evidence source
            <select
              value={source}
              onChange={(e) => {
                setSource(e.target.value);
                setOffset(0);
              }}
              className="mt-2 block min-h-11 w-full rounded-lg border border-card-border bg-card-background px-3 text-text-primary focus-visible:outline-primary-500"
            >
              {[...new Set(item.evidence.map((e) => e.source))].map((s) => (
                <option key={s} value={s}>
                  {s.replaceAll("_", " ")}
                </option>
              ))}
            </select>
          </label>
          {rows.isPending ? <p role="status">Loading evidence…</p> : null}
          {rows.isError ? (
            <button
              type="button"
              onClick={() => void rows.refetch()}
              className="min-h-11 underline"
            >
              Evidence could not load. Retry
            </button>
          ) : null}
          {rows.data ? (
            <>
              <EvidenceTable rows={rows.data.items} />
              <div className="flex flex-wrap items-center gap-4">
                <span>
                  {rows.data.total} records · page {Math.floor(offset / 50) + 1}
                </span>
                <button
                  type="button"
                  disabled={offset === 0}
                  onClick={() => setOffset(offset - 50)}
                  className="min-h-11 underline disabled:opacity-40"
                >
                  Previous records
                </button>
                <button
                  type="button"
                  disabled={offset + 50 >= rows.data.total}
                  onClick={() => setOffset(offset + 50)}
                  className="min-h-11 underline disabled:opacity-40"
                >
                  Next records
                </button>
              </div>
            </>
          ) : null}
        </div>
      </details>
    </div>
  );
}

function showValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "not set";
  if (typeof value === "boolean") return value ? "yes" : "no";
  if (Array.isArray(value)) return value.length ? value.join(", ") : "none";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

/** The cited rows as a table. A stored record should be readable, not pasted JSON. */
function EvidenceTable({ rows }: { rows: Record<string, unknown>[] }) {
  if (!rows.length) {
    return (
      <p className="text-text-secondary">
        No stored records matched this source.
      </p>
    );
  }
  // Columns that are empty for every row tell the reader nothing, so they are dropped.
  const columns = Object.keys(rows[0]).filter((key) =>
    rows.some(
      (row) => row[key] !== null && row[key] !== undefined && row[key] !== "",
    ),
  );

  function show(value: unknown): string {
    if (value === null || value === undefined || value === "") return "—";
    if (typeof value === "boolean") return value ? "Yes" : "No";
    if (Array.isArray(value)) return value.length ? value.join(", ") : "—";
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
  }

  return (
    <div className="max-h-80 overflow-auto rounded-lg border border-card-border">
      <table className="w-full border-collapse text-xs">
        <thead className="sticky top-0 bg-background-gray-secondary">
          <tr className="text-left">
            {columns.map((column) => (
              <th
                key={column}
                scope="col"
                className="px-3 py-2 font-medium whitespace-nowrap text-text-tertiary"
              >
                {column.replaceAll("_", " ")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr
              key={String(row.id ?? index)}
              className="border-t border-card-border"
            >
              {columns.map((column) => (
                <td
                  key={column}
                  className="max-w-64 truncate px-3 py-2 text-text-primary"
                  title={show(row[column])}
                >
                  {show(row[column])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
