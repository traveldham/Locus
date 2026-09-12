import { redirect } from "next/navigation";

/** Insights opens on performance; the other two sections are reached from the tabs. */
export default function InsightsPage() {
  redirect("/insights/performance");
}
