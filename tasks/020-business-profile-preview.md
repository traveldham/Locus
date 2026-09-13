# Google-style location preview

Scope: approved by the user; extend location detail without replacing its management tools.

Status: shipped. Independent bounded desktop/mobile finish review returned **ship**,
with no material issues. Nonblocking follow-ups: singular video-count wording and gray
inactive section labels (active section remains indicated by its blue underline).

## Direction contract

THESIS: Let an operator read the stored profile in the familiar search business-panel
hierarchy, then identify work in a separate operator-only column.

OWN-WORLD: User clarified that the panel must not inherit Locus branding. Scope a
white Google-style surface, Google Sans headings/controls, Arial body, blue actions,
gold stars and gray dividers to the preview only. The rest of the app retains its theme.
No Google logo or assertion that this is Google's actual rendering.

STORY: Open a location, inspect identity/contact/hours, explore reviews and updates,
then switch to management or the location's existing audit.

FIRST VIEWPORT: Large business name, aggregate rating, category, contact actions and
Overview/Reviews/Updates/About navigation. Honest media-availability area, no stock clinic
photo. A narrower adjacent operator panel points to evidence-backed recommendations.

FORM: User-pinned Google-style panel inside the existing location detail. Local extension,
code-led; no concept seed needed. Operate mode, responsive single column on mobile.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review,
the verdict, DESIGN.md, and every shipping raster carrying its provenance.

Constraints: sample locations must never generate real Google business lookups; no new
map API, invented imagery, fabricated booking link, public writes or live open-now claim.
Ratings use all valid stored reviews, with that scope visible. Explicit false attributes
remain distinct from missing values. Existing edit workflow stays intact.

## Implementation and verification

- Default preview on location details; management and approved edit flows retained.
- `GET /api/v1/reviews/summary` calculates rating/count across the entire stored review
  collection. Reviews and updates use paginated existing APIs; all supplied attributes
  and replies are inspectable. No migrations or seed writes.
- Google style is scoped to `google-profile.module.css`; surrounding shell and audit
  column retain their existing brand. Google Sans is locally hosted with OFL/provenance.
- Verified 11 review tests (including >200 reviews, changed ratings, empty results,
  unauthorized and cross-tenant access), targeted ruff, frontend TypeScript, ESLint and
  production build. Browser exercised Overview/Reviews/Updates/About, review page 2 and
  management switch. No uncaught page errors. Google Sans loaded, heading weight 400,
  active action color rgb(25,103,210) verified from computed styles.
- Desktop/mobile captures: `.impeccable/review/profile-preview/`. Media is an honest
  placeholder because assets are absent; no real business lookup or invented map.
- Visual resemblance is intentionally Google-style, not a pixel-exact claim across all
  Google Search devices/experiments. Global product/design documents have pre-existing
  historical scope drift; this local feature does not redefine the rest of the app.
