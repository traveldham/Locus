import { ProjectDetailView } from "@/components/projects/project-detail-view";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Project",
};

export default async function ProjectDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <ProjectDetailView projectId={id} />;
}
