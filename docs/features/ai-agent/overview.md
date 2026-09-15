# AI agent

A chat agent that **works on** a Google Business Profile — not one that talks about it. It
reads the profile's audit, reviews and fields, and it acts: replying to reviews, editing
profile fields, running new audits.

A conversation is scoped to **exactly one location**. That is the whole boundary: the
profile the chat is about is the only one the agent can read, and the only one it can write
to.

## What it can do

| Ask it | What happens |
| --- | --- |
| "How is this location doing?" | Reads the latest audit — score, grade, coverage, top priorities |
| "Reply to the reviews nobody has answered" | Lists the unanswered ones, writes replies, sends them, tells you which |
| "Apply the audit's suggested description" | Reads the audit's own AI draft and writes it to the profile |
| "Add Saturday hours" | Edits the profile through the same path the profile editor uses |
| "Run an audit and tell me if that helped" | Queues a run, waits for it, compares |
| "What have you changed so far?" | Reads the `profile_actions` audit trail |

## The one design decision that matters

**The agent owns no business logic.** Every capability is an existing function:
`reply_to_review` calls the same `app.api.reviews.reply_to_review` the review inbox calls;
`update_location_profile` calls the same `app.api.locations.apply_edit` the profile editor
calls. Two consequences:

- The agent cannot drift away from the product's behaviour, because there is only one
  implementation of each behaviour.
- Every write it makes lands in the `profile_actions` audit trail
  (`pending → executing → succeeded/failed`) with the user's name on it — because that trail
  lives inside the function it called, not in the agent.

Anything the agent does is something a person could have done through the UI, recorded the
same way.

## How it runs

```
POST /messages  →  writes the message, creates an AgentTurn (pending), queues Celery, returns 202
                        │
Celery worker   →  claims the turn, rebuilds the transcript, runs the LangGraph loop
                        │           each message committed as it appears
                        ▼
                   Redis pub/sub  agent:turn:{id}
                        │
Browser         →  GET /turns/{id}/stream   (server-sent events)
                   or polls GET /turns/{id} — both work, both show the same answer
```

A turn is a background job, not a request: one message can cost several model calls and
several writes. One live turn per conversation, held by a partial unique index — a second
is a `409`.

## The loop

A LangGraph `StateGraph` whose entire state is the message list. Two nodes, `agent` and
`tools`; an assistant message carrying `tool_calls` goes to the tools node and control
returns to the model; an assistant message with no tool calls ends the turn.
`RECURSION_LIMIT = 25` bounds it.

One deliberate choice: a **single loop with eleven tools**, not a supervisor delegating to
sub-agents. The model can sequence "read the audit, list unanswered reviews, reply to this
one" perfectly well by itself.

## Configuration

Nothing beyond what the audit's suggestion layer already needed:

```
LLM_PROVIDER=vertex
VERTEX_PROJECT=<your Google Cloud project>
VERTEX_LOCATION=global
VERTEX_MODEL=gemini-3.8-flash
AGENT_TURN_TIMEOUT_SECONDS=180      # bounded 30-600
```

Vertex authenticates with application default credentials
(`gcloud auth application-default login`, or a service account on the VM). Temperature is
`0.2`. `build_chat_model` raises with the exact setting to fix, and that message reaches the
user as the turn's error rather than disappearing into a log.

**Vertex only.** The audit's suggestion layer can also use the Gemini Developer API; the
agent cannot — tool-calling needs a chat-model binding, and a second one doubled the surface
without adding capability.

## Where things live

| Path | What |
| --- | --- |
| `app/api/agent.py` | The six endpoints, including the SSE stream |
| `app/services/agent/graph.py` | The LangGraph loop, replay and repair |
| `app/services/agent/tools.py` | All eleven tools and every safety rule |
| `app/services/agent/llm.py` | Building the chat model |
| `app/services/agent/stream.py` | Redis pub/sub, event shapes |
| `app/tasks/agent.py` | The Celery turn |
| `app/models/agent.py` | Conversation, message, turn |
| `frontend/src/components/agent/` | The floating widget |
| `frontend/src/hooks/use-agent-chat.ts` | Streaming, polling, fallback |

## Known limits

- **Fixture data, not Google.** Every write goes to the sample provider — Google never
  approved this project for Business Profile API access (`429 RESOURCE_EXHAUSTED`,
  `quota_limit_value: 0`). The write path is real and complete; what sits behind it is not
  yet Google. When quota is granted, `get_provider()` is the one place that changes.
- **One location per conversation.** No project-wide chat.
- **No field clearing** — the agent can set a field, never blank one. See
  [safety.md](safety.md).
- **No way to cancel a running turn.** Start a new chat; an abandoned turn is released
  automatically.
- **Conversation history is not browsable.** The widget shows the newest conversation per
  location; older ones are stored and returned by the list endpoint, but no UI reaches them.
- **A missed stream event is not resent** — no replay buffer, no last-event-id.

## Related

- [architecture.md](architecture.md) — why it is shaped this way, in depth
- [tools.md](tools.md) — every tool, its arguments and its budget
- [streaming.md](streaming.md) — the SSE wire contract
- [safety.md](safety.md) — the invariants and the tests that hold them
- [../audit-engine/suggestions.md](../audit-engine/suggestions.md) — the other AI system, which drafts text for findings
