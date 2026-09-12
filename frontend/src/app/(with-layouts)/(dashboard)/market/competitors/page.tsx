import { CompetitorsView } from "@/components/market/competitors-view";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Competitors",
  description:
    "The businesses ranking around you for a tracked keyword, measured by Locus rather than supplied by Google.",
};

/** Reads the first value only; a repeated parameter is a malformed link, not a choice. */
function firstValue(value: string | string[] | undefined) {
  if (Array.isArray(value)) return value[0] ?? null;
  return value ?? null;
}

export default async function CompetitorsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;

  return (
    <CompetitorsView
      initialLocationId={firstValue(params.location)}
      initialKeywordId={firstValue(params.keyword)}
    />
  );
}
