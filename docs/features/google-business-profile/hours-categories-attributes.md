# Hours, categories and attributes

The three child collections of a location. Each has rules that are easy to get wrong.

## Hours

`location_hours_periods`, one row per opening period.

```
hours_type   "REGULAR" by default
open_day     MONDAY … SUNDAY
open_hour    0-23        open_minute   0-59
close_day    MONDAY … SUNDAY
close_hour   0-24        close_minute  0-59
```

**Periods are never collapsed to one row per weekday.** Google allows several periods in a
day (a lunch break is two periods) and overnight spans (`open_day != close_day`), so the
model keeps them as they come.

Rules worth knowing:

- **No hours at all is not the same as closed every day.** A profile with no regular week is
  "not set", which is a different instruction to Google. The edit form encodes this: it only
  sends `hours_periods` when the profile *had* regular hours or the operator entered some.
- **`24:00` is legal on close only.** Google writes a period ending at midnight as `24:00`,
  so `close_hour = 24` is accepted — and only with `close_minute = 0`.
- **An overnight span is valid.** Validation only requires close > open when the two days are
  the same.
- Sending `hours_periods` **replaces the whole regular schedule**. Non-regular sets (special
  hours, if they ever arrive) survive, because `apply_locally` deletes only `REGULAR` rows.
- Validation stops at the first bad period, so at most one message appears under
  `hours_periods`.

In the sample dataset, one CSV row per weekday becomes one period with
`open_day == close_day`. A row with blank or unparseable times produces **no period** — which
is how a closed day is represented.

`HoursPeriodInput` has no `hours_type` field and does not forbid extra keys, so a client that
sends one has it silently dropped and the period is planned as regular.

## Categories

`location_categories`: `category_name` (Google's `gcid:` id), `display_name`, `is_primary`.

- `Location.primary_category_name` / `primary_category_display` denormalise the primary one,
  because almost every read wants it and almost none want the list.
- The audit's attribute catalog is filtered by `primary_category_display`, casefolded — which
  is why a new business category needs its own catalog rows.
- **Only the primary category is editable.** `plan_edit` writes `is_primary=True` and nothing
  else; secondary categories are not in `EDITABLE_FIELDS`. `apply_locally` mutates the
  existing primary row or appends one.
- A category is compared on `category_name` only. The display name is Google's own rendering,
  so a differing label alone is not a change worth sending.

## Attributes

Two tables, and the distinction between them is the point.

**`attribute_catalog_items`** — the menu. What Google *offers* for a business category,
organization-wide, unique on `(organization_id, external_attribute_id)`:

```
external_attribute_id   attr_01
attribute_name          wheelchair_accessible_entrance
attribute_group         accessibility | payments | services | amenities | planning | identity
applies_to_category     Dentist
value_type              bool
```

**`location_attribute_values`** — what one location has actually *set*, unique on
`(location_id, attribute_id)`:

```
attribute_id   "attributes/wheelchair_accessible_entrance"    ← the name behind a prefix
value_type     BOOL | ENUM | REPEATED_ENUM | URL
values         JSON — typed, so not a scalar string
```

Note the id shapes differ: the catalog holds a bare `attribute_name`, the value row holds
`attributes/<attribute_name>`. Anything resolving between them has to strip the prefix — the
audit worker does it in `attribute_name()`, and the agent does it when applying a drafted
attributes map.

### Three states, not two

| State | Stored as | Means |
| --- | --- | --- |
| yes | a row with `[true]` | Answered, affirmative |
| no | a row with `[false]` | **Answered**, negative |
| unknown | **no row at all** | Never filled in |

An attribute set to `FALSE` and an attribute never filled in are different things, and the
audit treats them differently: `attributes_sparse` counts an explicit no as *answered*, while
`accessibility_unanswered` fires only on the missing row. Never infer a service exists, and
never mark one the location does not offer.

### Editing them

- Attributes **merge**, they do not replace. Only attributes whose `(value_type, values)`
  genuinely differ are sent, because `attributeMask` names exactly the ones written and the
  rest survive untouched.
- **An attribute cannot be deleted** through this path, only set or changed.
- The web edit form does not send attributes at all. The only caller is the audit's
  suggestion panel — which applies them **without a preview step**.
- In the sample loader, an `attribute_id` with no catalog entry is skipped entirely: an
  attribute with no type cannot be sent.

## Related

- [editing-a-profile.md](editing-a-profile.md)
- [../audit-engine/categories/profile.md](../audit-engine/categories/profile.md) — the checks that read all three
