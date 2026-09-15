# Streaming a turn

The wire contract for anyone writing a client. Code: `app/services/agent/stream.py`,
`app/api/agent.py`, and on the browser side `frontend/src/services/api/agent.ts`.

## Why pub/sub

The turn runs in a Celery worker; the reader is attached to the API process. The API cannot
see the model's tokens. The two are joined by **one Redis pub/sub channel per turn**,
`agent:turn:{turn_id}` — Redis is already the Celery broker, so this adds no infrastructure.
The worker publishes; `GET /api/v1/agent/turns/{id}/stream` subscribes and forwards as
server-sent events, scoped to the caller's organization exactly like the poll it replaces.

## The four events

Wire envelope on the Redis channel is `{"event": ..., "data": {...}}`; the SSE frame is
`event: {name}\ndata: {json}\n\n`.

| Event | Payload | Meaning |
| --- | --- | --- |
| `token` | `{text}` | An assistant text delta |
| `message` | the full `AgentMessageResponse` | A message that has just been **committed** |
| `status` | `{status, current_tool}` | What the agent is doing now |
| `done` | `{status, error}` | Stop waiting. The only event a client cannot do without |

Event ordering: `status` is the first event on every path **except** one — a turn that is
already terminal when the request arrives is answered with `done` alone, immediately, rather
than subscribing to a dead channel. (If the turn settles in the gap between opening the
subscription and re-reading the row, you get `status` then `done`.)

## Headers and timing

| | |
| --- | --- |
| `Cache-Control` | `no-cache` |
| `Connection` | `keep-alive` |
| `X-Accel-Buffering` | `no` — nginx must not buffer this |
| Heartbeat | a `:` comment every `HEARTBEAT_SECONDS` (15), or proxies drop an idle connection |
| Subscribe timeout | `SUBSCRIBE_TIMEOUT_SECONDS` (5) |
| Hard lifetime cap | `MAX_STREAM_SECONDS` = turn timeout + 30 s |

A `done` is emitted in a `finally`, so **every** exit path including failure says so. The
hard cap exists because a worker killed at its own time limit publishes nothing on the way
out.

nginx needs the SSE route excluded from buffering. The shipped config does it with a regex
location, which takes precedence over the `/api/` prefix:

```nginx
location ~ ^/api/v1/agent/turns/[^/]+/stream$ {
    proxy_pass http://127.0.0.1:8000;
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 600s;
    proxy_set_header Connection "";
}
```

## Streaming is an addition, never a replacement

Everything on the channel is a **view of something already committed**, published after the
commit. A reader can never be shown a message that a reload would take away.

Publishing therefore cannot fail a turn: a broker that is down, a channel nobody reads, a
value that will not serialise — all logged and stepped over. `TurnEvents` latches `_broken`
on the first publish failure and stops trying; `done()` resets it for one last attempt. A
reader loses an animation; the turn loses nothing, and the transcript in the database stays
the only source of truth.

Polling `GET /api/v1/agent/turns/{id}` and re-reading the transcript works identically and
shows the same answer. That is the fallback, and it is always available.

## The graph side

The graph is invoked with `stream_mode=["values", "messages"]`. The `values` half still does
all the writing, unchanged; the `messages` half is only read for deltas.

That mode is **not** a token stream — LangGraph also puts every node's finished output on it,
so a whole `ToolMessage` and the completed `AIMessage` arrive alongside the chunks that built
them. **Only an `AIMessageChunk` is forwarded.** (The node still calls `ainvoke`; LangGraph's
messages handler is a streaming callback handler, and `BaseChatModel` routes an invoke
through `_astream` whenever one is attached.)

Each produced message is `db.add` → `turn.current_tool` set → `commit` → **then** published.

## Failure codes

| Code | When |
| --- | --- |
| `404` | Turn not found, or another tenant's |
| `503 "Live updates are unavailable. Poll the turn instead."` | The subscription could not be opened |
| `503 "The agent is unavailable right now. Try again shortly."` | Queuing the Celery task failed when the message was posted |

## No resume

There is **no replay buffer and no last-event-id**. A reader who reconnects gets a `status`
saying where the turn is now, then whatever comes next, and reads the rest from the
transcript. That is the trade for pub/sub, and it is survivable only because the transcript
is the record and the stream is not.

## How the browser consumes it

`EventSource` **cannot send an `Authorization` header**, which is why the client streams over
`fetch` instead — inheriting the bearer token, the refresh-once-on-401 retry and the
`ApiError` shape.

The parser reads `response.body.getReader()` with a streaming `TextDecoder`, normalises CRLF
across the buffer, and cuts frames only at `\n\n`. Comment lines (including the `: ping`
heartbeats) are skipped; one leading space after a colon is stripped; repeated `data:` lines
are joined with `\n`; `id` and `retry` are deliberately ignored. A frame that will not parse
is dropped — one frame lost, not the stream. An unknown event name is ignored.

An idle watchdog (`STREAM_IDLE_TIMEOUT_MS = 45_000`, "three missed heartbeats") cancels the
reader on silence, which drops out of the loop like any other broken stream. The promise
resolves only after a `done` frame; every other exit throws. There is no retry and no resume
on the client either — when the stream dies, the polls that stood down while it was live
resume and finish the job.
