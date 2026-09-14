import { apiFetch, apiRequest } from "./client";

/** Who produced a message. `tool` rows carry a tool result, never prose for the reader. */
export type AgentMessageRole = "user" | "assistant" | "tool";

/** Lifecycle of one background run of the agent. Only the first two are still moving. */
export type AgentTurnStatus = "pending" | "running" | "succeeded" | "failed";

/**
 * The tools the agent is allowed to run. `current_tool` and `tool_name` are typed as plain
 * strings so a tool added on the server does not break the transcript; this union is what
 * the client knows how to label.
 */
export type AgentToolName =
  | "get_latest_audit"
  | "start_audit"
  | "poll_audit_job"
  | "list_reviews"
  | "sync_reviews"
  | "reply_to_review"
  | "get_location_profile"
  | "update_location_profile"
  | "list_recent_actions"
  | "list_locations";

/** One tool the assistant decided to run, with the arguments it chose. */
export interface AgentToolCall {
  id: string;
  name: string;
  args: Record<string, unknown>;
}

export interface AgentMessage {
  id: string;
  role: AgentMessageRole;
  /** Null on the rows that only carry tool calls. */
  content: string | null;
  /** Present on assistant rows that ran tools; null everywhere else. */
  tool_calls: AgentToolCall[] | null;
  /** On a `tool` row, the id of the call it answers. */
  tool_call_id: string | null;
  tool_name: string | null;
  created_at: string;
}

export interface ConversationSummary {
  id: string;
  /** Every conversation is about exactly one location. */
  location_id: string;
  /** The server names a conversation from its first exchange; null until then. */
  title: string | null;
  created_at: string;
}

export interface ConversationDetail extends ConversationSummary {
  /** Oldest first, and written incrementally while a turn runs. */
  messages: AgentMessage[];
  /**
   * The turn still `pending` or `running`, or null when the agent is idle. This is how a
   * reader who reloaded mid-answer finds the run that is already in flight: the same
   * shape `GET /agent/turns/{id}` returns, so it feeds the poll directly.
   */
  active_turn: TurnResponse | null;
}

