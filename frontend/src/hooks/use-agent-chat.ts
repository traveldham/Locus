"use client";

import {
  agentApi,
  type AgentMessage,
  type AgentTurnStatus,
  type ConversationSummary,
  type TurnResponse,
} from "@/services/api/agent";
import { ApiError } from "@/services/api/client";
import {
  LOCATIONS_MAX_PAGE_SIZE,
  locationsApi,
  type LocationListParams,
  type LocationSummary,
} from "@/services/api/locations";
import {
  useMutation,
  useQuery,
  useQueryClient,
  type QueryClient,
} from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";
import { locationKeys } from "./use-locations";

export const agentKeys = {
  all: ["agent"] as const,
  conversationLists: () => [...agentKeys.all, "conversations"] as const,
  /** One list per location: a conversation belongs to exactly one. */
  conversations: (locationId: string) =>
    [...agentKeys.conversationLists(), locationId] as const,
  conversation: (id: string) => [...agentKeys.all, "conversation", id] as const,
  turn: (id: string) => [...agentKeys.all, "turn", id] as const,
};

/** Where the widget remembers which location it was last talking about. */
const LOCATION_STORAGE_KEY = "locus.agent-location";

function readStoredChoice(): string | null {
  try {
    return window.localStorage.getItem(LOCATION_STORAGE_KEY);
  } catch {
    // Private windows and blocked site data are fine; the default choice is used.
    return null;
  }
}

function rememberChoice(value: string) {
  try {
    window.localStorage.setItem(LOCATION_STORAGE_KEY, value);
  } catch {
    // Non-fatal: the choice simply does not survive a reload.
  }
}

/**
 * The locations of the active project, which is what the rest of the dashboard is scoped
 * to. Offering the whole organization would mean offering profiles the reader has not
 * imported into the project they are looking at, which reads as a bug even though every
 * one of them is theirs.
 *
 * The key matches the other project-scoped location lists, so this shares their cache
 * entry; it only adds the gate that keeps the request from firing on every page for
 * someone who never opens the widget.
 */
function agentLocationParams(projectId: string | null): LocationListParams {
  return {
    limit: LOCATIONS_MAX_PAGE_SIZE,
    projectId: projectId ?? undefined,
  };
}

export function useAgentLocationsQuery(
  projectId: string | null,
  enabled: boolean,
) {
  const params = agentLocationParams(projectId);
  return useQuery({
    queryKey: locationKeys.list(params),
    queryFn: () => locationsApi.list(params),
    enabled,
    retry: 1,
    staleTime: 30_000,
  });
}

export interface AgentLocationChoice {
  /** The chosen location's id, and the picker's value. Null with nothing to talk about. */
  locationId: string | null;
  /** The chosen location itself, for naming it in the panel. */
  location: LocationSummary | null;
  setValue: (value: string) => void;
}

/**
 * Which location the widget is talking about.
 *
 * Deliberately not read from the URL: the widget is on every page, including the ones that
 * name no location. The remembered choice is only honoured while it is still on offer, so
 * anything else - a location dropped from the project, a switch to a project that does not
 * contain it, or the "all" that older builds of this widget used to store - is treated the
 * same way, as nothing valid remembered, and falls back to the first location in the list
 * rather than leaving the picker pointing at something that is not there.
 *
 * A project with no locations in it, and one whose locations have not arrived yet, both
 * leave this with nothing: an agent with no profile to read has nothing to answer with, and
 * the panel says so rather than taking the message.
 */
export function useAgentLocationChoice(
  locations: LocationSummary[],
): AgentLocationChoice {
  const [chosen, setChosen] = useState<string | null>(() =>
    typeof window === "undefined" ? null : readStoredChoice(),
  );

  const isKnown = locations.some((location) => location.id === chosen);
  const locationId = isKnown ? chosen : (locations[0]?.id ?? null);
  const location =
    locations.find((candidate) => candidate.id === locationId) ?? null;

  return {
    locationId,
    location,
    setValue: (next: string) => {
      rememberChoice(next);
      setChosen(next);
    },
  };
}

/** The two statuses that mean the agent is still working. */
function isActiveStatus(status: AgentTurnStatus | undefined): boolean {
  return status === "pending" || status === "running";
}

/**
 * Both polls give up after this many consecutive failures. Without a cap a poll whose
 * endpoint has started failing keeps firing forever off its last good payload, and the
 * composer stays disabled the whole time. Giving up surfaces an error the reader can act
 * on instead.
 */
