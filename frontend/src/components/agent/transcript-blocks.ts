import type { AgentMessage } from "@/services/api/agent";

export interface ActivityItem {
  /**
   * A React key, not a tool-call id. `tool_calls` is typed loosely on the wire, so a call
   * that arrives without an id falls back to its position in the message.
   */
  key: string;
  name: string;
  /** True once the server has written the result of this call. */
  isDone: boolean;
}

export type TranscriptBlock =
  | {
      kind: "message";
      id: string;
      role: "user" | "assistant";
      content: string;
    }
  | { kind: "activity"; id: string; items: ActivityItem[] };

/**
 * Turns the raw message rows into what a reader should see.
 *
 * Tool calls and tool results are the agent's plumbing: shown as raw rows they read like a
 * debug log. Each call becomes one short chip instead, and the result row that answers it
 * only marks that chip as finished. Consecutive chips collapse into a single run.
 */
export function buildTranscript(messages: AgentMessage[]): TranscriptBlock[] {
  const calledIds = new Set<string>();
  for (const message of messages) {
    for (const call of message.tool_calls ?? []) {
      if (call?.id) calledIds.add(call.id);
    }
  }

  const answeredIds = new Set<string>();
  for (const message of messages) {
    if (message.role === "tool" && message.tool_call_id) {
      answeredIds.add(message.tool_call_id);
    }
  }

  const blocks: TranscriptBlock[] = [];

  function appendActivity(id: string, items: ActivityItem[]) {
    if (items.length === 0) return;
    const last = blocks[blocks.length - 1];
    if (last && last.kind === "activity") last.items.push(...items);
    else blocks.push({ kind: "activity", id, items });
  }

  for (const message of messages) {
    if (message.role === "tool") {
      // Normally the chip already exists from the call that produced this row. A result
      // with no matching call still deserves a chip rather than silently vanishing.
      if (!message.tool_call_id || !calledIds.has(message.tool_call_id)) {
        appendActivity(`${message.id}-activity`, [
          {
            key: `${message.id}-result`,
            name: message.tool_name ?? "",
            isDone: true,
          },
        ]);
      }
      continue;
    }

    const text = message.content?.trim();
    if (text) {
      blocks.push({
        kind: "message",
        id: message.id,
        role: message.role === "user" ? "user" : "assistant",
        content: text,
      });
    }

    appendActivity(
      `${message.id}-activity`,
      (message.tool_calls ?? []).map((call, index) => ({
        key: call?.id ?? `${message.id}-${index}`,
        name: call?.name ?? "",
        // A call with no id can never be matched to its result, so it is shown as done
        // rather than left pulsing forever.
        isDone: call?.id ? answeredIds.has(call.id) : true,
      })),
    );
  }

  return blocks;
}
