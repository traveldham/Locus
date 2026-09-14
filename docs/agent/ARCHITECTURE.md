# The operator agent

A chat agent that works on Google Business Profiles. It reads their audits, reviews and
fields, and it acts on them: replying to reviews, editing profile fields, and running new
audits. It is not a chatbot bolted onto the product — it drives the same code paths the
product's own screens drive, so anything it does is something a person could have done
through the UI, recorded the same way.

A conversation is scoped to **exactly one location**. That is the whole boundary: the
profile the chat is about is the only profile the agent can read, and the only one it can
write to.

Ask it "how is this location doing?" and it reads the audit. Tell it "reply to the reviews
nobody has answered" and it lists them, writes replies, sends them, and tells you which
ones it answered. Ask "did that help?" and it runs a fresh audit and compares the score.

---

## Why it is shaped this way

**The agent owns no business logic.** Every capability it has is an existing function.
`reply_to_review` calls the same `app.api.reviews.reply_to_review` the review inbox calls;
`update_location_profile` calls the same `app.api.locations.apply_edit` the profile editor
calls. Those are plain `async def` functions whose `Depends` annotations are inert when
called in-process, so the agent calls them directly rather than over HTTP. Two consequences
matter: the agent cannot drift away from the product's behaviour, because there is only one
implementation; and every write it makes already lands in the `profile_actions` audit trail
(`pending → executing → succeeded/failed`) with the user's name on it, because that trail
lives inside the function it called.

**A turn is a background job, not a request.** One message can cost several model calls and
several writes to Google. That cannot sit in an HTTP request, so posting a message records
it, queues a Celery turn and returns the turn's id. The client polls.

**The transcript is written as it happens.** Each message the loop produces is committed
immediately rather than batched at the end, so an agent that spends forty seconds working
is visibly working. That is also what makes a mid-turn page reload recoverable.

**Nothing the model does can take down a worker.** A tool that fails returns a structured
error the model can read and explain; an exception anywhere in the loop lands as a `failed`
turn carrying its reason. A chat that silently stops answering is the worst outcome, so it
is the one outcome that cannot happen.

---

## The loop

```
                  ┌──────────────────────────────┐
                  │  system prompt + transcript   │
                  └───────────────┬──────────────┘
                                  ▼
    ┌──────────► ┌──────────────────────────────┐
    │            │  agent node                   │
    │            │  model.bind_tools(...)        │
    │            └───────────────┬──────────────┘
    │                            │
    │              tool calls?   │   no ──────────►  END (final answer)
    │                            │ yes
    │                            ▼
    │            ┌──────────────────────────────┐
    └────────────┤  tools node (ToolNode)        │
                 │  runs the requested tools     │
                 └──────────────────────────────┘
```

A LangGraph `StateGraph` whose entire state is the message list. The conditional edge is
`tools_condition`: an assistant message carrying `tool_calls` goes to the tools node, which
runs them and appends one tool message per call, and control returns to the model. An
assistant message with no tool calls ends the turn.

`RECURSION_LIMIT = 25` bounds it. A model that has not answered in twenty-five steps is
looping, not working.

One deliberate choice: this is a **single loop with eleven tools**, not a supervisor
delegating to sub-agents. The model is perfectly capable of sequencing "read the audit,
list the unanswered reviews, reply to this one" itself. A routing layer would have added
indirection and a second system prompt without adding capability.

### The system prompt

Rebuilt on every model call from the location and today's date, and never stored as a
message — so a changed prompt applies to old conversations too. Its load-bearing rule is
the first one: *call a tool to learn anything factual; never state a score, a finding, a
review, or that an action succeeded, unless a tool just said so.* Without that, a model
will happily invent a plausible health score. It is also told to act without asking for
confirmation twice, to say concretely what it did afterwards, and that it can only ever see
one location.

### Replaying a conversation

This is the part most likely to break if touched carelessly. Vertex/Gemini's tool-calling
protocol requires every tool result to appear **immediately after** the assistant message
whose `tool_calls` requested it, matched on `tool_call_id`. Reordering rows, dropping an
assistant message that had no text of its own, or losing a call id does not degrade the
answer — it makes the request invalid.

So messages are stored with everything needed to reproduce that exactly:

