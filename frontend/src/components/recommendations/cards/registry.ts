import type { ComponentType } from "react";
import type {
  AuditLocation,
  Recommendation,
} from "@/services/api/recommendations";
import { ContentCard } from "./content-card";
import { OperationsCard } from "./operations-card";
import { PerformanceCard } from "./performance-card";
import { ReputationCard } from "./reputation-card";
import { VisibilityCard } from "./visibility-card";

/** What a category card receives: that worker's card data and its findings. */
export interface CategoryCardProps {
  card: unknown;
  items: Recommendation[];
  location: AuditLocation;
}

/**
 * One visual per category, registered by key. Profile's before/after card is rendered
 * by the category view itself. Each card lives in `cards/<key>-card.tsx`.
 */
export const CATEGORY_CARDS: Partial<
  Record<string, ComponentType<CategoryCardProps>>
> = {
  reputation: ReputationCard,
  visibility: VisibilityCard,
  operations: OperationsCard,
  performance: PerformanceCard,
  content: ContentCard,
};
