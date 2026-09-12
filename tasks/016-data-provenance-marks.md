# 016 — Data provenance marks

**Status:** PLANNED (Wave 2)

## The rule

Every piece of business data carries a mark showing **where it comes from**.

| Mark | Source | Data |
|---|---|---|
| Google **G** | Google Business Profile API | locations, hours, attributes, categories, reviews, replies, posts, photos, performance, search terms |
| Locus favicon | Locus itself — not Google | competitors, keyword rankings, tracked keywords, bookings |

## Why this exists

Google does **not** provide four of the things this product shows:

- **Competitor data** — Google never tells you about a rival's profile
- **Keyword rankings / local pack position** — no ranking API exists
- **Tracked keywords** — that is our own configuration
- **Bookings** — Google gives only an aggregate count, never individual records

In a real product these come from paid SEO providers and the customer's CRM.

Without a mark, a user reasonably assumes everything on the screen came from Google. That is a quiet lie, and it becomes a loud one the day someone asks "why doesn't this match my Google dashboard?" — because for those four, it never will.

The mark makes provenance visible without a paragraph of explanation.

## Distinct from the sample-data label

Two different questions, two different indicators. Do not merge them:

| Question | Indicator |
|---|---|
| Is this real yet? | "Sample data" chip — disappears when Google approves and live data flows |
| Where would this come from? | Google mark / Locus mark — **permanent**, true forever |

A location today carries both: "Sample data" *and* the Google mark. After approval it keeps the Google mark and loses the sample chip. A competitor row carries the Locus mark permanently, because that is simply where competitor data comes from.

## Implementation

- One small `SourceMark` component. Two variants, nothing more.
- Locus variant uses the existing `/brand/favicon.webp`. Note it is a dark maroon glyph on transparent, so it needs inverting on dark surfaces — see the `onDark` handling in `brand-logo.tsx`.
- Shown on section headers (Competitors, Rankings, Bookings) rather than repeated on every row, so it informs without becoming visual noise.
- An accessible label on each — never icon alone.

## Storage

Mark source at the data layer, not just in the UI, so it cannot drift. Rows that can never come from Google are stored as Locus-sourced from the moment they are written, and the API returns that. The UI renders what the data says rather than hardcoding which table is which.
