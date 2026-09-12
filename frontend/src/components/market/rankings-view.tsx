"use client";

import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { LinkButton } from "@/components/common/link-button";
import { PageHeader } from "@/components/common/page-header";
import { SectionCard } from "@/components/common/section-card";
import { SourceMark } from "@/components/common/source-mark";
import { useLocationsQuery } from "@/hooks/use-locations";
import { useRankHistoryQuery, useTrackedKeywordsQuery } from "@/hooks/use-market";
import type { SearchIntent } from "@/services/api/market";
import { cn } from "@/utils/cn";
import { Buildings11, Search1, TrendUp2 } from "@tailgrids/icons";
import { useMemo, useState } from "react";
import { KeywordList } from "./keyword-list";
import { IntentSelect, LocationSelect } from "./market-selects";
import { KeywordListSkeleton, RankChartSkeleton } from "./market-skeletons";
import { RankChart } from "./rank-chart";
import { RankHistoryTable } from "./rank-history-table";
import { RankSummary } from "./rank-summary";

export function RankingsView() {
  const [pickedLocationId, setPickedLocationId] = useState<string | null>(null);
  const [pickedKeywordId, setPickedKeywordId] = useState<string | null>(null);
  const [intent, setIntent] = useState<SearchIntent | null>(null);
  const [showTable, setShowTable] = useState(false);

  const locations = useLocationsQuery();
  const locationList = useMemo(() => locations.data ?? [], [locations.data]);
  // Falling back to the first location keeps the screen useful on arrival without
  // pinning a choice the person never made.
  const locationId =
    pickedLocationId && locationList.some((location) => location.id === pickedLocationId)
      ? pickedLocationId
      : (locationList[0]?.id ?? null);

  const keywords = useTrackedKeywordsQuery(locationId);
  const allKeywords = useMemo(() => keywords.data?.items ?? [], [keywords.data]);

  const intents = useMemo(() => {
    const seen: SearchIntent[] = [];
    for (const keyword of allKeywords) {
      if (!seen.includes(keyword.search_intent)) seen.push(keyword.search_intent);
    }
    return seen;
  }, [allKeywords]);

  const visibleKeywords = useMemo(
    () =>
      intent === null
        ? allKeywords
        : allKeywords.filter((keyword) => keyword.search_intent === intent),
    [allKeywords, intent],
  );

  const keywordId =
    pickedKeywordId && visibleKeywords.some((keyword) => keyword.id === pickedKeywordId)
      ? pickedKeywordId
      : (visibleKeywords[0]?.id ?? null);
  const selectedKeyword = visibleKeywords.find((keyword) => keyword.id === keywordId) ?? null;

  const rankings = useRankHistoryQuery(keywordId);
  const points = rankings.data?.points ?? [];

  const locationName =
    locationList.find((location) => location.id === locationId)?.title ?? null;

  return (
    <div className="px-5 py-8 lg:px-8 lg:py-10">
      <PageHeader
        title="Keyword rankings"
        description="Where each tracked keyword places your listing in local search, week by week. Google publishes no ranking data, so these positions are measured by Locus and will not appear in your Google dashboard."
        meta={<SourceMark source="locus" detail="Covers every position on this page." />}
      />

      <div className="mt-6 flex flex-col gap-3 rounded-xl border border-card-border bg-card-background p-4 lg:flex-row lg:items-center">
        <LocationSelect
          locations={locationList}
          value={locationId}
          onChange={(next) => {
            setPickedLocationId(next);
            setPickedKeywordId(null);
          }}
          isLoading={locations.isPending}
          className="w-full lg:max-w-72"
        />
        <IntentSelect
          intents={intents}
          value={intent}
          onChange={(next) => {
            setIntent(next);
            setPickedKeywordId(null);
          }}
          className="w-full lg:max-w-56"
        />
      </div>

      {locations.isError ? (
        <div className="mt-5 max-w-3xl">
          <ErrorState
            title="We could not load your locations"
            onRetry={() => void locations.refetch()}
            isRetrying={locations.isFetching}
          />
        </div>
      ) : null}

      {!locations.isPending && !locations.isError && locationList.length === 0 ? (
        <div className="mt-5">
          <EmptyState
            icon={<Buildings11 aria-hidden="true" focusable="false" />}
            title="No locations yet"
            description="Rankings are tracked per location. Connect Google and import a location, then keyword tracking has something to measure."
            actions={
              <LinkButton href="/settings/integrations">Connect Google</LinkButton>
            }
          />
        </div>
      ) : null}

      {locationId ? (
        <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,20rem)_minmax(0,1fr)]">
          <SectionCard
            title="Tracked keywords"
            icon={<Search1 aria-hidden="true" focusable="false" />}
            actions={<SourceMark source="locus" />}
            bodyClassName="px-3 py-4"
          >
            {keywords.isPending ? <KeywordListSkeleton /> : null}

            {!keywords.isPending && keywords.isError ? (
              <ErrorState
                title="We could not load tracked keywords"
                onRetry={() => void keywords.refetch()}
                isRetrying={keywords.isFetching}
              />
            ) : null}

            {!keywords.isPending && !keywords.isError && visibleKeywords.length === 0 ? (
              <p className="px-2 py-6 text-center text-sm leading-6 text-text-tertiary">
                {allKeywords.length === 0
                  ? `No keywords are tracked for ${locationName ?? "this location"} yet.`
                  : "No tracked keyword has this search intent. Choose another intent to see more."}
              </p>
            ) : null}

            {!keywords.isPending && !keywords.isError && visibleKeywords.length > 0 ? (
              <KeywordList
                keywords={visibleKeywords}
                selectedId={keywordId}
                onSelect={setPickedKeywordId}
                showGroupHeadings={intent === null}
              />
            ) : null}
          </SectionCard>

          <SectionCard
            title={
              selectedKeyword ? `Rank over time — ${selectedKeyword.keyword}` : "Rank over time"
            }
            icon={<TrendUp2 aria-hidden="true" focusable="false" />}
            actions={
              <div className="flex flex-wrap items-center gap-2">
                <SourceMark source="locus" />
                {keywordId ? (
                  <LinkButton
                    href={`/market/competitors?location=${encodeURIComponent(
                      locationId,
                    )}&keyword=${encodeURIComponent(keywordId)}`}
                    appearance="outline"
                    size="lg"
                  >
                    View competitors
                  </LinkButton>
                ) : null}
              </div>
            }
          >
            {!keywordId ? (
              <p className="py-6 text-sm leading-6 text-text-tertiary">
                Select a tracked keyword to see its weekly position.
              </p>
            ) : null}

            {keywordId && rankings.isPending ? <RankChartSkeleton /> : null}

            {keywordId && !rankings.isPending && rankings.isError ? (
              <ErrorState
                title="We could not load this rank history"
                onRetry={() => void rankings.refetch()}
                isRetrying={rankings.isFetching}
              />
            ) : null}

            {keywordId && !rankings.isPending && !rankings.isError && points.length === 0 ? (
              <EmptyState
                icon={<TrendUp2 aria-hidden="true" focusable="false" />}
                title="No weeks recorded yet"
                description={
                  selectedKeyword
                    ? `Locus has not recorded a position for “${selectedKeyword.keyword}” yet. The first reading appears after the next weekly check.`
                    : "Locus has not recorded a position for this keyword yet."
                }
                className="border-0 bg-transparent py-8"
              />
            ) : null}

            {keywordId && !rankings.isPending && !rankings.isError && points.length > 0 ? (
              <div
                aria-busy={rankings.isFetching}
                className={cn(
                  "flex flex-col gap-6 transition-opacity",
                  rankings.isFetching && "opacity-60",
                )}
              >
                <RankSummary points={points} />
                <RankChart points={points} keyword={selectedKeyword?.keyword ?? ""} />

                <div className="border-t border-card-border pt-4">
                  <button
                    type="button"
                    aria-expanded={showTable}
                    onClick={() => setShowTable((open) => !open)}
                    className="flex min-h-11 items-center rounded-lg px-2 text-sm font-medium text-text-secondary underline decoration-border-secondary-alt underline-offset-4 transition outline-none hover:text-text-primary focus-visible:ring-2 focus-visible:ring-primary-500"
                  >
                    {showTable ? "Hide the weekly table" : "Read the weekly table"}
                  </button>
                  {showTable ? (
                    <div className="mt-3">
                      <RankHistoryTable points={points} />
                    </div>
                  ) : null}
                </div>
              </div>
            ) : null}
          </SectionCard>
        </div>
      ) : null}
    </div>
  );
}
