import { Badge } from "@/components/tailgrids/core/badge";
import type { Project } from "@/services/api/projects";
import { cn } from "@/utils/cn";
import { formatDate } from "@/utils/format-date";
import { BoxArchive1 } from "@tailgrids/icons";
import Link from "next/link";
import { DeleteProjectButton } from "./delete-project-button";

function initials(name: string) {
  const words = name.trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return "—";
  return words
    .slice(0, 2)
    .map((word) => word.charAt(0).toUpperCase())
    .join("");
}

export function ProjectCard({ project }: { project: Project }) {
  const created = formatDate(project.created_at);
  const isArchived = project.status === "archived";

  return (
    // The link covers the card rather than wrapping it: a delete button nested inside an
    // anchor is invalid, and a browser would sooner follow the link than press it.
    <div
      className={cn(
        "group relative flex w-full flex-col rounded-xl border p-5 transition hover:border-border-secondary-alt hover:shadow-sm focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-primary-500",
        // An archived project is still openable, but it should never read as a live one.
        isArchived
          ? "border-dashed border-card-border bg-background-gray-secondary"
          : "border-card-border bg-card-background",
      )}
    >
      <Link
        href={`/projects/${project.id}`}
        aria-label={`Open ${project.name}`}
        className="absolute inset-0 rounded-xl outline-none"
      />

      <div className="flex items-start justify-between gap-3">
        <span
          aria-hidden="true"
          className={cn(
            "flex size-10 shrink-0 items-center justify-center rounded-lg text-sm font-semibold",
            isArchived
              ? "bg-background-gray-secondary_alt text-text-tertiary"
              : "bg-background-gray-secondary_alt_2 text-white-100",
          )}
        >
          {initials(project.name)}
        </span>
        <div className="flex items-center gap-1.5">
          <Badge
            color={isArchived ? "gray" : "success"}
            size="sm"
            prefixIcon={
              isArchived ? (
                <BoxArchive1 aria-hidden="true" focusable="false" />
              ) : undefined
            }
          >
            {isArchived ? "Archived" : "Active"}
          </Badge>
          <DeleteProjectButton
            projectId={project.id}
            projectName={project.name}
            locationCount={project.location_count}
          />
        </div>
      </div>

      <h3
        className={cn(
          "mt-4 text-base leading-6 font-semibold tracking-[-0.015em] break-words underline-offset-4 group-hover:underline",
          isArchived ? "text-text-secondary" : "text-text-primary",
        )}
      >
        {project.name}
      </h3>
      <p className="mt-1 truncate text-xs text-text-tertiary">{project.slug}</p>

      <dl className="mt-5 flex items-end gap-8 border-t border-card-border pt-4">
        <div>
          <dt className="text-[11px] font-medium tracking-[0.08em] text-text-tertiary uppercase">
            Profiles
          </dt>
          <dd className="mt-1 text-sm font-semibold text-text-primary tabular-nums">
            {project.location_count}
          </dd>
        </div>
        <div>
          <dt className="text-[11px] font-medium tracking-[0.08em] text-text-tertiary uppercase">
            Created
          </dt>
          <dd className="mt-1 text-sm font-medium text-text-primary">
            {created ?? <span className="text-text-disable">Not set</span>}
          </dd>
        </div>
      </dl>
    </div>
  );
}