const MAX_POLL_FAILURES = 5;

/** Newest first, so the widget always reopens on the most recent conversation. */
function newestConversation(
  conversations: ConversationSummary[] | undefined,
): ConversationSummary | null {
  if (!conversations || conversations.length === 0) return null;
  return [...conversations].sort((a, b) =>
    b.created_at.localeCompare(a.created_at),
  )[0];
}

export function useAgentConversationsQuery(
  locationId: string | null,
  enabled: boolean,
) {
  return useQuery({
    queryKey: agentKeys.conversations(locationId ?? ""),
    queryFn: () => agentApi.listConversations(locationId as string),
    enabled: enabled && Boolean(locationId),
    staleTime: 30_000,
    retry: 1,
  });
}

/**
 * One transcript. The agent writes its messages as it works, so while a turn is moving
 * the transcript is re-read on a short interval and the reply appears in pieces.
 *
 * The interval is driven by the transcript's own `active_turn` rather than by the turn
 * poll, which keeps the two queries from depending on each other: this one is what tells
 * the rest of the hook that there is a turn to poll at all. `isSending` only covers the
 * moment between pressing send and the first read that knows about the new turn.
 *
 * While the stream is delivering, the same rows arrive as `message` events the moment they
 * are written, so the interval stands down. The query itself stays exactly where it was:
 * `isStreaming` going false — for any of the several reasons a stream can die — brings the
 * interval straight back at the cadence it always used.
 */
export function useAgentConversationQuery(
  conversationId: string | null,
  {
    enabled,
    isSending,
    isPanelOpen,
    isStreaming,
  }: {
    enabled: boolean;
    isSending: boolean;
    isPanelOpen: boolean;
    isStreaming: boolean;
  },
) {
  return useQuery({
    queryKey: agentKeys.conversation(conversationId ?? ""),
    queryFn: () => agentApi.getConversation(conversationId as string),
    enabled: enabled && Boolean(conversationId),
    staleTime: 0,
    refetchInterval: (q) => {
      // Stop rather than hammer a failing endpoint off the last good payload.
      if (q.state.fetchFailureCount >= MAX_POLL_FAILURES) return false;
      const isActive = isActiveStatus(q.state.data?.active_turn?.status);
      if (!isActive && !isSending) return false;
      // Collapsed, the widget still follows a run in flight so the launcher can show it,
      // but nothing else: an `active_turn` that never settles cannot poll unseen forever.
      if (!isPanelOpen && !isActive) return false;
      if (isStreaming) return false;
      // Offset from the turn poll so the two do not fire in lockstep.
      return 2_500;
    },
    retry: 1,
  });
}

/**
 * Polls one background run while it works, then refreshes the transcript once it lands.
 *
 * Mirrors the audit job poll: the interval stops itself on a terminal status, and the
 * refresh is published from an effect rather than the query function so invalidating the
 * transcript cannot loop back into this query.
 *
 * The stream stands the interval down but never the query. The first read still happens,
 * on purpose: it puts a real `TurnResponse` in the cache for the stream's `status` and
 * `done` events to amend, so the composer and the launcher dot follow the stream without
 * another round trip. After that the interval only comes back if the stream stops.
 */
export function useAgentTurnQuery(
  turnId: string | null,
  { isStreaming }: { isStreaming: boolean } = { isStreaming: false },
) {
  const client = useQueryClient();
  const published = useRef<string | null>(null);

  const query = useQuery({
    queryKey: agentKeys.turn(turnId ?? ""),
    queryFn: () => agentApi.getTurn(turnId as string),
    enabled: Boolean(turnId),
    refetchInterval: (q) => {
      const status = q.state.data?.status;
      if (status === "succeeded" || status === "failed") return false;
      // A turn endpoint that keeps failing is reported, not retried indefinitely.
      if (q.state.fetchFailureCount >= MAX_POLL_FAILURES) return false;
      if (isStreaming) return false;
      return q.state.status === "error" ? 5_000 : 2_000;
    },
    staleTime: 0,
    retry: 1,
  });

  const status = query.data?.status;
  const conversationId = query.data?.conversation_id;

  useEffect(() => {
    if (!turnId || (status !== "succeeded" && status !== "failed")) return;
    if (published.current === turnId) return;
    published.current = turnId;
    if (conversationId) {
      void client.invalidateQueries({
        queryKey: agentKeys.conversation(conversationId),
      });
    }
    void client.invalidateQueries({ queryKey: agentKeys.conversationLists() });
  }, [client, turnId, status, conversationId]);

  return query;
}

