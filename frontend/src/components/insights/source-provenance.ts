import type { DataSource } from "@/services/api/insights";

const SOURCE_PROVENANCE: Record<DataSource, string> = {
  google: "reported by Google",
  locus: "held by Locus",
};

/**
 * Reads inside a sentence: "Figures reported by Google."
 *
 * The visible mark on a section is `SourceMark` in `components/common`; this is the
 * phrasing used in the footnotes that explain a chart.
 */
export function sourceProvenance(source: DataSource) {
  return SOURCE_PROVENANCE[source] ?? `from ${source}`;
}
