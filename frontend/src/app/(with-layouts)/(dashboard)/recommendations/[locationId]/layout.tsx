"use client";

import { LocationShell } from "@/components/recommendations/location-shell";
import { useParams } from "next/navigation";
import type { ReactNode } from "react";

export default function LocationAuditLayout({
  children,
}: {
  children: ReactNode;
}) {
  const locationId = String(useParams().locationId ?? "");
  return <LocationShell locationId={locationId}>{children}</LocationShell>;
}
