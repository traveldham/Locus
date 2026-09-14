"use client";

import type { MediaSummary } from "@/services/api/insights";
import { cn } from "@/utils/cn";
import { formatDate } from "@/utils/format-date";
import { CheckCircle1, InfoTriangle, Video } from "@tailgrids/icons";
import { formatExact } from "./chart-series";
import styles from "./chart-theme.module.css";
import { SourceMark } from "@/components/common/source-mark";

interface CategorySlice {
  key: string;
  label: string;
  count: number;
  color: string;
}

/**
 * Google's category counts are not a partition of the photo total: a photo can be
 * uncategorised, so the three named categories usually fall short of it. The
 * remainder is therefore named and drawn, never absorbed into the categories.
 */
function buildSlices(media: MediaSummary) {
  const named: CategorySlice[] = [
    {
      key: "interior",
      label: "Interior",
      count: media.interior_photo_count,
      color: "var(--viz-series-1)",
    },
    {
      key: "exterior",
      label: "Exterior",
      count: media.exterior_photo_count,
      color: "var(--viz-series-2)",
    },
    {
      key: "team",
      label: "Team",
      count: media.team_photo_count,
      color: "var(--viz-series-3)",
    },
  ];

  const categorised = named.reduce((sum, slice) => sum + slice.count, 0);
  const remainder = media.photo_count - categorised;

  return {
    named,
    remainder,
    /** True when the categories exceed the total, so no share can be drawn honestly. */
    isInconsistent: remainder < 0,
    slices:
      remainder > 0
        ? [
            ...named,
            {
              key: "uncategorised",
              label: "Uncategorised",
              count: remainder,
              color: "var(--viz-neutral)",
            },
          ]
        : named,
  };
}

function StatusChip({ isSet, label }: { isSet: boolean; label: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium",
        isSet
          ? "bg-badge-success-background text-badge-success-text"
          : "bg-badge-warning-background text-badge-warning-text",
      )}
    >
      {isSet ? (
        <CheckCircle1 aria-hidden="true" focusable="false" className="size-3.5 shrink-0" />
      ) : (
        <InfoTriangle aria-hidden="true" focusable="false" className="size-3.5 shrink-0" />
      )}
      {isSet ? `${label} set` : `No ${label.toLowerCase()}`}
    </span>
  );
}

export function PhotoCoverageCard({ media }: { media: MediaSummary }) {
  const { named, remainder, isInconsistent, slices } = buildSlices(media);
  const drawableTotal = slices.reduce((sum, slice) => sum + slice.count, 0);
  const canDrawBar = !isInconsistent && drawableTotal > 0;
  const lastUploaded = formatDate(media.last_photo_uploaded_on);
  const hasGap = !media.has_profile_photo || !media.has_cover_photo;

  return (
    <article
      className={cn(
        styles.scope,
        "flex flex-col rounded-xl border bg-card-background p-5",
        hasGap ? "border-badge-warning-text/40" : "border-card-border",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="min-w-0 text-sm font-semibold break-words text-text-primary">
          {media.location_title}
        </h3>
        <SourceMark source={media.source} className="shrink-0" />
      </div>

      <p className="mt-3 text-[28px] leading-9 font-semibold tracking-[-0.02em] text-text-primary">
        {formatExact(media.photo_count)}
        <span className="ml-2 text-sm font-medium text-text-tertiary">
          {media.photo_count === 1 ? "photo" : "photos"}
        </span>
      </p>

      {canDrawBar ? (
        <div
          role="img"
          aria-label={slices
            .map((slice) => `${slice.label}: ${slice.count.toLocaleString()}`)
            .join(", ")}
          className="mt-4 flex h-2.5 w-full gap-[2px] overflow-hidden"
        >
          {slices
            .filter((slice) => slice.count > 0)
            .map((slice, index, visible) => (
              <span
                key={slice.key}
                style={{
                  backgroundColor: slice.color,
                  flexGrow: slice.count,
                  flexBasis: 0,
                }}
                className={cn(
                  "block h-full min-w-[3px]",
                  index === 0 && "rounded-l-full",
                  index === visible.length - 1 && "rounded-r-full",
                )}
              />
            ))}
        </div>
      ) : null}

      <ul className="mt-4 flex flex-col gap-2">
        {named.map((slice) => (
          <li key={slice.key} className="flex items-center gap-2 text-sm">
            <span
              aria-hidden="true"
              className="size-2.5 shrink-0 rounded-sm"
              style={{ backgroundColor: slice.color }}
            />
            <span className="text-text-secondary">{slice.label}</span>
            <span className="ml-auto font-medium text-text-primary tabular-nums">
              {formatExact(slice.count)}
            </span>
          </li>
        ))}
        {remainder > 0 ? (
          <li className="flex items-center gap-2 text-sm">
            <span
              aria-hidden="true"
              className="size-2.5 shrink-0 rounded-sm"
              style={{ backgroundColor: "var(--viz-neutral)" }}
            />
            <span className="text-text-secondary">Uncategorised</span>
            <span className="ml-auto font-medium text-text-primary tabular-nums">
              {formatExact(remainder)}
            </span>
          </li>
        ) : null}
        <li className="flex items-center gap-2 border-t border-card-border pt-2 text-sm">
          <Video
            aria-hidden="true"
            focusable="false"
            className="size-3.5 shrink-0 text-icon-tertiary"
          />
          <span className="text-text-secondary">
            {media.video_count === 1 ? "Video" : "Videos"}
          </span>
          <span className="ml-auto font-medium text-text-primary tabular-nums">
            {formatExact(media.video_count)}
          </span>
        </li>
      </ul>

      {isInconsistent ? (
        <p className="mt-3 text-xs leading-5 text-text-tertiary">
          Google&rsquo;s category counts add up to more than the photo total for this profile,
          so no share of the total is drawn. The counts are listed as reported.
        </p>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-2">
        <StatusChip isSet={media.has_profile_photo} label="Profile photo" />
        <StatusChip isSet={media.has_cover_photo} label="Cover photo" />
      </div>

      <p className="mt-4 border-t border-card-border pt-3 text-xs leading-5 text-text-tertiary">
        {lastUploaded ? (
          <>Last photo uploaded {lastUploaded}.</>
        ) : (
          <>Google did not report when a photo was last uploaded.</>
        )}
      </p>
    </article>
  );
}