/**
 * Amends the cached turn in place.
 *
 * The stream reports the same two things the turn poll would have — which tool is running,
 * and how the run ended — so writing them where the poll writes them means the status line,
 * the disabled composer, the failure notice and the dot on the collapsed launcher keep
 * reading from exactly one place and cannot disagree about whether the agent is busy.
 *
 * A turn with nothing cached yet is left alone rather than invented: there is no honest
 * value for the fields a `status` frame does not carry. That case resolves itself, because
 * the stream going quiet is what lets the poll's interval start again.
 */
function patchCachedTurn(
  client: QueryClient,
  turnId: string,
  patch: Partial<TurnResponse>,
) {
  client.setQueryData<TurnResponse>(agentKeys.turn(turnId), (cached) =>
    cached ? { ...cached, ...patch } : cached,
  );
}

/** What the widget can see of a stream in flight. */
interface AgentStream {
  /** True only while frames are actually arriving. The polls stand down on this. */
  isLive: boolean;
  /** Reply text delivered ahead of the server writing it down; "" when there is none. */
  partialText: string;
  /** Rows the stream delivered, ahead of the transcript being re-read. */
  messages: AgentMessage[];
}

/** Held against the turn it belongs to, so a scope switch cannot show the wrong reply. */
interface StreamState extends AgentStream {
  turnId: string | null;
}

const IDLE_STREAM: StreamState = {
  turnId: null,
  isLive: false,
  partialText: "",
  messages: [],
};

const NO_MESSAGES: AgentMessage[] = [];

/**
 * Follows one turn over server-sent events, with the poll still behind it.
 *
 * The stream is an enhancement, not a replacement: it delivers the same rows the transcript
 * poll would have delivered, only sooner, plus the token deltas that make a reply appear as
 * it is written. So every failure here is quiet. A stream that will not open, one a proxy
 * kills mid-answer, one that goes silent — all of them end the same way, with `isLive`
 * false, which is the signal both polls watch to start again. The reader still gets their
 * answer; it simply arrives in one piece instead of in words.
 *
 * One attempt per turn, deliberately. The contract has no cursor and no `Last-Event-ID`
 * handling, so a reopened stream would start from the beginning and repeat text already on
 * screen. Reconnecting is the poll's job, and the poll is the part that has been proven.
 *
 * `done` does not end the story. What the stream delivered is early delivery, not the
 * record: the transcript is re-read so the bubbles on screen are the rows the database
 * actually holds.
 */
function useAgentTurnStream({
  turnId,
  conversationIdRef,
  enabled,
}: {
  turnId: string | null;
  /** Read when `done` lands rather than captured, since it is known after this runs. */
  conversationIdRef: { current: string | null };
  enabled: boolean;
}): AgentStream {
  const client = useQueryClient();
  const [state, setState] = useState<StreamState>(IDLE_STREAM);
  // Turns whose stream has already been opened and lost. Survives the re-renders that
  // adopting a turn causes, and is what stops a stream that died from being reopened.
  const attempted = useRef(new Set<string>());

  useEffect(() => {
    // Read once here so the cleanup below closes over the set itself. The ref is never
    // reassigned, so this is the same set either way; the lint rule cannot know that.
    const alreadyAttempted = attempted.current;
    if (!enabled || !turnId || alreadyAttempted.has(turnId)) return;
    alreadyAttempted.add(turnId);

    const controller = new AbortController();
    setState({ turnId, isLive: true, partialText: "", messages: [] });

    // Frames can land after the widget has moved on to another turn or another scope.
    // Anything that is no longer the turn being followed is dropped rather than merged.
    const update = (next: (previous: StreamState) => StreamState) => {
      setState((previous) =>
        previous.turnId === turnId ? next(previous) : previous,
      );
    };

    void agentApi
      .streamTurn(
        turnId,
        {
          onToken: ({ text }) =>
            update((previous) => ({
              ...previous,
              partialText: previous.partialText + text,
            })),

          onMessage: (message) =>
            update((previous) => ({
              ...previous,
              // The row that just arrived is the finished form of whatever was being
              // typed above it, so the partial bubble is retired in the same render that
              // the real one appears. Nothing blinks, because nothing is ever absent.
              partialText: "",
              messages: previous.messages.some(
                (existing) => existing.id === message.id,
              )
                ? previous.messages
                : [...previous.messages, message],
            })),

          onStatus: ({ status, current_tool }) =>
            patchCachedTurn(client, turnId, { status, current_tool }),

          onDone: ({ status, error }) => {
            patchCachedTurn(client, turnId, {
              status,
              error,
              current_tool: null,
            });
            // The database is the source of truth and the stream was only early delivery.
            // `useAgentTurnQuery` publishes the same refresh off the terminal status this
            // just wrote; both are guarded, and a duplicate refetch is deduplicated.
            const conversationId = conversationIdRef.current;
            if (conversationId) {
              void client.invalidateQueries({
                queryKey: agentKeys.conversation(conversationId),
              });
            }
            void client.invalidateQueries({
              queryKey: agentKeys.conversationLists(),
            });
          },
        },
        controller.signal,
      )
      .catch(() => {
        // Every failure is the same failure, and none of them is worth a notice: the poll
        // takes over from here and the reader is told nothing they could act on.
      })
      .finally(() => {
        // An abort is this effect being cleaned up, which means the turn or the scope has
        // already changed. Writing to state for a turn nobody is following would only
        // undo the reset the next run just did.
        if (controller.signal.aborted) return;
        update((previous) => ({ ...previous, isLive: false }));
      });

    return () => {
      controller.abort();
      // Tearing this effect down is not the stream failing, so it does not count as the
      // one attempt. Without this the double-invoked effect React runs in development
      // would spend the attempt on a connection it immediately aborts, and the widget
      // would silently poll for the whole of every turn there.
      alreadyAttempted.delete(turnId);
    };
  }, [client, conversationIdRef, enabled, turnId]);

  // Derived rather than cleared from an effect, so the moment the widget is following a
  // different turn - or none - nothing of the last one is on screen or holding the polls
  // down, without waiting a render for a reset to take effect.
  const isCurrent = state.turnId !== null && state.turnId === turnId;
  return {
    isLive: isCurrent && state.isLive,
    partialText: isCurrent ? state.partialText : "",
    messages: isCurrent ? state.messages : NO_MESSAGES,
  };
}

