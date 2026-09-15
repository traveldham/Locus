# Agent safety

The agent holds live write tools and is told to act without asking for confirmation twice.
Everything on this page is what stops that being dangerous. Code:
`app/services/agent/tools.py`; regression suites `tests/test_agent_tool_safety.py` and
`tests/test_agent_replay.py`.

## 1. The boundary is the conversation's location

`AgentToolContext` **requires** a `location_id`, exactly as the conversation row does, so
there is no shape of context that could mean "every location". Every tool closes over it.

**No tool takes a `location_id` argument.** Two tools are pointed at something other than a
location — `reply_to_review` takes a review, `poll_audit_job` takes a job — and both resolve
that row's location and check it against the conversation's before acting:

```python
def _in_scope(ctx, location_id):
    return location_id is not None and location_id == ctx.location_id
```

**That check is security, not tidiness.** `list_reviews` feeds up to fifty pieces of
customer-written review text into a model holding live write tools. Before the check, a
review whose text contained an instruction plus another location's review UUID was a working
prompt-injection exploit against a sibling location's public profile.

The refusal (`REVIEW_NOT_HERE`) deliberately reveals nothing about the other location — the
test asserts neither its title nor its id appears in the error. The system prompt also states
that tool output is data rather than instructions, but the refusal in the tool is what
actually enforces it.

`ToolArgs` sets `extra="forbid"`, so a model that invents a `location_id` is refused rather
than having it silently dropped — the write would otherwise land on this conversation's own
profile while the model reported editing the other one. **Caveat:** `StructuredTool` skips
validation entirely for a schema with no fields, so on the no-argument read tools a stray
argument is still merely dropped. The refusal is asserted for the five tools that take
arguments.

## 2. A field can be set, never cleared

`update_location_profile` can **set** a field. It cannot **clear** one.

`plan_edit` decides what to change from `payload.model_fields_set` — the fields explicitly
present on the request. Pydantic marks a field as set when it is passed to the constructor
**even if the value is `None`**, and a tool-calling model fills in every field in the schema,
sending `None` for the ones it was not asked about. Passed through unfiltered, "change the
phone number" would arrive at Google as "change the phone number **and blank the title,
website and description**" — a live public business profile, silently gutted.

Three shapes all count as "not supplied" and are dropped by `_supplied` before the request is
built:

| Shape | Why it matters |
| --- | --- |
| `None` | The model fills every field in the schema |
| `""` or whitespace | Told it cannot pass null, a model asked to "remove the description" passes `""` |
| `[]` | Asked to drop fixed hours it passes `[]`, which reached `regularHours` with zero periods and **wiped the week's schedule** |

All empty → `_ToolFailure(NOTHING_TO_CHANGE)`.

The cost is that the agent cannot express "make this field empty". That is the deliberate
trade: its job is filling in what an audit found missing, not erasing what is there. Clearing
a field is what the profile editor in the UI is for.

## 3. A write needs a real signed-in user

`_acting_user` raises `_ToolFailure(NO_USER)` if `ctx.user_id` is `None` or the row is gone.
It guards `sync_reviews`, `reply_to_review` and `update_location_profile`.
`AgentConversation.user_id` is `ON DELETE SET NULL`, so this is reachable, not theoretical —
and every write must be attributable in the `profile_actions` trail.

## 4. Session isolation

Each tool invocation opens its own session from the context's `session_factory`. Without it,
a failing tool's rollback expired the *caller's* ORM objects, and parallel calls under
`asyncio.gather` landed one tool's rollback inside another's transaction. See
[tools.md](tools.md) for the full account — both were real, reproduced bugs.

## 5. Two exceptions are never handed to the model

`SoftTimeLimitExceeded` and `asyncio.CancelledError` propagate out of `_guarded` rather than
becoming `{"error": ...}`. Both mean the turn is being torn down; handing "you ran out of
time" to the model would only buy it another model call it does not have time for.

## 6. One live turn per conversation

Two turns would replay the same history and interleave their messages into a transcript
neither of them read — and an interleaved transcript is one the tool-calling protocol
rejects outright.

