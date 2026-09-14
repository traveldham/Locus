import {
  BarChart2,
  Buildings11,
  ClockThree,
  PenToSquare,
  RefreshCircle1Clockwise,
  Reply,
  Shop,
  StarFat,
} from "@tailgrids/icons";
import type { ComponentType, SVGProps } from "react";

type ToolIconComponent = ComponentType<SVGProps<SVGSVGElement>>;

interface ToolPresentation {
  /** Present tense, for the line shown while the tool is running. */
  active: string;
  /** Past tense, for the chip left behind in the transcript. */
  done: string;
  Icon: ToolIconComponent;
}

/**
 * Human wording for every tool the agent can run. The raw snake_case name is never shown:
 * the transcript should read like a colleague reporting what they did.
 */
const TOOLS: Record<string, ToolPresentation> = {
  get_latest_audit: {
    active: "Checking the latest audit",
    done: "Checked the latest audit",
    Icon: BarChart2,
  },
  start_audit: {
    active: "Running an audit",
    done: "Ran an audit",
    Icon: BarChart2,
  },
  poll_audit_job: {
    active: "Waiting for the audit to finish",
    done: "Checked on the audit",
    Icon: ClockThree,
  },
  list_reviews: {
    active: "Reading reviews",
    done: "Read the reviews",
    Icon: StarFat,
  },
  sync_reviews: {
    active: "Fetching the newest reviews from Google",
    done: "Fetched the newest reviews from Google",
    Icon: RefreshCircle1Clockwise,
  },
  reply_to_review: {
    active: "Replying to a review",
    done: "Replied to a review",
    Icon: Reply,
  },
  get_location_profile: {
    active: "Reading the profile",
    done: "Read the profile",
    Icon: Shop,
  },
  update_location_profile: {
    active: "Updating the profile",
    done: "Updated the profile",
    Icon: PenToSquare,
  },
  list_recent_actions: {
    active: "Checking recent activity",
    done: "Checked recent activity",
    Icon: ClockThree,
  },
  // Only reachable in project scope, where the agent has to find out which locations it
  // is allowed to work on before it can do anything to one of them.
  list_locations: {
    active: "Looking up your locations",
    done: "Looked up your locations",
    Icon: Buildings11,
  },
};

/** "sync_reviews" becomes "Sync reviews", so an unknown tool still reads as English. */
function humanize(name: string) {
  const words = name.replace(/[_-]+/g, " ").trim();
  if (!words) return "Working on it";
  return words.charAt(0).toUpperCase() + words.slice(1);
}

export function toolLabel(name: string | null, state: "active" | "done") {
  if (!name) return state === "active" ? "Thinking" : "Worked on it";
  const tool = TOOLS[name];
  if (tool) return tool[state];
  return humanize(name);
}

export function ToolIcon({
  name,
  className,
}: {
  name: string | null;
  className?: string;
}) {
  const Icon = (name && TOOLS[name]?.Icon) || ClockThree;
  return <Icon className={className} aria-hidden="true" />;
}