| Row | Stored | Replays as |
|---|---|---|
| `role=user` | `content` | `HumanMessage` |
| `role=assistant` | `content`, `tool_calls` (JSON) | `AIMessage(content, tool_calls=[...])` |
| `role=tool` | `content`, `tool_call_id`, `tool_name` | `ToolMessage(content, tool_call_id, name)` |

**A stored transcript is not assumed to be valid.** Because each message is committed as it
appears, a turn that dies between asking for a tool and recording its result — a crash, the
recursion limit, a worker killed at its time limit — leaves an assistant message that
nothing answers. Replayed as-is, that turn's conversation would be rejected on *every*
future turn: one interruption would kill the chat permanently.

So `_repair` runs on every replay. An unanswered call is given a synthetic result saying it
never finished, which is valid and also true; a result whose call is missing is dropped.
Repairing on replay rather than on write means conversations already stored broken heal
themselves. There are regression tests for both orphan directions.

Only the most recent `MAX_REPLAYED_MESSAGES` (60) are replayed. A long-running conversation
would otherwise outgrow the model's context — tool results are the bulk of it, an audit
summary alone running to thousands of characters — and then fail on every turn. The window
is applied *before* the repair, so a call cut away by the window takes its results with it
rather than stranding them.

Ordering is `created_at, id`. The id only makes the order deterministic, not correct — it
is random, so a genuine timestamp collision could still order a result before its call.
`_repair` is what makes that survivable rather than fatal.

---

## The tools

| Tool | Reads or writes | Backs onto |
|---|---|---|
| `get_latest_audit` | read | `recommendations.runs.latest_run` — returns a compact summary (score, grade, coverage, top priorities), never the whole report, which is far too large for a prompt |
| `list_audit_suggestions` | read | the same run's AI-drafted `Suggestion`s, each with the id the existing write tool needs — or an honest reason it cannot be applied |
| `start_audit` | read† | `recommendations.queue.start_audit` — joins an audit already running rather than starting a second |
| `poll_audit_job` | read | polls the `AuditJob` internally for up to ~90s rather than making the model re-ask every two seconds |
| `list_reviews` | read | `api.reviews.list_reviews`, scoped to this location; `unreplied_only` is the filter that matters |
| `sync_reviews` | read† | `api.reviews.sync_reviews` — refreshes from the provider before acting |
| `reply_to_review` | **write** | `api.reviews.reply_to_review` |
| `get_location_profile` | read | `api.locations.get_location` |
| `update_location_profile` | **write** | `api.locations.apply_edit` |
| `list_recent_actions` | read | `api.locations.list_location_actions` — lets it answer "what have you changed so far" |
| `list_locations` | read | the one location the chat is about — how it answers "which profile am I on" |

† writes a job or sync row, but nothing on the public profile.

**No tool takes a `location_id`.** The conversation's location is closed over, so there is
no argument for the model to get wrong and nothing to guess. The two tools that are pointed
at something other than that location are the ones given a row rather than a location —
`reply_to_review` takes a review, `poll_audit_job` takes a job — and both resolve that row's
location and check it before acting. The argument schemas also forbid unknown fields, so a
model that invents a `location_id` anyway is refused rather than having it silently dropped:
the write would otherwise land on this conversation's own profile while the model reported
editing the other one.

### Every tool call gets its own session

`AgentToolContext` carries a `session_factory`, not a session, and each invocation opens
its own. This is load-bearing for two reasons, both of which were real bugs before it:

- **A tool's rollback would expire the caller's objects.** `AsyncSession.rollback()` expires
  every instance in the identity map — `expire_on_commit=False` governs commit, not
  rollback. A tool that failed, or any successful `poll_audit_job`, left the task holding
  expired objects, and the task's next attribute read raised `MissingGreenlet`. The effect
  was that the model never saw a single tool error: the entire "a tool never raises, the
  model reads the error and adapts" design was dead on arrival.
- **Parallel tool calls corrupted each other.** `ToolNode` runs a model's parallel calls
  under `asyncio.gather`, and Gemini emits them routinely. Sharing one session meant one
  tool's rollback landed inside another's transaction — a reproduction had a legitimate
  profile edit *and its audit row* silently destroyed by a failing sibling.

The trade is that a tool cannot see the task's uncommitted state. That costs nothing: the
task only commits chat messages, which no tool reads.

### Applying the audit's own drafts

