# Frontend

Next.js 16 App Router, React 19, TypeScript strict. `frontend/`.

## Stack

| | |
| --- | --- |
| Framework | Next.js 16.2, **App Router only** — no `pages/`, no `middleware.ts` |
| Data | TanStack Query v5. No Redux, no Zustand |
| App state | Two React contexts — `auth-context`, `active-project` — plus local `useState` |
| Styling | Tailwind CSS v4, configured **in CSS**; there is no `tailwind.config` |
| Theme | `next-themes` with `attribute="data-theme"`; tokens in `src/app/css/default.css` and `dark.css` |
| Primitives | 44 vendored TailGrids components under `src/components/tailgrids/core/` |
| Charts | Recharts |
| Markdown | `react-markdown` + `remark-gfm`, no `rehype-raw` |
| Env | one variable — `NEXT_PUBLIC_API_URL` |

## Routes

Two groups: `(without-layouts)` for sign-in, `(with-layouts)` for everything authenticated.

| Route | Screen |
| --- | --- |
| `/login` | Sign-in. Prefilled with the seeded demo account |
| `/` | redirects to `/locations` |
| `/locations` | Profiles table; import sample profiles |
| `/locations/[id]` | One profile: preview, hours, attributes, edit form, change history |
| `/projects`, `/projects/[id]` | Projects and membership |
| `/reviews` | Review inbox: filters, reply composer, sync |
| `/posts` | Published posts |
| `/bookings` | Booking table |
| `/insights/performance` · `/search-terms` · `/photos` | Insights tabs |
| `/market/rankings` · `/market/competitors` | Local search |
| `/settings/integrations` | Google connection |
| `/recommendations` | **Audit directory** — every profile with its score |
| `/recommendations/[locationId]` | Overview: score ring, category rings, strengths, trend |
| `…/profile` · `…/category/[category]` · `…/issues` · `…/issues/[rule]` | The audit sections |

`/projects` and `/settings/integrations` are reached from the header, not the sidebar.

## The API client

`src/services/api/client.ts` is the only place that talks to the backend.

- Base URL `NEXT_PUBLIC_API_URL`, default `http://localhost:8000/api/v1`.
- Access token in `localStorage` under `locus_access_token`, injected as a bearer header.
- `credentials: "include"` on every call, so the refresh cookie travels.
- A `401` triggers **one** refresh and **one** replay — except on `/auth/refresh` and
  `/auth/login`. Concurrent refreshes are de-duplicated by a module-level promise.
- `ApiError` carries `status` and `detail`; the message prefers a string `detail`, then
  `detail.message`, then `body.message`, else a generic sentence.

Thirteen modules wrap the endpoints: `auth`, `projects`, `locations`, `reviews`, `posts`,
`bookings`, `insights`, `market`, `integrations`, `demo-profiles`, `recommendations`, `agent`.

## Hooks

Fourteen files under `src/hooks/`, each exporting a **query-key factory** so invalidation is
precise. The ones with non-obvious behaviour:

| Hook | Behaviour |
| --- | --- |
| `useLocationsQuery` | Injects the active project id; an explicit caller param wins |
| `useAllLocationsQuery` | Same endpoint with project scope **forced off**, for membership pickers |
| `useLocationActionsQuery` | Polls every 8 s while any action is `pending`/`approved`/`executing` |
| `useAuditJob` | Polls every 2 s, stops on terminal status, publishes the terminal state once per job id |
| `useAuditRun` | Composes latest + job into `{run, history, job, isAuditing, trackJob, inputsChanged}` |
| `useReviewStatusCountsQuery` | Three parallel `limit: 1` calls, reading only `total` |
| `useAgentChat` | The whole chat: transcript poll, turn poll, SSE stream, optimistic send |

## Audit cards

`src/components/recommendations/cards/registry.ts` is the whole contract:

```ts
export interface CategoryCardProps { card: unknown; items: Recommendation[]; location: AuditLocation }

export const CATEGORY_CARDS: Partial<Record<string, ComponentType<CategoryCardProps>>> = {
  reputation: ReputationCard, visibility: VisibilityCard, operations: OperationsCard,
  performance: PerformanceCard, content: ContentCard,
};
```

To add one: create `cards/<key>-card.tsx`, export a component typed to `CategoryCardProps`
(each card also exports its own `…CardData` interface and narrows the `unknown` `card` prop
against it), and register the key.

`CategoryAuditView` is the only consumer. `profile` deliberately never goes through the
registry — it renders `ProfileBeforeAfter` instead. A missing key is a silent fallback
paragraph, not a compile error.

## Auth on the client

Client-side only; there is no middleware, so nothing is protected at the edge. `AuthGuard`
wraps the whole authenticated tree, shows "Opening your workspace…" while loading, and
redirects to `/login?next=…` once loading finishes with no user.

`activeOrganization` is `user.organizations[0]` — there is no organization picker.

## Project scope

`ActiveProjectProvider`: `?project=` in the URL is the single source of truth.
`localStorage` (`locus.active-project`) only seeds it on first load, and a remembered id is
honoured only while it is still in the project list. `useActiveProjectId()` returns `null`
outside the tree, so data hooks can call it unconditionally.

## The agent widget

Mounted once in `(with-layouts)/layout.tsx`, **outside** the scrolling region, so it neither
moves nor resets as you navigate. Because it is global but a conversation belongs to one
location, the panel carries its own location picker rather than reading the route — it has to
work on pages with no location in the URL. The choice is remembered in `localStorage`.

The transcript shows no raw tool traffic: a tool call renders as a short activity chip
("Replied to a review") that pulses while it runs. Model output goes through `react-markdown`
with `skipHtml` and an element allowlist, deliberately — it can quote customer-written review
text, which is untrusted.

Streaming is a `fetch`, not `EventSource`, because `EventSource` cannot send an
`Authorization` header. → [../features/ai-agent/streaming.md](../features/ai-agent/streaming.md)

## Conventions

From `AGENTS.md`: prefer Server Components; authenticated routes under `(with-layouts)`; use
the semantic Tailwind tokens from `globals.css` rather than raw colours; reuse
`components/tailgrids/core/` before adding a library; 44×44px minimum touch targets. Gate is
`npm run lint && npm run build` — there is no test suite.

## Known gaps

Verified, and listed so nobody rediscovers them:

- **Performance totals tiles read keys that do not exist** (`totals.impressions` and the
  per-surface keys). The backend emits `impressions_total`, `impressions_maps`, … so those
  tiles show "not reported" even when the number was computed.
- **The change-history summary reads Google mask paths as payload keys**, so every value
  renders "—" and labels fall through to "Phonenumbers". The real before/after data is in
  `payload.changes`, unread.
- **`ProfileActionResponse.user` is an object** `{id, email, full_name}` but is typed
  `string | null` and interpolated into a template literal.
- **The hours error is set under `hours_periods` and cleared under `hours`**, so editing an
  hours row does not clear the banner.
- **`bookings.status_counts` is returned but never read.**
- Several TS interfaces are **stricter than the API** — non-nullable fields the backend
  returns nullable (tracked keywords, competitors, media summary, bookings).
- `DataSource` is declared twice, in `insights.ts` and `market.ts`.
- `src/types/` is empty; `tsconfig.json` includes a path that does not exist.
