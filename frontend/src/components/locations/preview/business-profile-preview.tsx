"use client";

import { useMediaSummaryQuery } from "@/hooks/use-insights";
import { useLatestRecommendations } from "@/hooks/use-recommendations";
import type { LocationDetail } from "@/services/api/locations";
import { reviewsApi } from "@/services/api/reviews";
import { useQuery } from "@tanstack/react-query";
import { ClockThree, Link1AngularRight, MapMarker5 } from "@tailgrids/icons";
import Link from "next/link";
import styles from "./google-profile.module.css";
import { useId, useState } from "react";
import {
  dayLabel,
  describePeriod,
  humanizeToken,
  normalizeToken,
  regularPeriods,
  WEEK_DAYS,
} from "../hours-model";
import {
  PreviewPosts,
  PreviewReviews,
  previewControl,
  RatingStars,
} from "./profile-preview-content";

function webUrl(value: string | null) {
  if (!value) return null;
  try {
    const url = new URL(value);
    return ["https:", "http:"].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
}

const sections = ["Overview", "Reviews", "Updates", "About"] as const;
type PreviewSection = (typeof sections)[number];

export function BusinessProfilePreview({
  location,
  onEdit,
}: {
  location: LocationDetail;
  onEdit: () => void;
}) {
  const [section, setSection] = useState<PreviewSection>("Overview");
  const panelId = useId();
  const summary = useQuery({
    queryKey: ["reviews", "summary", location.id],
    queryFn: () => reviewsApi.summary(location.id),
    staleTime: 30_000,
    retry: 1,
  });
  const mediaQuery = useMediaSummaryQuery({ locationId: location.id });
  const media = mediaQuery.data?.items.find(
    (item) => item.location_id === location.id,
  );
  const audit = useLatestRecommendations(location.id);
  const recommendations =
    audit.data?.run?.items.filter((item) => item.location_id === location.id) ??
    [];
  const website = webUrl(location.website_uri);
  const directions =
    location.source === "fixture" ? null : webUrl(location.maps_uri);
  const phone = location.phone_primary?.replace(/[^\d+]/g, "");
  const periods = regularPeriods(location.hours_periods);

  return (
    <div className="mt-6 grid items-start gap-6 xl:grid-cols-[minmax(0,720px)_minmax(240px,1fr)]">
      <div
        className={`${styles.panel} min-w-0 overflow-hidden border border-card-border bg-card-background`}
      >
        <div className="border-b border-card-border bg-background-gray-secondary px-5 py-3 text-xs leading-5 text-text-secondary sm:px-7">
          Google-style preview ·{" "}
          {location.source === "fixture"
            ? "Synthetic sample data"
            : "Stored profile data"}
          . Not a live Google listing; Google’s layout may differ.
        </div>
        <div className="px-5 pt-6 sm:px-7">
          <h2 className="text-2xl font-semibold leading-tight text-text-primary sm:text-3xl">
            {location.title}
          </h2>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-text-secondary">
            {summary.isPending ? (
              <span role="status">Loading rating…</span>
            ) : null}
            {summary.isError ? (
              <button
                className="min-h-11 underline"
                onClick={() => void summary.refetch()}
              >
                Rating unavailable. Retry
              </button>
            ) : null}
            {summary.data ? (
              summary.data.average !== null ? (
                <>
                  <span className="font-medium text-text-primary">
                    {summary.data.average.toFixed(1)}
                  </span>
                  <RatingStars rating={summary.data.average} />
                  <button
                    className="min-h-11 underline underline-offset-4 focus-visible:outline-primary-500"
                    onClick={() => setSection("Reviews")}
                  >
                    {summary.data.total.toLocaleString()} stored reviews
                  </button>
                </>
              ) : (
                <span>No stored reviews</span>
              )
            ) : null}
          </div>
          <p className="mt-1 text-sm text-text-secondary">
            {location.primary_category_display || "Category not supplied"}
            {location.locality ? ` in ${location.locality}` : ""}
          </p>
          <div
            className="mt-5 flex flex-wrap gap-2"
            aria-label="Business actions"
          >
            {website ? (
              <a
                className={previewControl}
                href={website}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Link1AngularRight className="size-4" aria-hidden="true" />
                Website
              </a>
            ) : (
              <button
                className={previewControl}
                disabled
                title="No valid website URL stored"
              >
                Website unavailable
              </button>
            )}
            {directions ? (
              <a
                className={previewControl}
                href={directions}
                target="_blank"
                rel="noopener noreferrer"
              >
                <MapMarker5 className="size-4" aria-hidden="true" />
                Directions
              </a>
            ) : (
              <button
                className={previewControl}
                disabled
                title={
                  location.source === "fixture"
                    ? "Directions are disabled for synthetic profiles"
                    : "No map URL stored"
                }
              >
                Directions unavailable
              </button>
            )}
            {phone && location.source !== "fixture" ? (
              <a className={previewControl} href={`tel:${phone}`}>
                Call
              </a>
            ) : (
              <button
                className={previewControl}
                disabled
                title={
                  location.source === "fixture"
                    ? "Calling is disabled for synthetic phone numbers"
                    : "No phone number stored"
                }
              >
                Call unavailable
              </button>
            )}
          </div>
          <nav
            className="mt-5 flex gap-1 border-b border-card-border"
            aria-label="Profile preview sections"
          >
            {sections.map((label) => (
              <button
                key={label}
                aria-pressed={section === label}
                aria-controls={panelId}
                onClick={() => setSection(label)}
                className={`min-h-12 min-w-11 flex-1 border-b-2 px-1 text-sm transition-colors focus-visible:outline-primary-500 sm:px-3 ${section === label ? "border-primary-500 font-semibold text-text-primary" : "border-transparent text-text-secondary hover:text-text-primary"}`}
              >
                {label}
              </button>
            ))}
          </nav>
        </div>
        <div id={panelId} className="px-5 py-6 sm:px-7">
          {section === "Overview" ? (
            <>
              <div className="flex min-h-36 flex-col items-center justify-center rounded-xl bg-background-gray-secondary px-5 py-6 text-center">
                <p className="text-base font-medium text-text-primary">
                  {media
                    ? `${media.photo_count} photos · ${media.video_count} videos recorded`
                    : "Profile imagery"}
                </p>
                <p className="mt-2 max-w-sm text-sm leading-6 text-text-secondary">
                  Photo files and URLs are not included in the stored dataset.
                  No business imagery is invented for this preview.
                </p>
                {mediaQuery.isPending ? (
                  <p role="status" className="mt-2 text-xs text-text-secondary">
                    Loading media summary…
                  </p>
                ) : null}
                {mediaQuery.isError ? (
                  <button
                    className="mt-2 min-h-11 text-sm underline"
                    onClick={() => void mediaQuery.refetch()}
                  >
                    Media counts unavailable. Retry
                  </button>
                ) : null}
              </div>
              <dl className="mt-5 divide-y divide-card-border text-sm">
                <div className="flex gap-3 py-4">
                  <MapMarker5
                    className="mt-0.5 size-5 shrink-0 text-text-secondary"
                    aria-hidden="true"
                  />
                  <div>
                    <dt className="font-medium text-text-primary">Address</dt>
                    <dd className="mt-1 leading-6 text-text-secondary">
                      {location.address ||
                        [
                          location.locality,
                          location.administrative_area,
                          location.postal_code,
                        ]
                          .filter(Boolean)
                          .join(", ") ||
                        "Not supplied"}
                    </dd>
                  </div>
                </div>
                <div className="py-4">
                  <dt className="font-medium text-text-primary">
                    Business status
                  </dt>
                  <dd className="mt-1 text-text-secondary">
                    {location.open_status === "open"
                      ? "Operating · see regular hours below"
                      : location.open_status
                        ? humanizeToken(location.open_status)
                        : "Unknown"}
                  </dd>
                </div>
                <div className="py-4">
                  <dt className="font-medium text-text-primary">Phone</dt>
                  <dd className="mt-1 text-text-secondary">
                    {location.phone_primary || "Not supplied"}
                  </dd>
                </div>
              </dl>
              <details className="border-y border-card-border py-1">
                <summary className="min-h-11 cursor-pointer py-3 text-sm font-medium text-text-primary">
                  <ClockThree
                    className="mr-2 inline size-4"
                    aria-hidden="true"
                  />
                  Regular opening hours
                </summary>
                {periods.length ? (
                  <dl className="pb-4 text-sm">
                    {WEEK_DAYS.map((day) => (
                      <div
                        className="flex justify-between gap-4 py-2"
                        key={day}
                      >
                        <dt className="text-text-secondary">{dayLabel(day)}</dt>
                        <dd className="text-right text-text-primary">
                          {periods
                            .filter(
                              (period) =>
                                normalizeToken(period.open_day) === day,
                            )
                            .map(describePeriod)
                            .join("; ") || "Closed"}
                        </dd>
                      </div>
                    ))}
                  </dl>
                ) : (
                  <p className="pb-4 text-sm text-text-secondary">
                    No regular hours supplied.
                  </p>
                )}
                <p className="pb-4 text-xs leading-5 text-text-secondary">
                  Stored schedule only. Special hours and the profile’s time zone are
                  not resolved into a live “open now” status.
                </p>
              </details>
              <h3 className="mt-6 font-semibold text-text-primary">
                From the business
              </h3>
              <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-7 text-text-secondary">
                {location.description || "No business description supplied."}
              </p>
            </>
          ) : null}
          {section === "Reviews" ? (
            <PreviewReviews key={location.id} locationId={location.id} />
          ) : null}
          {section === "Updates" ? (
            <PreviewPosts key={location.id} locationId={location.id} />
          ) : null}
          {section === "About" ? (
            <section>
              <h3 className="text-lg font-semibold text-text-primary">
                About this business
              </h3>
              <p className="mt-3 whitespace-pre-wrap break-words text-sm leading-7 text-text-secondary">
                {location.description || "No description supplied."}
              </p>
              <h4 className="mt-6 font-medium text-text-primary">Categories</h4>
              <p className="mt-2 text-sm text-text-secondary">
                {location.categories
                  .map(
                    (category) =>
                      category.display_name || category.category_name,
                  )
                  .join(" · ") ||
                  location.primary_category_display ||
                  "Not supplied"}
              </p>
              <h4 className="mt-6 font-medium text-text-primary">
                Recorded attributes
              </h4>
              <p className="mt-2 text-xs leading-5 text-text-secondary">
                Only stored values are shown. “No” is an explicit value, not a
                missing attribute.
              </p>
              <dl className="mt-3 divide-y divide-card-border text-sm">
                {location.attributes.map((attribute) => (
                  <div
                    key={attribute.attribute_id}
                    className="flex flex-wrap justify-between gap-2 py-3"
                  >
                    <dt className="text-text-secondary">
                      {humanizeToken(
                        attribute.attribute_id.replace(/^attributes\//, ""),
                      )}
                    </dt>
                    <dd className="font-medium text-text-primary">
                      {attribute.values.length
                        ? attribute.values
                            .map((value) =>
                              value === true
                                ? "Yes"
                                : value === false
                                  ? "No"
                                  : value === null
                                    ? "Unknown"
                                    : typeof value === "object"
                                      ? JSON.stringify(value)
                                      : String(value),
                            )
                            .join(", ")
                        : "Unknown"}
                    </dd>
                  </div>
                ))}
              </dl>
              {!location.attributes.length ? (
                <p className="mt-4 text-sm text-text-secondary">
                  No attribute values supplied.
                </p>
              ) : null}
            </section>
          ) : null}
        </div>
      </div>
      <aside
        className="min-w-0 px-1 py-2"
        aria-label="Operator recommendations"
      >
        <h2 className="text-lg font-semibold text-text-primary">
          Improve this profile
        </h2>
        <p className="mt-2 text-sm leading-6 text-text-secondary">
          Your operator workspace. These actions are not part of the public
          business profile.
        </p>
        {audit.isPending ? (
          <p role="status" className="mt-4 text-sm text-text-secondary">
            Loading saved recommendations…
          </p>
        ) : null}
        {audit.isError ? (
          <button
            className={`${previewControl} mt-4`}
            onClick={() => void audit.refetch()}
          >
            Recommendations unavailable. Retry
          </button>
        ) : null}
        {audit.data?.inputs_changed ? (
          <p className="mt-4 text-sm text-badge-warning-text">
            Data has changed. Regenerate the audit before acting on these saved
            findings.
          </p>
        ) : null}
        {audit.data?.run ? (
          <p className="mt-4 text-xs text-text-secondary">
            Saved analysis: {audit.data.run.as_of} · {recommendations.length}{" "}
            actions
          </p>
        ) : null}
        <div className="mt-3 divide-y divide-card-border">
          {recommendations.slice(0, 3).map((item) => (
            <div key={item.key} className="py-4">
              <p className="text-xs font-medium text-text-secondary">
                {humanizeToken(item.severity ?? "notice")}
              </p>
              <h3 className="mt-1 font-medium text-text-primary">
                {item.title}
              </h3>
              <p className="mt-2 text-sm leading-6 text-text-secondary">
                {item.why}
              </p>
            </div>
          ))}
        </div>
        {!audit.isPending && !audit.isError && !recommendations.length ? (
          <p className="mt-4 text-sm leading-6 text-text-secondary">
            No saved actions for this profile. Open the audit to check coverage
            or generate an analysis.
          </p>
        ) : null}
        <div className="mt-5 flex flex-wrap gap-3">
          <Link
            className={previewControl}
            href={`/recommendations/${location.id}`}
          >
            View full profile audit
          </Link>
          <button className={previewControl} onClick={onEdit}>
            Edit profile details
          </button>
        </div>
        <p className="mt-5 text-xs leading-5 text-text-secondary">
          Preview values come from your current database. Saved recommendations
          may use an earlier snapshot.
        </p>
      </aside>
    </div>
  );
}
