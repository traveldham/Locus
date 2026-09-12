import { ProjectsView } from "@/components/projects/projects-view";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Projects",
  description: "Named sets of the business locations your organization manages on Google.",
};

export default function ProjectsPage() {
  return <ProjectsView />;
}