The audit already drafts content: a reply for each unanswered low review, a description
for a profile that has none. The agent could not see any of it, so "apply the audit's
suggested replies" produced an agent writing its own wording and ignoring drafts the
product had already generated and safety-checked.

`list_audit_suggestions` shows it those drafts. It is a **read** tool, deliberately: the
drafts are applied with `reply_to_review` and `update_location_profile`, which already go
through the human write paths and the `ProfileAction` trail. A second way to write would
be exactly the unaudited parallel path the tools module exists to prevent.

Each suggestion says where it can be applied, and that resolution is the delicate part.
A finding's `subject` is **Google's** review id — `reputation.review_ref` prefers it — and
`reply_to_review` takes our row UUID. The same mismatch has already shipped once as a
button that did nothing. The row id appears only in the finding's `evidence` entry whose
source is `reviews`, so that is where it is read from, and it still has to name exactly one
review of *this* location before it is offered; anything else comes back as
`applies_to: null` with a sentence saying the target could not be identified. Guessing
would publish a reply under a review nobody chose.

A drafted `attributes` map is the same problem in a different shape. It is keyed by the
catalog's bare attribute name; the stored id is that name behind `attributes/` and the
value type is the catalog's own, so both are resolved here and handed over as a payload
`update_location_profile` takes as it stands. The agent has no tool that reads the catalog,
so a prompt telling it to look the type up would be a prompt telling it to guess. A drafted
answer is always a yes or no, and only a `BOOL` attribute can hold one, so a name the
catalog does not list or types otherwise is left out and the suggestion says how many were.

The rest have no write path at all — posts and bookings are read-only here, and secondary
categories are not in `EDITABLE_FIELDS`. Each of those says plainly that it is advice for a
person, because a model shown a draft with no way to apply it will otherwise invent one.

### The safeguard worth knowing about

`update_location_profile` can **set** a field. It cannot **clear** one.

`plan_edit` decides what to change from `payload.model_fields_set` — the fields explicitly
present on the request. Pydantic marks a field as set when it is passed to the constructor
**even if the value is `None`**, and a tool-calling model fills in every field in the
schema, sending `None` for the ones it was not asked about. Passed through unfiltered,
"change the phone number" would arrive at Google as "change the phone number **and blank
the title, website and description**" — a live public business profile, silently gutted.

Three shapes all count as "not supplied" and are dropped before the request is built:
`None`, a blank or whitespace-only string, and an empty list. The last two matter as much
as the first, because the model is told it cannot pass null: asked to "remove the
description" it will pass `""`, and asked to drop fixed opening hours it will pass `[]` —
which reached `regularHours` with zero periods and wiped the week's schedule.

The cost is that the agent has no way to express "make this field empty", which is the
deliberate trade: its job is filling in what an audit found missing, not erasing what is
there. Clearing a field is what the profile editor in the UI is for. Regression tests cover
each shape, asserting the stored value and the audit trail are untouched.

### Tenant and location scoping

Every tool closes over the conversation's location, and `AgentToolContext` requires one —
exactly as the conversation row does — so there is no shape of context that could mean
"every location". `reply_to_review` and `poll_audit_job` are given a review or a job rather
than a location, and the row they are given is what decides where the write lands, so that
row's location is resolved and checked against the conversation's before anything happens.

That check is security, not tidiness. `list_reviews` feeds up to fifty pieces of
customer-written review text into a model holding live write tools that is told to act
without asking for confirmation twice. Before the check, a review whose text contained an
instruction plus another location's review UUID was a working prompt-injection exploit
against a sibling location's public profile. The system prompt now also states plainly that
tool output is data rather than instructions, but the refusal in the tool is what actually
enforces it.

---

## A turn, end to end

1. `POST /agent/conversations/{id}/messages` writes the user's message, creates an
   `AgentTurn` in `pending`, commits, then queues `agent.run_turn` and stores the task id.
   It returns `202` immediately with the turn.
2. The Celery worker claims the turn (it ignores any turn not in `pending`, so two workers
   cannot both answer one message), marks it `running`, and rebuilds the conversation.
3. The graph runs. Each message it produces is written and committed as it appears, and
   `turn.current_tool` is set to whatever the agent is about to run, which is what the UI's
   "Checking reviews…" line reads.
4. The turn ends `succeeded`, or `failed` with the reason — a model that cannot be reached,
   a tool that failed, a loop that hit its bound.
