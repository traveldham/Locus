# Provenance

Two different questions, two different fields. Confusing them is the fastest way to make the
product lie about where a number came from.

## `DataSource` — where the row's data originates, permanently

```python
class DataSource(StrEnum):
    google = "google"
    locus  = "locus"
```

This is **not** the "is it sample data yet?" question — that one disappears the day Google
approves the app. This one never changes.

Four of our datasets have **no Google API behind them and never will**: tracked keywords,
weekly ranks, competitor observations and individual booking requests. Google publishes no
ranking API, never discloses a competitor's profile, the keyword list is our own
configuration, and Google's performance API reports a bookings *count* and nothing else. Those
four are written `locus` from the moment they are created, at the database level, and the API
reports it.

| Table | `source` | Why |
| --- | --- | --- |
| `performance_daily` | `google` | Google's performance API |
| `search_terms_monthly` | `google` | Google's search terms report |
| `media_summary` | `google` | Derived from Google's media list |
| `posts` | `google` | Google Business Profile posts |
| `tracked_keywords` | `locus` | Our own configuration |
| `keyword_ranks` | `locus` | Our own tracker — no Google ranking API exists |
| `competitor_observations` | `locus` | Google never discloses a rival's profile |
| `bookings` | `locus` | Only the customer's booking system has these |

The UI renders **whatever the row says** rather than hardcoding a list of tables, so the mark
cannot drift away from the data. `SourceMark` is the badge component.

### The consequence people ask about

`performance_daily.bookings` and the `bookings` table **will not agree**, and nothing tries to
reconcile them. One is Google's attributed count; the other is individual CRM records. There
is no join, no foreign key and no reconciliation code. The provenance mark is what makes that
legible instead of alarming.

The audit encodes the same caution: `google_bookings_untracked` fires when Google reports zero
bookings across a window while the CRM holds requests, and its limitation says outright that
Google only counts Reserve with Google bookings and the two numbers never reconcile.

## `LocationSource` — how this profile got here

```python
class LocationSource(StrEnum):
    google  = "google"    # synced from a live Google connection
    fixture = "fixture"   # the sample dataset, while API access is unapproved
    manual  = "manual"    # entered by hand
```

This one *is* temporary, and it is what the "Sample data" affordances key off.

Everywhere a `fixture` profile appears, the UI says so: a chip on every row in the profiles
table, a notice above the list, "Synthetic sample data" on the Google-style preview — and the
preview **suppresses the Directions link**, because a link that cannot work is worse than no
link.

`SampleGbpProvider.location_source` is `fixture`, and the seed stamps it onto every location
it writes. The demo-profile generator does the same.

It changes one audit rule: `address_incomplete` requires a street line only on
Google-sourced profiles, because the sample export never carries one. Inventing a street would
make the finding lie.

## `booking_source` — a third thing entirely

`Booking.booking_source` is `website | google_profile | phone | walk_in`: **how the customer
reached us**. It is named `booking_source` specifically so it cannot be confused with
`source`, which answers where the row itself came from. The sample CSV's column is called
`source`, and the loader reads it into `booking_source` while writing `source = locus`.

## Confidence, which is not provenance

A finding's `confidence` is `high` or `medium`, and it describes the **evidence**, never the
likely success of the fix:

- `high` — "Directly observed in stored records; outcome is not predicted."
- `medium` — "A descriptive pattern supports investigation, not a causal claim."

So `phone_missing` is high (the column is empty; that is a fact) while
`reviews_few_vs_competitors` is medium (stored reviews and a scraped competitor figure are not
measured the same way). Every finding also carries a `limitation` sentence naming what it
cannot tell you.

## The rule for new data

Before adding a table, answer: *could Google ever supply this?* If not, it is `locus` from day
one, at the database default, and the screen that shows it says so.
