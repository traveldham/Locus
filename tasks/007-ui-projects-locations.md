# 007 — Projects + Locations UI

**Status:** BUILT (unverified in a browser)

## Goal

The screens the user lives in after onboarding.

## Screens

| Route | Purpose |
|---|---|
| `/projects` | List, with a real empty state pointing a new account at `/settings/integrations` |
| `/projects/new` | Name it, pick from locations already imported — **no trip back through Google** |
| `/projects/[id]` | Project detail with its locations |
| `/locations` | Searchable, sortable table with status chips |
| `/locations/[id]` | Full read-only profile |

## Location detail sections

**Business info** (title, categories, phone, website, description) · **Address** · **Hours** · **Attributes** · **Google status** (Voice of Merchant, pending edits, suggested updates, duplicate)

## Requirements that are easy to skip

- **Hours rendering** must group periods by day and handle a `close_day` that differs from `open_day` (overnight). A naive one-row-per-weekday render will be wrong for real data.
- **"Open in Google"** via `maps_uri`, and a review-request link via `new_review_uri`, shown only when present. These exist because some actions are only possible in Google's dashboard — without them the user hits a dead end.
- **Empty fields show "Not set", never blank.** On this screen an empty field is meaningful information, not absence of information.
- No invented analytics, scores or recommendations anywhere. Render only what the API returns.

## Implementation notes

- **Hours** are grouped by `hours_type` then `open_day`. A differing `close_day` renders the closing weekday in the range; a midnight-to-midnight span renders "Open 24 hours". Regular hours list all seven days so a day with no period reads "Closed" — absence of a period is meaningful and must not render as blank.
- **New project from an existing connection** reads the organization's already-imported locations and posts `location_ids`. No Google round-trip. With nothing imported it explains why and links to `/settings/integrations` instead of dead-ending, and still allows the project to be created.
- The API caps a page at 200 locations, so the list views request 200 and show an honest "Showing the first 200 locations" note when the cap is hit. In-page search and sort act only on what was loaded — they do not silently imply a full-dataset search.

## Issues found and fixed during the agent's own review

- The location picker's search input suppressed its focus indicator with `focus:outline-none` — replaced with a visible focus outline.
- `/projects` could flash the wrong empty state (the "connect Google" one) when the projects query resolved before the locations query. The empty state now waits on both.

## Verification

`npm run lint` and `npx tsc --noEmit` clean across the whole frontend after merge.

**Not verified:** never opened in a browser. Needs a visual pass at desktop and 400px in both themes.
