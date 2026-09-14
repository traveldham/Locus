"use client";

import { cn } from "@/utils/cn";
import type { ActivityItem } from "./transcript-blocks";
import { ToolIcon, toolLabel } from "./tool-labels";

export interface AgentActivityProps {
  items: ActivityItem[];
}

/**
 * What the agent did, as a compact run of chips rather than the JSON it actually
 * exchanged. A chip still waiting on its result keeps a quiet pulse.
 *
 * No chip names a location: the conversation is about one, and it is already named above
 * the transcript, so repeating it on every line would be noise.
 */
export function AgentActivity({ items }: AgentActivityProps) {
  return (
    <ul className="flex flex-col items-start gap-1">
      {items.map((item) => (
        <li
          key={item.key}
          className={cn(
            "flex max-w-full items-center gap-1.5 rounded-full border border-card-border bg-background-gray-secondary py-1 pr-3 pl-2 text-xs leading-5 text-text-secondary",
            !item.isDone && "animate-pulse",
          )}
        >
          <ToolIcon
            name={item.name}
            className="size-3.5 shrink-0 text-icon-secondary"
          />
          <span className="truncate">
            {toolLabel(item.name, item.isDone ? "done" : "active")}
          </span>
        </li>
      ))}
    </ul>
  );
}