interface SendInput {
  locationId: string;
  /** Null on the first message for a location: the conversation is created first. */
  conversationId: string | null;
  content: string;
}

/** Creates the conversation when there is not one yet, then queues the turn. */
export function useSendAgentMessageMutation() {
  const client = useQueryClient();

  return useMutation({
    mutationFn: async ({ locationId, conversationId, content }: SendInput) => {
      const id =
        conversationId ?? (await agentApi.createConversation(locationId)).id;
      return agentApi.sendMessage({ conversationId: id, content });
    },
    onSuccess: (turn: TurnResponse, variables: SendInput) => {
      // Seed the poll with the turn the POST just described. Without this the turn query
      // has no data until its first round trip, `isBusy` is briefly false, and a second
      // Enter lands on a 409 that records nothing.
      client.setQueryData(agentKeys.turn(turn.id), turn);
      void client.invalidateQueries({
        queryKey: agentKeys.conversations(variables.locationId),
      });
      void client.invalidateQueries({
        queryKey: agentKeys.conversation(turn.conversation_id),
      });
    },
    onError: (error: Error, variables: SendInput) => {
      // A 409 means a turn is already running that this client does not know about —
      // typically a POST whose response was lost. The transcript carries `active_turn`,
      // so re-reading it reattaches the poll instead of leaving the reader to retry into
      // the same conflict forever.
      if (!(error instanceof ApiError) || error.status !== 409) return;
      if (variables.conversationId) {
        void client.invalidateQueries({
          queryKey: agentKeys.conversation(variables.conversationId),
        });
      }
      void client.invalidateQueries({
        queryKey: agentKeys.conversations(variables.locationId),
      });
    },
  });
}

/** One turn, remembered against the location it belongs to. */
interface TurnRef {
  locationId: string;
  id: string;
}

/** The message the person just sent, shown before the server has written it down. */
interface PendingMessage {
  locationId: string;
  content: string;
  /** How many identical messages the transcript already held when this was sent. */
  priorCount: number;
}

