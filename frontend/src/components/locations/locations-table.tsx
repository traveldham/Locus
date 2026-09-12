"use client";

import { NotSet } from "@/components/common/data-field";
import { Input } from "@/components/tailgrids/core/input";
import {
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRoot,
  TableRow,
} from "@/components/tailgrids/core/table";
import { TextField } from "@/components/tailgrids/core/text-field";
import type { LocationSummary } from "@/services/api/locations";
import { cn } from "@/utils/cn";
import { formatDateTime } from "@/utils/format-date";
import { ChevronBothDirection, ChevronDown, ChevronUp, Search1 } from "@tailgrids/icons";
import Link from "next/link";
import { useMemo, useState } from "react";
import { LocationStatusChip, locationStatusKinds } from "./location-status-chip";

type SortColumn = "title" | "address" | "category" | "store_code" | "last_synced_at";
type SortDirection = "asc" | "desc";

interface SortState {
  column: SortColumn;
  direction: SortDirection;
}

const COLUMNS: { id: SortColumn; label: string; className?: string }[] = [
  { id: "title", label: "Location", className: "w-[24%]" },
  { id: "address", label: "Address", className: "w-[26%]" },
  { id: "category", label: "Primary category", className: "w-[16%]" },
  { id: "store_code", label: "Store code", className: "w-[10%]" },
];

function sortValue(location: LocationSummary, column: SortColumn) {
  switch (column) {
    case "title":
      return location.title;
    case "address":
      return location.address;
    case "category":
      return location.primary_category_display;
    case "store_code":
      return location.store_code;
    case "last_synced_at":
      return location.last_synced_at;
  }
}

function matchesQuery(location: LocationSummary, query: string) {
  return [location.title, location.address, location.primary_category_display, location.store_code]
    .filter((value): value is string => Boolean(value))
    .some((value) => value.toLowerCase().includes(query));
}

interface LocationsTableProps {
  locations: LocationSummary[];
  /** The list view keeps its search; short embedded tables can opt out. */
  showSearch?: boolean;
  className?: string;
}

export function LocationsTable({ locations, showSearch = true, className }: LocationsTableProps) {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<SortState>({ column: "title", direction: "asc" });

  const query = search.trim().toLowerCase();

  const visible = useMemo(() => {
    const filtered = query ? locations.filter((item) => matchesQuery(item, query)) : locations;

    return [...filtered].sort((a, b) => {
      const left = sortValue(a, sort.column);
      const right = sortValue(b, sort.column);
      // Missing values always sort last so an empty field never hides a populated one.
      if (!left) return right ? 1 : 0;
      if (!right) return -1;
      const comparison = left.localeCompare(right, undefined, {
        numeric: true,
        sensitivity: "base",
      });
      return sort.direction === "asc" ? comparison : -comparison;
    });
  }, [locations, query, sort]);

  function toggleSort(column: SortColumn) {
    setSort((current) =>
      current.column === column
        ? { column, direction: current.direction === "asc" ? "desc" : "asc" }
        : { column, direction: "asc" },
    );
  }

  return (
    <div className={cn("flex flex-col gap-4", className)}>
      {showSearch ? (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <TextField
            aria-label="Search locations"
            value={search}
            onChange={setSearch}
            className="relative w-full sm:max-w-sm"
          >
            <Search1
              aria-hidden="true"
              focusable="false"
              className="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-icon-tertiary"
            />
            <Input
              type="search"
              placeholder="Search name, address or store code"
              className="h-11 w-full pl-10"
            />
          </TextField>
          <p className="text-sm text-text-tertiary" aria-live="polite">
            {query
              ? `${visible.length} of ${locations.length} locations`
              : `${locations.length} ${locations.length === 1 ? "location" : "locations"}`}
          </p>
        </div>
      ) : null}

      <TableRoot className="min-w-[64rem]">
        <TableHeader className="bg-background-gray-secondary">
          <TableRow>
            {COLUMNS.map((column) => (
              <SortableHead
                key={column.id}
                label={column.label}
                column={column.id}
                sort={sort}
                onToggle={toggleSort}
                className={column.className}
              />
            ))}
            <TableHead className="w-[16%]">Status</TableHead>
            <SortableHead
              label="Last synced"
              column="last_synced_at"
              sort={sort}
              onToggle={toggleSort}
              className="w-[14%]"
            />
          </TableRow>
        </TableHeader>
        <TableBody>
          {visible.length === 0 ? (
            <tr>
              <td colSpan={6} className="px-5 py-14 text-center">
                <p className="text-sm font-medium text-text-primary">No matching locations</p>
                <p className="mt-1.5 text-sm text-text-tertiary">
                  {query
                    ? `No location matches “${search.trim()}”. Try a different name, address or store code.`
                    : "There are no locations to show here."}
                </p>
              </td>
            </tr>
          ) : (
            visible.map((location) => (
              <TableRow key={location.id} className="transition hover:bg-background-gray-secondary">
                <TableCell className="py-2">
                  <Link
                    href={`/locations/${location.id}`}
                    className="inline-flex min-h-11 items-center text-sm font-semibold text-text-primary underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
                  >
                    {location.title}
                  </Link>
                </TableCell>
                <TableCell className="py-2 text-text-secondary">
                  {location.address ? (
                    <span className="block max-w-80 truncate" title={location.address}>
                      {location.address}
                    </span>
                  ) : (
                    <NotSet />
                  )}
                </TableCell>
                <TableCell className="py-2 text-text-secondary">
                  {location.primary_category_display ?? <NotSet />}
                </TableCell>
                <TableCell className="py-2 text-text-secondary tabular-nums">
                  {location.store_code ?? <NotSet />}
                </TableCell>
                <TableCell className="py-2">
                  <div className="flex flex-wrap gap-1.5">
                    {locationStatusKinds(location).map((kind) => (
                      <LocationStatusChip key={kind} kind={kind} />
                    ))}
                  </div>
                </TableCell>
                <TableCell className="py-2 whitespace-nowrap text-text-secondary tabular-nums">
                  {formatDateTime(location.last_synced_at) ?? <NotSet />}
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </TableRoot>
    </div>
  );
}

interface SortableHeadProps {
  label: string;
  column: SortColumn;
  sort: SortState;
  onToggle: (column: SortColumn) => void;
  className?: string;
}

function SortableHead({ label, column, sort, onToggle, className }: SortableHeadProps) {
  const isActive = sort.column === column;
  const ariaSort = isActive ? (sort.direction === "asc" ? "ascending" : "descending") : "none";
  const Icon = !isActive ? ChevronBothDirection : sort.direction === "asc" ? ChevronUp : ChevronDown;

  return (
    <TableHead aria-sort={ariaSort} className={cn("p-0", className)}>
      <button
        type="button"
        onClick={() => onToggle(column)}
        className="flex h-12 w-full items-center gap-1.5 px-5 text-left text-xs font-medium text-title-50 transition hover:text-text-primary focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-primary-500"
      >
        {label}
        <Icon
          aria-hidden="true"
          focusable="false"
          className={cn("size-3.5 shrink-0", isActive ? "text-text-primary" : "text-icon-tertiary")}
        />
        <span className="sr-only">
          {isActive
            ? `Sorted ${sort.direction === "asc" ? "ascending" : "descending"}. Activate to reverse.`
            : "Activate to sort by this column."}
        </span>
      </button>
    </TableHead>
  );
}