The API checks before inserting, but two simultaneous requests can both pass that check, so
the invariant is actually held by a **partial unique index**:

```sql
uq_agent_turns_one_active_per_conversation
  ON agent_turns (conversation_id) WHERE status IN ('pending', 'running')
```

Losing the race surfaces as the same `409`.

Three things stop a stuck turn wedging the chat forever:

- Queuing the Celery task is inside a `try`. The turn row is committed *before* dispatch, so
  a broker that is down would otherwise leave it `pending` with nothing coming to run it;
  instead the turn is failed and the caller gets a `503`.
- The task's failure path guards its own rollback — a connection-level error makes the
  rollback raise too, and an exception escaping there would leave the turn `running`.
- A turn still active past `ABANDONED_AFTER` (timeout + 60 s) is released on the next
  message — the case a worker killed at its hard time limit leaves behind.

## 7. Replay is repaired, not trusted

Vertex/Gemini's tool-calling protocol requires every tool result to appear **immediately
after** the assistant message whose `tool_calls` requested it, matched on `tool_call_id`.
Because each message is committed as it appears, a turn that dies between asking for a tool
and recording its result leaves an assistant message that nothing answers. Replayed as-is,
that conversation would be rejected on *every* future turn — one interruption would kill the
chat permanently.

`_repair` runs on every replay: an unanswered call gets a synthetic result saying it never
finished (valid, and also true); a result whose call is missing is dropped. Repairing on
replay rather than on write means conversations already stored broken heal themselves.

Only the most recent `MAX_REPLAYED_MESSAGES` (60) are replayed, and the window is applied
**before** the repair, so a call cut away by the window takes its results with it rather than
stranding them.

## The test matrix

`tests/test_agent_tool_safety.py` — fixture: one organization, two locations, a review on the
*other* one.

| Test | Asserts |
| --- | --- |
| `a_failing_tool_leaves_the_callers_session_untouched` | A caller's held ORM object is still readable after a tool error; the next tool call still works |
| `every_failure_route_comes_back_as_a_readable_error` | `HTTP 404`, `HTTP 422` and a scope refusal all arrive as `{"error": ...}`; tools usable afterwards |
| `a_sibling_tools_rollback_cannot_undo_a_committed_edit` | Under `asyncio.gather` with 3 failing siblings the edit survives; exactly one `ProfileAction`, mask `["phoneNumbers"]` |
| `concurrent_tool_calls_never_share_a_session` | 3 concurrent invocations open 3 distinct sessions |
| `empty_hours_do_not_wipe_the_weekly_schedule` | `hours_periods: []` errors; 5 REGULAR periods intact; **zero** action rows |
| `a_blank_description_does_not_clear_the_description` | `"   "` errors; description unchanged; no action row |
| `a_blank_value_is_dropped_without_dropping_the_real_one` | `fields_changed == ["phone_primary"]` |
| `a_real_value_still_goes_through` | mask `["title", "regularHours"]` |
| `replying_to_another_locations_review_is_refused` | Provider `reply` never called; no action row; the error leaks neither the other title nor its id |
| `polling_another_locations_audit_job_is_refused` | — |
| `a_tool_handed_another_location_refuses_rather_than_retargeting` | `ValidationError` for all five argument-taking tools; neither profile written |
| `list_locations_returns_the_one_location_this_chat_is_about` | The sibling's id appears nowhere |
| `the_poll_budget_leaves_room_for_a_second_poll` | `POLL_BUDGET_SECONDS*2 + POLL_INTERVAL_SECONDS < turn timeout` |
| `a_soft_time_limit_is_not_handed_to_the_model_as_a_tool_error` | Propagates |
| `cancellation_is_not_handed_to_the_model_either` | Propagates |

Each was verified to fail when its fix is reverted — which is the only evidence that a
regression test is worth having.

**No test reaches a language model.** `StubChatModel` returns a scripted sequence of
assistant messages, so the real loop runs against real tools with no network anywhere. The
turn stream runs over an in-process `FakeRedisBroker`, autouse, so no test can open a socket
by forgetting to ask for it.