/** One background run. `POST .../messages` answers with it before the agent has worked. */
export interface TurnResponse {
  id: string;
  conversation_id: string;
  status: AgentTurnStatus;
  /** The tool running right now, while the status is `running`. */
  current_tool: string | null;
  /** Set only when the status is `failed`. */
  error: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

/** Statuses the client keeps polling. Anything else is final. */
export const AGENT_ACTIVE_TURN_STATUSES: AgentTurnStatus[] = [
  "pending",
  "running",
];

/** Every status the wire can carry, for checking one that arrived over the stream. */
const AGENT_TURN_STATUSES: AgentTurnStatus[] = [
  "pending",
  "running",
  "succeeded",
  "failed",
];

/**
 * A client-side stop on runaway pastes. The API publishes no limit, so this is generous
 * and only exists to keep an accidental multi-megabyte paste out of a request.
 */
export const AGENT_MESSAGE_MAX_LENGTH = 4000;

export interface SendAgentMessageInput {
  conversationId: string;
  content: string;
}

function conversationPath(id: string) {
  return `/agent/conversations/${encodeURIComponent(id)}`;
}

export const agentApi = {
  /** Starts an empty conversation about one location. */
  createConversation: (locationId: string) =>
    apiRequest<ConversationSummary>("/agent/conversations", {
      method: "POST",
      body: JSON.stringify({ location_id: locationId }),
    }),
  listConversations: (locationId: string) =>
    apiRequest<ConversationSummary[]>(
      `/agent/conversations?${new URLSearchParams({ location_id: locationId })}`,
    ),
  getConversation: (id: string) =>
    apiRequest<ConversationDetail>(conversationPath(id)),
  /**
   * Queues the agent. The reply describes the queued run, not the answer: read the
   * answer by polling the turn and re-reading the conversation.
   */
  sendMessage: ({ conversationId, content }: SendAgentMessageInput) =>
    apiRequest<TurnResponse>(`${conversationPath(conversationId)}/messages`, {
      method: "POST",
      body: JSON.stringify({ content }),
    }),
  getTurn: (id: string) =>
    apiRequest<TurnResponse>(`/agent/turns/${encodeURIComponent(id)}`),
  streamTurn,
};

/* ------------------------------------------------------------------ *
 * Streaming one turn
 * ------------------------------------------------------------------ */

/**
 * How long the reader will sit in silence before it decides the connection is dead.
 *
 * The server sends a `: ping` comment about every fifteen seconds, so silence longer than
 * this means something between here and there has stopped forwarding without closing the
 * socket — a proxy that buffered the response, a laptop that slept, a connection a mobile
 * network dropped without a FIN. A stream in that state looks healthy forever, which is the
 * one failure the poll behind it could not otherwise notice. Three missed heartbeats.
 */
const STREAM_IDLE_TIMEOUT_MS = 45_000;

/** A delta to append to the reply being written. */
export interface AgentTokenEvent {
  text: string;
}

/** The agent's progress, mirroring the fields the turn poll would have reported. */
export interface AgentStatusEvent {
  status: AgentTurnStatus;
  current_tool: string | null;
}

/** The last event of a healthy stream. Anything after it is ignored. */
export interface AgentDoneEvent {
  status: "succeeded" | "failed";
  error: string | null;
}

export interface AgentStreamHandlers {
  onToken: (event: AgentTokenEvent) => void;
  /** A row the server has written down, delivered ahead of the transcript refetch. */
  onMessage: (message: AgentMessage) => void;
  onStatus: (event: AgentStatusEvent) => void;
  onDone: (event: AgentDoneEvent) => void;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function optionalString(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

/**
 * One decoded frame, as the event-stream format defines it.
 *
 * Only the two fields this contract uses are read. `id` and `retry` are part of the format
 * but mean nothing here: there is no resumption to sequence and no reconnection to pace.
 */
interface StreamFrame {
  event: string;
  data: string;
}

/**
 * A single `event:`/`data:` block, already separated from its neighbours.
 *
 * Comment lines — the `: ping` heartbeats among them — carry no field and are skipped, as
 * is a frame that turns out to hold nothing but comments. One space after the colon belongs
 * to the wire format rather than to the value, and repeated `data:` lines are one payload
 * split across lines, joined back with the newlines that separated them.
 */
function parseFrame(block: string): StreamFrame | null {
  let event = "message";
  const data: string[] = [];

  for (const line of block.split("\n")) {
    if (line === "" || line.startsWith(":")) continue;
    const colon = line.indexOf(":");
    const field = colon === -1 ? line : line.slice(0, colon);
    let value = colon === -1 ? "" : line.slice(colon + 1);
    if (value.startsWith(" ")) value = value.slice(1);
    if (field === "event") event = value;
    else if (field === "data") data.push(value);
  }

  return data.length === 0 ? null : { event, data: data.join("\n") };
}

/** Hands one frame to the matching handler, or drops it. */
function dispatchFrame(frame: StreamFrame, handlers: AgentStreamHandlers) {
  let payload: unknown;
  try {
    payload = JSON.parse(frame.data);
  } catch {
    // A frame that is not JSON is one frame lost, never the whole stream: the turn is
    // still running and the next frame may well be fine.
    return;
  }
  if (!isRecord(payload)) return;

  switch (frame.event) {
    case "token": {
      if (typeof payload.text === "string")
        handlers.onToken({ text: payload.text });
      return;
    }
    case "message": {
      // The one place a wire value becomes a transcript row, so the fields the transcript
      // keys and groups by are checked rather than assumed.
      if (
        typeof payload.id !== "string" ||
        (payload.role !== "user" &&
          payload.role !== "assistant" &&
          payload.role !== "tool")
      ) {
        return;
      }
      handlers.onMessage({
        id: payload.id,
        role: payload.role,
        content: optionalString(payload.content),
        tool_calls: Array.isArray(payload.tool_calls)
          ? (payload.tool_calls as AgentToolCall[])
          : null,
        tool_call_id: optionalString(payload.tool_call_id),
        tool_name: optionalString(payload.tool_name),
        created_at:
          optionalString(payload.created_at) ?? new Date().toISOString(),
      });
      return;
    }
    case "status": {
      // The first frame of every stream, describing the turn as it stood when the
      // connection opened — so this is also how a turn adopted after a reload learns which
      // tool it is in the middle of, without waiting for the next one to start.
      if (!AGENT_TURN_STATUSES.includes(payload.status as AgentTurnStatus))
        return;
      handlers.onStatus({
        status: payload.status as AgentTurnStatus,
        current_tool: optionalString(payload.current_tool),
      });
      return;
    }
    case "done": {
      const status = payload.status === "failed" ? "failed" : "succeeded";
      handlers.onDone({ status, error: optionalString(payload.error) });
      return;
    }
    default:
      // An event the server learns to send before this client learns to read it.
      return;
  }
}

/**
 * Follows one turn over server-sent events until it finishes.
 *
 * Resolves only after a `done` frame has been delivered. Every other way out — a stream
 * that will not open, a body that ends early, a socket that goes quiet, a request the
 * caller aborted — rejects, and the caller is expected to answer that by falling back to
 * the turn poll. Nothing here retries: the contract offers no way to resume from where a
 * broken stream stopped, so a second attempt would replay tokens the reader already has.
 *
 * The clearest of those exits is the one the server states outright: a `503` means live
 * updates are not available at all — the endpoint says so rather than leaving a socket to
 * die — and `apiFetch` turns it into an `ApiError` before a single frame is read. It needs
 * no special case here precisely because it arrives as a rejection like the rest, which is
 * already the signal to go back to polling.
 *
 * Two shapes of stream are normal and both are handled by the loop below without a branch:
 * a run in flight opens with a `status` frame and then works, and a turn that finished
 * before the connection was made sends `done` on its own and closes.
 *
 * The parse is incremental because it has to be. A chunk off the socket is whatever the
 * network chose to deliver: it can carry three frames, or half of one, or split a
 * multi-byte character down the middle. So the decoder is told the text is streaming, the
 * buffer keeps whatever is left over after the last blank line, and frames are only cut at
 * a blank line — which is the one thing the format promises separates them.
 */
async function streamTurn(
  turnId: string,
  handlers: AgentStreamHandlers,
  signal: AbortSignal,
): Promise<void> {
  const response = await apiFetch(
    `/agent/turns/${encodeURIComponent(turnId)}/stream`,
    {
      headers: { Accept: "text/event-stream" },
      // A stream replayed from a cache is not a stream, and there is nothing here worth
      // keeping once it has been read.
      cache: "no-store",
      signal,
    },
  );

  if (!response.body) {
    throw new Error("The assistant's stream could not be read.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let isDone = false;

  // Cancelling the reader makes the pending `read()` settle, which drops out of the loop
  // below without a `done` frame — exactly the way any other broken stream ends.
  let idleTimer: ReturnType<typeof setTimeout> | undefined;
  const armIdle = () => {
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => {
      void reader.cancel().catch(() => undefined);
    }, STREAM_IDLE_TIMEOUT_MS);
  };

  try {
    while (!isDone) {
      armIdle();
      const chunk = await reader.read();
      clearTimeout(idleTimer);
      if (chunk.done) break;

      // Carriage returns are normalised across the whole buffer rather than per chunk, so
      // a `\r\n` split between two reads cannot be mistaken for a frame boundary.
      buffer = (buffer + decoder.decode(chunk.value, { stream: true })).replace(
        /\r\n?/g,
        "\n",
      );

      let boundary = buffer.indexOf("\n\n");
      while (boundary !== -1) {
        const frame = parseFrame(buffer.slice(0, boundary));
        buffer = buffer.slice(boundary + 2);
        if (frame) {
          dispatchFrame(frame, handlers);
          if (frame.event === "done") {
            isDone = true;
            break;
          }
        }
        boundary = buffer.indexOf("\n\n");
      }
    }
  } finally {
    clearTimeout(idleTimer);
    // Releases the socket whether the turn finished, the caller walked away, or the
    // connection died mid-answer.
    await reader.cancel().catch(() => undefined);
  }

  if (!isDone) {
    throw new Error("The assistant's stream ended before the answer did.");
  }
}