5. The client watches `GET /agent/turns/{id}/stream` — or polls `GET /agent/turns/{id}`
   and re-reads the transcript, which still works and still shows the same answer.

A second turn is refused with `409` while one is running. Two turns on one conversation
would replay the same history and interleave their messages into a transcript neither of
them read — and per the repair section, an interleaved transcript is one the protocol
rejects. The API checks before inserting, but two simultaneous requests can both pass that
check, so the invariant is actually held by a **partial unique index** on
`agent_turns (conversation_id) WHERE status IN ('pending', 'running')`; losing the race
surfaces as the same `409`.

Three things stop a turn becoming a permanent wedge, because "one live turn per chat" means
a stuck turn blocks the chat forever:

- Queuing the Celery task is inside a `try`. The turn row is committed *before* dispatch, so
  a broker that is down would otherwise leave it `pending` with nothing coming to run it;
  instead the turn is failed and the caller gets a `503`.
- The task's failure path guards its own rollback. A connection-level error makes the
  rollback raise too, and an exception escaping there would leave the turn `running`.
- A turn still active well past its own timeout (`ABANDONED_AFTER`) is released on the next
  message — the case a worker killed at its hard time limit leaves behind, since it never
  gets to write anything.

---

## The API

| | |
|---|---|
| `POST /agent/conversations` | `{location_id}`, required → the conversation |
| `GET /agent/conversations?location_id=` | one location's conversations, newest first |
| `GET /agent/conversations/{id}` | the full transcript, plus `active_turn` |
| `POST /agent/conversations/{id}/messages` | `{content}` → `202` + the queued turn |
| `GET /agent/turns/{id}` | turn status — the polling target |
| `GET /agent/turns/{id}/stream` | the same turn as it happens, as server-sent events |

Everything is scoped to the caller's organization; another tenant's conversation, turn or
location is a `404`, not a `403`. A conversation cannot be created without a location: the
request is `422`, and the column is `NOT NULL` besides, because a chat with no location is
an agent with no boundary.

`active_turn` on the conversation detail exists for one reason: a turn outlives the request
that started it, so a client that reloaded the page mid-answer has no other way to discover
that the agent is still working. Without it the chat looks finished while messages are still
being written to it.

---

## Watching a turn happen

The turn runs in a Celery worker and the reader is attached to the API, so the API
process cannot see the model's tokens. The two are joined by one Redis pub/sub channel
per turn, `agent:turn:{turn_id}` — Redis is already the Celery broker, so this adds no
infrastructure. The worker publishes; `GET /agent/turns/{id}/stream` subscribes and
forwards as server-sent events, scoped to the caller's organization exactly like the
poll it replaces.

Four events. `token` `{text}` is an assistant text delta; `message` is a message that has
just been committed, in the same shape the REST API returns; `status` `{status,
current_tool}` says what the agent is doing; `done` `{status, error}` is the only one a
client cannot do without, because it is what says to stop waiting.

The graph is invoked with `stream_mode=["values", "messages"]` — the `values` half still
does all the writing, unchanged, and the `messages` half is only read for deltas. That
mode is not a token stream: LangGraph also puts every node's finished output on it, so a
whole `ToolMessage` and the completed `AIMessage` arrive there alongside the chunks that
built it. Only an `AIMessageChunk` is forwarded. (The node still calls `ainvoke`;
LangGraph's messages handler is a streaming callback handler, and `BaseChatModel` routes
an invoke through `_astream` whenever one is attached.)

**Streaming is an addition and never a replacement.** Everything on the channel is a view
of something already committed, published after the commit, so a reader can never be
shown a message a reload would take away. Publishing therefore cannot fail a turn: a
broker that is down, a channel nobody reads, a value that will not serialise — all
logged and stepped over. A reader loses an animation; the turn loses nothing, and the
transcript in the database stays the only source of truth.

Three things stop a stream becoming its own kind of wedge: a `done` in a `finally`, so
every exit path including failure says so; a heartbeat comment every 15 seconds, without
which the proxies in front of this API drop an idle connection; and a hard lifetime cap
just above `AGENT_TURN_TIMEOUT_SECONDS`, because a worker killed at its own time limit
publishes nothing on the way out. A turn that is already terminal when the request
arrives is answered with `done` immediately rather than subscribing to a dead channel.

---

## The interface