export interface AgentChat {
  messages: AgentMessage[];
  /** The just-sent message, or null once it appears in the transcript. */
  pendingMessage: string | null;
  /**
   * The reply as it is being written, before the server has written it down. Null unless a
   * stream is live and has delivered text the transcript does not hold yet.
   */
  streamingText: string | null;
  turn: TurnResponse | null;
  /** True from the moment send is pressed until the turn reaches a terminal status. */
  isBusy: boolean;
  /** True while the transcript is being read for the first time. */
  isLoading: boolean;
  /**
   * False until it is known which conversation a message belongs in. Sending before then
   * would start a second conversation and strand the first, which has no history UI to
   * get back to.
   */
  isReady: boolean;
  /** A send that never reached the server, as opposed to a turn that failed. */
  sendError: Error | null;
  loadError: Error | null;
  /** A poll that gave up while a run was supposedly still going. */
  pollError: Error | null;
  /** Resolves true only once the server has accepted the message. */
  send: (content: string) => Promise<boolean>;
  retryLoad: () => void;
  /** The way out of a run that never settles, and of a conversation gone wrong. */
  startNewChat: () => void;
  canStartNewChat: boolean;
  isStartingNewChat: boolean;
}

/**
 * Everything the chat panel needs for one location: the transcript, the run in flight, and
 * the one way to send. Nothing here reads the URL.
 */
