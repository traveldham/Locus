"use client";

import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { LinkButton } from "@/components/common/link-button";
import { PageHeader } from "@/components/common/page-header";
import { SectionCard } from "@/components/common/section-card";
import { SourceMark } from "@/components/common/source-mark";
import { useLocationsQuery } from "@/hooks/use-locations";
import {
  useCompetitorsQuery,
  useRankHistoryQuery,
  useTrackedKeywordsQuery,
} from "@/hooks/use-market";
import { cn } from "@/utils/cn";
import { Buildings11, UserMultiple1 } from "@tailgrids/icons";
import { useMemo, useState } from "react";
import { CompetitorsTable } from "./competitors-table";
import { KeywordSelect, LocationSelect, WeekSelect } from "./market-selects";
import { MarketTableSkeleton } from "./market-skeletons";
import { formatWeekLong, isNotFound, NOT_FOUND_LABEL } from "./rank-format";

export interface CompetitorsViewProps {
  /** Carried over from the rankings screen so the same keyword stays selected. */
  initialLocationId?: string | null;
  initialKeywordId?: string | null;
}

export function CompetitorsView({
  initialLocationId = null,
  initialKeywordId = null,
}: CompetitorsViewProps) {
  const [pickedLocationId, setPickedLocationId] = useState<string | null>(initialLocationId);
  const [pickedKeywordId, setPickedKeywordId] = useState<string | null>(initialKeywordId);
  const [pickedWeek, setPickedWeek] = useState<string | null>(null);

  const locations = useLocationsQuery();
  const locationList = useMemo(() => locations.data ?? [], [locations.data]);
  const locationId =
    pickedLocationId && locationList.some((location) => location.id === pickedLocationId)
      ? pickedLocationId
      : (locationList[0]?.id ?? null);

  const keywords = useTrackedKeywordsQuery(locationId);
  const keywordList = useMemo(() => keywords.data?.items ?? [], [keywords.data]);
  const keywordId =
    pickedKeywordId && keywordList.some((keyword) => keyword.id === pickedKeywordId)
      ? pickedKeywordId
      : (keywordList[0]?.id ?? null);
  const selectedKeyword = keywordList.find((keyword) => keyword.id === keywordId) ?? null;

  // The weeks on offer are exactly the weeks the rankings endpoint recorded, so the
  // week picker can never ask the API for a week that was never measured.
  const rankings = useRankHistoryQuery(keywordId);
  const weeks = useMemo(
    () => (rankings.data?.points ?? []).map((point) => point.week_start).reverse(),
    [rankings.data],
  );
  const weekStart = pickedWeek && weeks.includes(pickedWeek) ? pickedWeek : (weeks[0] ?? null);

  const weekPoint =
    rankings.data?.points.find((point) => point.week_start === weekStart) ?? null;
  const yourRank = weekPoint && !isNotFound(weekPoint) ? weekPoint.rank_absolute : null;

  const competitors = useCompetitorsQuery(keywordId, weekStart);
  const items = competitors.data?.items ?? [];

  return (
    <div className="px-5 py-8 lg:px-8 lg:py-10">
      <PageHeader
        title="Competitors"
        description="The businesses ranking around you for a tracked keyword. Google never exposes a rival's profile, so Locus measures this itself — these figures will not appear in your Google dashboard."
        meta={<SourceMark source="locus" detail="Covers every figure on this page." />}
        actions={
          <LinkButton href="/market/rankings" appearance="outline">
            Back to rankings
          </LinkButton>
        }
      />

      <div className="mt-6 flex flex-col gap-3 rounded-xl border border-card-border bg-card-background p-4 lg:flex-row lg:items-center">
        <LocationSelect
          locations={locationList}
          value={locationId}
          onChange={(next) => {
            setPickedLocationId(next);
            setPickedKeywordId(null);
            setPickedWeek(null);
          }}
          isLoading={locations.isPending}
          className="w-full lg:max-w-72"
        />
        <KeywordSelect
          keywords={keywordList}
          value={keywordId}
          onChange={(next) => {
            setPickedKeywordId(next);
            setPickedWeek(null);
          }}
          className="w-full lg:max-w-72"
        />
        <WeekSelect
          weeks={weeks}
          value={weekStart}
          onChange={setPickedWeek}
          formatLabel={formatWeekLong}
          className="w-full lg:max-w-60"
        />
      </div>

      {locations.isError ? (
        <div className="mt-5 max-w-3xl">
          <ErrorState
            title="We could not load your profiles"
            onRetry={() => void locations.refetch()}
            isRetrying={locations.isFetching}
          />
        </div>
      ) : null}

      {!locations.isPending && !locations.isError && locationList.length === 0 ? (
        <div className="mt-5">
          <EmptyState
            icon={<Buildings11 aria-hidden="true" focusable="false" />}
            title="No profiles yet"
            description="Competitors are tracked against one of your profiles. Connect Google and import a profile to start."
            actions={<LinkButton href="/settings/integrations">Connect Google</LinkButton>}
          />
        </div>
      ) : null}

      {locationId && !keywords.isPending && !keywords.isError && keywordList.length === 0 ? (
        <div className="mt-5">
          <EmptyState
            icon={<UserMultiple1 aria-hidden="true" focusable="false" />}
            title="No keywords are tracked here"
            description="Competitors are found through a tracked keyword. Once this profile has one, the businesses ranking around you appear here."
          />
        </div>
      ) : null}

      {keywords.isError ? (
        <div className="mt-5 max-w-3xl">
          <ErrorState
            title="We could not load tracked keywords"
            onRetry={() => void keywords.refetch()}
            isRetrying={keywords.isFetching}
          />
        </div>
      ) : null}

      {keywordId ? (
        <div className="mt-5">
          <SectionCard
            title={
              selectedKeyword
                ? `Ranking around you — ${selectedKeyword.keyword}`
                : "Ranking around you"
            }
            icon={<UserMultiple1 aria-hidden="true" focusable="false" />}
            actions={<SourceMark source="locus" />}
            bodyClassName="px-0 py-0"
          >
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 border-b border-card-border px-5 py-3.5">
              <p className="text-sm leading-5 text-text-secondary">
                {weekStart ? (
                  <>
                    Week of{" "}
                    <span className="font-medium text-text-primary">
                      {formatWeekLong(weekStart)}
                    </span>
                  </>
                ) : (
                  "No week recorded yet"
                )}
              </p>
              {weekPoint ? (
                <p className="text-sm leading-5 text-text-secondary tabular-nums">
                  Your position:{" "}
                  <span className="font-medium text-text-primary">
                    {yourRank === null ? NOT_FOUND_LABEL : `#${yourRank}`}
                  </span>
                </p>
              ) : null}
            </div>

            <div className="px-5 py-5">
              {competitors.isPending ? (
                <MarketTableSkeleton columns={6} label="Loading competitors" />
              ) : null}

              {!competitors.isPending && competitors.isError ? (
                <ErrorState
                  title="We could not load competitors"
                  onRetry={() => void competitors.refetch()}
                  isRetrying={competitors.isFetching}
                />
              ) : null}

              {!competitors.isPending && !competitors.isError && items.length === 0 ? (
                <EmptyState
                  icon={<UserMultiple1 aria-hidden="true" focusable="false" />}
                  title="No competitors recorded for this week"
                  description={
                    weekStart
                      ? `Locus recorded no other business ranking for this keyword in the week of ${formatWeekLong(weekStart)}. Try another week.`
                      : "Locus has not recorded a week for this keyword yet."
                  }
                  className="border-0 bg-transparent py-8"
                />
              ) : null}

              {!competitors.isPending && !competitors.isError && items.length > 0 ? (
                <div
                  aria-busy={competitors.isFetching}
                  className={cn(
                    "transition-opacity",
                    competitors.isFetching && "opacity-60",
                  )}
                >
                  <CompetitorsTable competitors={items} yourRank={yourRank} />
                  {yourRank === null ? (
                    <p className="mt-3 text-xs leading-5 text-text-tertiary">
                      Your own position is not shown for this week, so no comparison
                      against these businesses is drawn.
                    </p>
                  ) : null}
                </div>
              ) : null}
            </div>
          </SectionCard>
        </div>
      ) : null}
    </div>
  );
}
