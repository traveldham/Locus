# 006 — Integrations page + discovery/import wizard UI

**Status:** BUILT (unverified in a browser)

## Goal

The most important screen in the product: the first time a user sees their own business data in our app.

## Screens

| Route | Purpose |
|---|---|
| `/settings/integrations` | Connect card when disconnected; account, status, last sync, "Find my locations" and Disconnect when connected |
| `/settings/integrations/discover` | Discovery results + selection + project naming + import |

## The discovery screen

Every discovered location shows status chips:

`Verified` / `Unverified` · `Open` / `Temporarily closed` / `Permanently closed` · `Pending edits` · `Google suggested updates` · `Duplicate` · `Incomplete` (with which fields are missing)

Plus select-all, per-row checkboxes, a live "N of M selected" count, and search.

## Requirements that are easy to skip

- **Disconnect needs a confirmation dialog** stating the consequence plainly. It revokes access at Google.
- **Real empty state** for "connected but Google returned zero locations" — it happens, and the user needs to be told why and sent to Google, not shown a blank page.
- **Status chips must not rely on colour alone** — colour plus text, for accessibility.
- Tables get their own `overflow-x-auto` container. The page must never scroll sideways.
- Render only what the API returns. No invented counts, metrics or outcomes — `frontend/AGENTS.md` forbids fabricated data.

## Implementation notes worth keeping

- Chips are restricted to `neutral` / `success` / `warning` / `error` / `primary`. This was originally done on the belief that the other badge tokens were missing from `dark.css` — **that belief was wrong** (all 11 badge colours have full parity, verified). The restriction is harmless and the palette stays small on purpose, but do not repeat the claim: the full badge range is available.
- Dark mode is driven by `[data-theme="dark"]` token swaps. `dark:` utilities now work too — see the fix note below.
- Rendered as a responsive grid list rather than a `<table>`, so the most important onboarding screen reads correctly at 400px with no sideways scrolling at all.
- The summary headline counts what is actually rendered, never a separate `total`, so the header can never contradict the list.
- OAuth return params are stripped with `history.replaceState` so refreshing does not replay the banner. Five known OAuth error codes map to plain messages, with a fallback that still surfaces the raw code.
- `needs_reauth` / `revoked` / `error` connection states each render an explanatory alert and swap the primary action to "Reconnect Google".
- The "Incomplete" chip is a disclosure button listing the missing fields inline, not a tooltip — tooltips are unusable on touch.

## Fixed during integration

Post-import redirect originally went to `/projects/{slug}`; the API keys project detail on UUID, so it now routes to `/projects/{id}`.

## Verification

`npm run lint` and `npx tsc --noEmit` clean.

**Not verified:** never opened in a browser. Needs a visual pass at desktop and 400px in both themes, and a real Google consent round-trip.