export function useAgentChat({
  locationId,
  enabled,
  isPanelOpen,
}: {
  locationId: string | null;
  enabled: boolean;
  isPanelOpen: boolean;
}): AgentChat {
  const client = useQueryClient();
  // The one run this hook is following. Set either by sending from this tab or by
  // adopting a run the server reports as already in flight, and kept after it finishes so
  // its outcome stays on screen. Held against a location so switching the picker never
  // shows another conversation's run.
  const [trackedTurn, setTrackedTurn] = useState<TurnRef | null>(null);
  const [pending, setPending] = useState<PendingMessage | null>(null);
  // The conversation this tab just created, known before the list query catches up.
  const [started, setStarted] = useState<TurnRef | null>(null);
  // Held against its location, so a failure in one conversation does not surface under
  // another after the picker moves.
  const [sendFailure, setSendFailure] = useState<{
    locationId: string;
    error: Error;
  } | null>(null);

  // Resolved before the queries below, because it is what decides whether they poll at all.
  // One render behind while a turn is being adopted, which costs nothing: the adoption
  // re-renders immediately and the stream is opened from an effect, after the commit.
  const turnId =
    trackedTurn && trackedTurn.locationId === locationId
      ? trackedTurn.id
      : null;

  // Which conversation to refresh once the stream says the turn is done. A ref because
  // that is known further down this function and read long after this render, from a
  // callback the stream keeps for the life of the connection.
  const conversationIdRef = useRef<string | null>(null);
  const stream = useAgentTurnStream({ turnId, conversationIdRef, enabled });

  const send = useSendAgentMessageMutation();
  const conversations = useAgentConversationsQuery(locationId, enabled);

  const conversationId =
    (started && started.locationId === locationId ? started.id : null) ??
    newestConversation(conversations.data)?.id ??
    null;
  // Published after the commit rather than during render. The stream only reads this when
  // a turn finishes, which is always later than the effect that records it.
  useEffect(() => {
    conversationIdRef.current = conversationId;
  }, [conversationId]);

  const conversation = useAgentConversationQuery(conversationId, {
    enabled,
    isSending: send.isPending,
    isPanelOpen,
    isStreaming: stream.isLive,
  });

  // Starting a fresh conversation: the escape hatch from a run that never settles, and
  // from a transcript the reader wants to leave behind.
  const newChat = useMutation({
    mutationFn: (next: string) => agentApi.createConversation(next),
    // Keyed off what was asked for rather than what came back: the request already names
    // the location, so the widget does not depend on the server echoing it.
    onSuccess: (created: ConversationSummary, requested: string) => {
      setStarted({ locationId: requested, id: created.id });
      setTrackedTurn(null);
      setPending(null);
      setSendFailure(null);
      void client.invalidateQueries({
        queryKey: agentKeys.conversations(requested),
      });
    },
  });
  const persisted = conversation.data?.messages ?? NO_MESSAGES;

  /**
   * The transcript, plus anything the stream has delivered that has not come back from the
   * server yet.
   *
   * This is what makes a streamed reply settle without a blink. The rows the stream hands
   * over are the persisted rows — same ids, same text — so when the refetch after `done`
   * arrives it matches what is already on screen and the merge quietly stops adding
   * anything. Nothing is removed and re-added, so nothing flickers, and the tool chips a
   * long turn produces appear as the agent runs them rather than on the next poll.
   */
  const messages = useMemo(() => {
    if (stream.messages.length === 0) return persisted;
    const known = new Set(persisted.map((message) => message.id));
    const extra = stream.messages.filter((message) => !known.has(message.id));
    return extra.length === 0 ? persisted : [...persisted, ...extra];
  }, [persisted, stream.messages]);

  // What the server says is running right now, independent of anything this tab started.
  const serverTurn = conversation.data?.active_turn ?? null;
  const serverTurnId =
    serverTurn && isActiveStatus(serverTurn.status) ? serverTurn.id : null;

  // Adopting a run that was already going: a reload mid-answer, or a turn started in
  // another tab. Adjusted during render rather than from an effect, so the poll attaches
  // on the very first read instead of a frame late; it converges immediately, because
  // once the tracked id matches the branch is dead.
  //
  // Three things keep this from disturbing a finished run: only a pending-or-running turn
  // is ever adopted, an id already tracked is never re-adopted, and the server stops
  // reporting a turn the moment it settles — so a completed turn can neither be reopened
  // nor fire the terminal effect in `useAgentTurnQuery` twice.
  if (locationId && serverTurnId && trackedTurn?.id !== serverTurnId) {
    setTrackedTurn({ locationId, id: serverTurnId });
  }

  const turnQuery = useAgentTurnQuery(turnId, { isStreaming: stream.isLive });
  // Before the first poll answers, the transcript's copy already describes the run, so
  // the status line and the disabled composer are right from the first paint.
  const turn = turnQuery.data ?? serverTurn;
  const isTurnActive = isActiveStatus(turn?.status);
  const isBusy = send.isPending || isTurnActive;

  // Which conversation a message belongs in is only known once the list has answered.
  const isReady = Boolean(locationId) && conversations.isSuccess;

  // A poll that has given up while the agent is supposedly still working: the composer
  // would otherwise stay disabled with nothing on screen explaining why. Reported only
  // once the retries are exhausted, so a single dropped request stays invisible.
  const hasGivenUp =
    turnQuery.failureCount >= MAX_POLL_FAILURES ||
    conversation.failureCount >= MAX_POLL_FAILURES;
  const pollError =
    isTurnActive && hasGivenUp
      ? (turnQuery.error ?? conversation.error ?? null)
      : null;

  // Derived rather than cleared from an effect: the optimistic bubble disappears the
  // moment the same message comes back from the server.
  const pendingHere =
    pending && pending.locationId === locationId ? pending : null;
  const pendingMessage =
    pendingHere &&
    messages.filter(
      (message) =>
        message.role === "user" && message.content === pendingHere.content,
    ).length <= pendingHere.priorCount
      ? pendingHere.content
      : null;

  /**
   * Resolves true only once the server has the message, so the composer knows whether it
   * may clear what was typed. A failed send — offline, conflict, validation, server
   * error — must never destroy the text, because there is no way to get it back.
   */
  async function handleSend(content: string): Promise<boolean> {
    if (!locationId || !isReady || isBusy) return false;
    const priorCount = messages.filter(
      (message) => message.role === "user" && message.content === content,
    ).length;
    setSendFailure(null);
    setPending({ locationId, content, priorCount });
    try {
      const queued = await send.mutateAsync({
        locationId,
        conversationId,
        content,
      });
      setTrackedTurn({ locationId, id: queued.id });
      setStarted({ locationId, id: queued.conversation_id });
      return true;
    } catch (error) {
      setPending(null);
      setSendFailure({
        locationId,
        error: error instanceof Error ? error : new Error(String(error)),
      });
      return false;
    }
  }

  return {
    messages,
    pendingMessage,
    // Only while it is still ahead of the transcript. The moment the server writes the
    // reply down the same text is a real bubble, and showing both would double it.
    streamingText: stream.partialText.length > 0 ? stream.partialText : null,
    turn,
    isBusy,
    isLoading:
      conversations.isLoading ||
      (Boolean(conversationId) && conversation.isLoading),
    isReady,
    sendError:
      sendFailure && sendFailure.locationId === locationId
        ? sendFailure.error
        : null,
    loadError: conversations.error ?? conversation.error,
    pollError,
    send: handleSend,
    retryLoad: () => {
      void conversations.refetch();
      // Refetching a disabled query still runs its function, which without this guard
      // would request `/agent/conversations/null`.
      if (conversationId) void conversation.refetch();
      if (turnId) void turnQuery.refetch();
    },
    startNewChat: () => {
      if (!locationId || newChat.isPending) return;
      newChat.mutate(locationId);
    },
    // Offered only when there is something to leave: a transcript, or a run to abandon.
    canStartNewChat:
      isReady && !newChat.isPending && (messages.length > 0 || isBusy),
    isStartingNewChat: newChat.isPending,
  };
}