A **floating widget, present on every authenticated page** — mounted once in
`app/(with-layouts)/layout.tsx`, outside the scrolling region, so it neither moves nor
resets as you navigate. Collapsed it is a button in the corner; open it is a panel.

Because it is global but a conversation belongs to one location, the panel carries its own
location picker rather than reading the route — it has to work identically on pages that
have no location in the URL. The choice is remembered in `localStorage`.

The transcript does not show raw tool traffic. A tool call renders as a short activity chip
("Replied to a review", "Ran an audit") that pulses while it runs, and the agent's actual
words render as text. What you read is a conversation, not a debug log.

---

## Running it

Configuration is what the audit's suggestions already needed — nothing new:

```
LLM_PROVIDER=vertex
VERTEX_PROJECT=<your Google Cloud project>
VERTEX_LOCATION=global
VERTEX_MODEL=gemini-3.8-flash
```

Vertex authenticates with application default credentials (`gcloud auth application-default
login`, or a service account attached to the VM). `build_chat_model` raises with the exact
setting to fix if the provider is not configured, and that message reaches the user as the
turn's error rather than disappearing into a log.

`AGENT_TURN_TIMEOUT_SECONDS` (default 180) bounds a turn. It is set per-task because the
Celery-wide limit is sized for an audit, and someone waiting at a keyboard is not.

The Celery worker must load the new task module — `app.tasks.agent` is in the worker's
`include` list, so it is picked up on worker start. A deploy that restarts `locus-celery`
needs nothing else.

### Tests

```bash
cd backend && uv run pytest tests/test_agent_tools.py tests/test_agent_graph.py \
                            tests/test_agent_api.py tests/test_agent_turn.py \
                            tests/test_agent_tool_safety.py tests/test_agent_replay.py \
                            tests/test_agent_stream.py tests/test_agent_audit_summary.py \
                            tests/test_agent_audit_suggestions.py
```

`test_agent_tool_safety.py` and `test_agent_replay.py` are the regression suite for the
defects described above — session isolation under `asyncio.gather`, the three empty-value
shapes, the cross-location refusal, poll budgets, and both orphan directions on replay.
They were each verified to fail when the corresponding fix is reverted, which is the only
evidence that a regression test is worth having.

No test reaches a language model. `StubChatModel` in `tests/stubs.py` returns a scripted
sequence of assistant messages, so a test can say "first ask for this tool, then answer" and
the real loop runs against real tools with no network anywhere. The tools themselves run
against the in-memory provider stubs the rest of the suite uses, and the turn stream runs
over an in-process broker (`FakeRedisBroker`), autouse so no test can open a socket by
forgetting to ask for it. `test_agent_stream.py` asserts the event contract a browser
codes against, and — with `StreamingChatModel`, a real `BaseChatModel` behind a scripted
answer — that the deltas really do come out of LangGraph one word at a time.

---

## Known limits

- **Fixture data, not Google.** Every write goes to the sample provider, because Google has
  never approved this project for Business Profile API access (every live call returned
  `429 RESOURCE_EXHAUSTED`, `quota_limit_value: 0`). The agent's write path is real and
  complete; what is behind it is not yet Google. When quota is granted, `get_provider()` is
  the one place that changes and the agent needs no edit at all.
- **Vertex only.** The audit's suggestion layer can also use the Gemini Developer API; the
  agent cannot. Tool-calling needs a chat-model binding, and supporting a second one doubled
  the surface without adding capability.
- **One location per conversation.** There is no project-wide chat: comparing two profiles,
  or auditing a whole project in one go, means two conversations and the Overview screen.
  The database holds the invariant as `location_id NOT NULL`, because a row written by a
  migration or a fix-it script has to obey it too.
- **No field clearing.** See the safeguard above.
- **No way to cancel a running turn.** There is no endpoint for it; the UI's "start a new
  chat" is the escape, and an abandoned turn is released automatically.
- **Conversation history is not browsable.** The widget shows the newest conversation for a
  location. Older ones are still stored and still returned by the list endpoint, but there
  is no UI to reach them.
- **A missed event is not resent.** The stream has no replay buffer and no last-event-id:
  a reader who reconnects gets a `status` saying where the turn is now and then whatever
  comes next, and reads the rest from the transcript. That is the trade for pub/sub, and
  it is survivable only because the transcript is the record and the stream is not.
