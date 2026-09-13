# Profile worker: data inventory

Research note, 2026-09-13. What the `profile` worker can see, compute today, needs, and where the
data misleads. Sources: models, `snapshot.py`/`contracts.py`, the fixture loader
(`providers/sample_data.py`, `sample_datasets.py`), the 12-location CSVs, and the GBP API note.

## 0. What reaches the worker

`prepare_job` serialises every column of each table in `contracts.TABLES` except `EXCLUDED`
(`organization_id`, `connection_id`, `external_account_id`, `created_at`, `updated_at`, plus
reviewer/customer identity). Dates, UUIDs and enums become strings. The worker gets
`c.location` (the one `locations` row as a dict) and `c.rows("hours" | "categories" |
"attributes" | "media" | "posts")`, each filtered by `location_id == c.location["id"]`.

**`c.rows("catalog")` returns nothing.** Catalog rows have no `location_id`; read
`c.snapshot["catalog"]` directly. Nothing else in the snapshot is profile data.

## 1. Columns available to the profile worker

Distribution column = what the 12 fixture locations look like after `sample_data.py` maps the CSV.

### `locations` (one row)

| Column | Type | Null | Meaning | Fixture distribution (n=12) |
| --- | --- | --- | --- | --- |
| `id` | UUID | no | Row id, evidence key | 12 distinct |
| `google_location_name` | str(255) | no | `locations/{id}` | 12/12 |
| `source_location_id` | str(64) | yes | CSV `LOC-001` | 12/12 |
| `google_resource_name` | str(255) | yes | `accounts/…/locations/…` | 12/12 (synthesised) |
| `place_id` | str(255) | yes | Google `metadata.placeId` | **never set by fixture** |
| `store_code` | str(128) | yes | `storeCode` | 12/12 |
| `title` | str(320) | no | `title` | 12/12, all `Brightpath Dental — <area>` |
| `primary_category_name` | str(255) | yes | `categories/gcid:dentist` (slug synthesised) | 12/12, one value |
| `primary_category_display` | str(255) | yes | `Dentist` | 12/12 |
| `address_lines` | JSON list | yes | `storefrontAddress.addressLines` | **never set** (CSV has no street) |
| `locality` | str(160) | yes | city | 12/12, 11 distinct |
| `administrative_area` | str(160) | yes | state | 12/12 (TX ×9, AZ ×3) |
| `postal_code` | str(32) | yes | postal code | 12/12 |
| `region_code` | str(8) | yes | country | 12/12, hard-coded `US` |
| `latitude` / `longitude` | float | yes | `latlng` (Google: not always returned) | 12/12 |
| `phone_primary` | str(64) | yes | `phoneNumbers.primaryPhone` | 12/12, all `+1-xxx-555-01xx` |
| `website_uri` | str(1024) | yes | `websiteUri` | **11/12** (LOC-003 null) |
| `description` | Text | yes | `profile.description` | **11/12** (LOC-003 null); lengths 31–497 |
| `open_status` | enum open/closed_temporarily/closed_permanently | yes | `openInfo.status` | 12/12 `open` |
| `opening_date` | date | yes | `openInfo.openingDate` | 12/12, 2014-05-12 … 2025-11-03 |
| `has_voice_of_merchant` | bool | no (default False) | verified / VoM | 11 true, **LOC-009 false** |
| `has_pending_edits` | bool | no (default False) | `metadata.hasPendingEdits` | always False (never set) |
| `has_google_updated` | bool | no (default False) | `metadata.hasGoogleUpdated` | always False (never set) |
| `is_duplicate` | bool | no (default False) | `metadata.duplicateLocation` | always False (never set) |
| `maps_uri` / `new_review_uri` | str(1024) | yes | metadata URIs | never set |
| `source` | enum google/fixture/manual | no | provenance | all `fixture` |
| `last_synced_at` | datetime | yes | ingestion time | set by sync |

### `categories` (LocationCategory, 1–3 rows per location)

| Column | Type | Null | Meaning | Distribution |
| --- | --- | --- | --- | --- |
| `category_name` | str(255) | no | `categories/gcid:<slug>` | slug synthesised from display name |
| `display_name` | str(255) | yes | display text | 8 distinct additional names |
| `is_primary` | bool | no | primary flag | exactly 1 primary per location; additional: 1 (×8) or 2 (×4) |

### `hours` (LocationHoursPeriod, 5–6 rows per location)

| Column | Type | Null | Meaning | Distribution |
| --- | --- | --- | --- | --- |
| `hours_type` | str(32) | no, default `REGULAR` | REGULAR vs more-hours type | all REGULAR |
| `open_day` / `close_day` | str(16) | no | `MONDAY`… | always equal (no overnight) |
| `open_hour`, `open_minute`, `close_hour`, `close_minute` | int | no | 24h clock | 57 rows 08:00–17:00, 11 rows Sat 09:00–14:00, LOC-007 Mon/Wed 07:30–18:00, LOC-011 Fri 08:00–19:00 |

Coverage: Mon–Fri 12/12 open, Sat 11/12 (LOC-003 closed), Sun 0/12. **A closed day has no row**
(the loader drops blank CSV rows), so "no row for Sunday" and "hours never entered" look identical
at the row level; the distinction is "any rows at all".

### `attributes` (LocationAttributeValue, 9–31 rows per location)

| Column | Type | Null | Meaning | Distribution |
| --- | --- | --- | --- | --- |
| `attribute_id` | str(255) | no | `attributes/<name>` | 34 distinct |
| `value_type` | str(32) | no | `BOOL` / `ENUM` / `REPEATED_ENUM` / `URL` | 33 BOOL, 1 ENUM |
| `values` | JSON | no | typed list, e.g. `[true]` | 255 rows: 188 TRUE, 67 FALSE |

Per location: set/true/false/unset-of-34 — LOC-001 30/22/8/4, LOC-002 22/16/6/12, LOC-003
19/13/6/15, LOC-004 23/19/4/11, LOC-005 31/23/8/3, LOC-006 24/20/4/10, LOC-007 20/14/6/14,
**LOC-008 9/7/2/25**, LOC-009 15/9/6/19, LOC-010 25/20/5/9, LOC-011 26/19/7/8, **LOC-012 11/6/5/23**.
Only `free_street_parking` is set by all 12; `has_restroom` and `emergency_services` by only 5.

### `catalog` (AttributeCatalogItem, organization-wide, 34 rows)

| Column | Type | Null | Meaning |
| --- | --- | --- | --- |
| `external_attribute_id` | str(64) | no | `attr_01` … `attr_34` |
| `attribute_name` | str(255) | no | `wheelchair_accessible_entrance` |
| `attribute_group` | str(64) | no | accessibility 5, payments 5, services 8, amenities 6, planning 6, identity 4 |
| `applies_to_category` | str(255) | no | all `Dentist` |
| `value_type` | str(32) | no | lowercase `bool` (33) / `enum` (1) |

### `media` (MediaSummary, one row)

| Column | Type | Null | Distribution |
| --- | --- | --- | --- |
| `photo_count` | int | yes | 3–61; LOC-002 3, LOC-007 4, LOC-012 7 |
| `interior/exterior/team_photo_count` | int | yes | LOC-007 interior 0, team 0 |
| `video_count` | int | yes | 0 for 6 locations |
| `has_profile_photo` | bool | no, default False | 12/12 true |
| `has_cover_photo` | bool | no, default False | 6 true, 6 false |
| `last_photo_uploaded_on` | date | yes | 2025-12-04 (LOC-007) … 2026-08-29 |

`posts` (`post_type`, `summary`, `cta_type`, `published_on`) is also present but belongs to the
content worker; the profile worker should not score it.

## 2. Checks computable today

Conventions: **fail** = `triggered`; **pass** = `clear`; **abstain** = `insufficient_data`;
**suppress** = `suppressed`. Every check suppresses when `open_status == closed_permanently`.
Evidence source is the snapshot table name; `row_ids` is the `locations.id` unless stated.
Severity follows how directly Google's own "profile strength" and ranking guidance weight the
field, and how many customer actions it gates.

| Rule key | Tests | Fail | Pass | Abstain | Evidence fields | Severity |
| --- | --- | --- | --- | --- | --- | --- |
| `profile.website_missing` | A website is linked | `website_uri` null/blank | non-blank | never (null *is* the finding: fixture leaves it empty deliberately, Google omits the field when unset) | `website_uri` | critical: kills WEBSITE_CLICKS entirely. Fires on LOC-003 |
| `profile.website_not_https` | Website uses https | scheme is `http:` | `https:` | website null (covered by the check above) | `website_uri` | notice |
| `profile.phone_missing` | Primary phone set | `phone_primary` null/blank | non-blank | never | `phone_primary` | critical: gates CALL_CLICKS. Fires on none |
| `profile.description_missing` | Business description present | `description` null/blank | non-blank | never | `description` | warning. Fires on LOC-003 |
| `profile.description_short` | Description long enough to be useful | `len(description) < config.description_min_chars` (suggest 250; Google's cap is 750) | >= min | description null (other rule owns it) | `description`, `len` | warning. At 250: fires on LOC-002 (31), LOC-009 (114), LOC-011 (117), LOC-012 (67) |
| `profile.description_keyword_stuffed` | Description reads like keyword spam | primary-category word or city repeated >= `config.description_max_term_repeats` (suggest 4) | below | description null/short | `description`, term counts | notice (Google may reject; LOC-010 repeats "dentist" 5×, "Phoenix" 3×) |
| `profile.primary_category_missing` | Primary category set | no `categories` row with `is_primary` and `primary_category_name` null | one primary | never | `categories.is_primary`, `primary_category_name` | critical. Fires on none |
| `profile.secondary_categories_few` | Additional categories used | count(`is_primary=false`) < `config.min_additional_categories` (suggest 2) | >= min | no categories rows at all (sync failed, not "none set") -- but note the fixture always has >=1 row, so this abstain only guards a broken sync | `categories.*` row ids | notice. At 2: fires on 8/12 |
| `profile.address_incomplete` | Street address present | any of `locality`, `administrative_area`, `postal_code` null, **or** `address_lines` null/empty | all present | never | address columns | warning; **fires on all 12 today** because the CSV carries no street line -- see traps |
| `profile.pin_missing` | Map pin present | `latitude` or `longitude` null | both present | never; but Google may not return `latlng` for a verified listing, so severity must stay low | `latitude`, `longitude` | notice |
| `profile.hours_missing` | Regular hours entered | zero `hours` rows with `hours_type == REGULAR` | >= 1 row | never (no rows = Google `regularHours` empty) | `hours` row ids, `open_day` | critical: "Hours unknown" on Maps. Fires on none |
| `profile.hours_weekday_gaps` | Every Mon–Fri has a period | any weekday absent among REGULAR rows | all 5 present | no rows (owned by `hours_missing`) | missing `open_day` list, one finding per day (`subject`) | warning; dentists closed a weekday is plausible, so confidence "low". Fires on none |
| `profile.hours_saturday_unset` | Weekend coverage | no Saturday row **and** attribute `saturday_appointments` is `[true]` | Saturday row exists, or attribute false/unset | attribute unset (cannot tell closed from unentered) | `hours`, `attributes.saturday_appointments` | notice; consistency rule. Fires on none (LOC-003 has attr unset) |
| `profile.unverified` | Listing verified (Voice of Merchant) | `has_voice_of_merchant` is False **and** `source == google` | True | `source == fixture` or `manual`: the flag is a CSV boolean, not a Google state -- report with confidence "low" rather than abstain, since the fixture does carry it | `has_voice_of_merchant`, `source` | critical: unverified profiles cannot be edited or reply. Fires on LOC-009 |
| `profile.temporarily_closed` | Listing marked temporarily closed | `open_status == closed_temporarily` | `open` | `open_status` null | `open_status` | warning (it hides hours and suppresses in search). Fires on none |
| `profile.attributes_sparse` | Applicable attributes answered | set/catalog < `config.attribute_coverage_min` (suggest 0.5). Set = row exists, **whether true or false** | >= min | catalog empty, or `applies_to_category` never matches `primary_category_display` | `attributes` row ids, `catalog` ids, ratio | warning. At 0.5: fires on LOC-008 (9/34), LOC-009 (15/34), LOC-012 (11/34) |
| `profile.attribute_group_empty` | Each attribute group has >= 1 answer | one finding per `attribute_group` with zero rows (subject = group) | every group touched | catalog empty | group, member ids | notice. Fires on none (every location touches every group) |
| `profile.accessibility_unanswered` | Accessibility attributes answered | any of the 5 `accessibility` attributes has no row; enumerate (subject = attribute) | all 5 present (true or false both pass) | catalog lacks group | attribute ids | warning: Google surfaces "accessibility unknown" prominently. Fires on 11/12 (only LOC-001 and LOC-005 complete) |
| `profile.category_attribute_mismatch` | Additional categories are backed by the matching service attribute | pairs: Pediatric dentist→`pediatric_care`, Orthodontist→`orthodontic_care`, Dental implants periodontist→`implant_services`, Teeth whitening service→`teeth_whitening`, Emergency dental service→`emergency_services`; fail when category present and attribute row is `[false]` | attribute `[true]` | attribute row absent (unset != false) | category row id, attribute row id | notice (contradiction, not incompleteness). Fires on LOC-011 (Orthodontist + orthodontic_care FALSE) and LOC-012 (Pediatric dentist + emergency FALSE is not a pair; pediatric_care unset → abstain) |
| `profile.attribute_category_unbacked` | Service attribute true without matching category | inverse of above, e.g. `pediatric_care=[true]` and no Pediatric dentist category | — | attribute unset | same | notice; low confidence (categories are limited to what Google offers). Fires widely (e.g. LOC-001, 005, 006 pediatric true, no category) |
| `profile.logo_missing` | Profile photo / logo set | `media.has_profile_photo` False | True | no `media` row | `media.has_profile_photo` | warning. Fires on none |
| `profile.cover_photo_missing` | Cover photo set | `media.has_cover_photo` False | True | no `media` row | `media.has_cover_photo` | warning. Fires on 6/12 (002, 003, 007, 010, 011, 012) |
| `profile.opening_date_missing` | Opening date set | `opening_date` null | set | never | `opening_date` | notice (feeds "years in business"). Fires on none |
| `profile.google_pending_edits` | Edits awaiting Google review / Google-updated fields | `has_pending_edits` or `has_google_updated` True | both False | `source != google` (fixture never populates; a False here is a default, not an observation) | the two flags | notice. Cannot fire today |
| `profile.duplicate_listing` | Google flagged as duplicate | `is_duplicate` True | False | `source != google` | `is_duplicate` | critical. Cannot fire today |

Photo counts, videos, freshness (`last_photo_uploaded_on`) belong to the content worker; only the
two boolean flags above are profile-completeness.

Suggested `EngineConfig` knobs: `description_min_chars=250`, `description_max_term_repeats=4`,
`min_additional_categories=2`, `attribute_coverage_min=0.5`.

## 3. Checks needing data we do not store

| Check | Google Business Information API field | Note |
| --- | --- | --- |
| Description over Google's 750-char limit / policy rejection state | `profile.description` (already have) + validation error from PATCH | length check works today; rejection state needs write feedback |
| Special hours set for upcoming holidays | `specialHours.specialHourPeriods[]` | needs `location_special_hours` table |
| More-hours types (e.g. "Access", "Senior hours") | `moreHours[]` with `hoursTypeId`; `categories.primaryCategory.moreHoursTypes` says which apply | `hours_type` column exists but only REGULAR is ever written |
| Multiple periods per day / overnight | `regularHours.periods[]` | schema supports it; fixture never produces it |
| Service area configured (SAB) | `serviceArea.businessType`, `serviceArea.places` | no column |
| Services / service items and prices | `serviceItems[]` (`structuredServiceItem`, `freeFormServiceItem`, `price`) | no table; `metadata.canModifyServiceList` gates it |
| Messaging enabled | Not exposed in Business Information; Business Messages agent state | no API source |
| Appointment / booking link, menu link, order link | `placeActionLinks` (Place Actions API) | no table |
| Attribute catalog per country/category with enum vocabularies | `attributes.list` (`categories/gcid:dentist`, `regionCode`) with `valueMetadata` | current catalog is a flat CSV; `language_assistance` enum values unknown |
| Google-updated vs merchant values (diff) | `locations.getGoogleUpdated`, `attributes.getGoogleUpdated` | only a boolean flag is modelled |
| Verification state / pending verification | Verifications API `verifications.list`, `voiceOfMerchantState` | `has_voice_of_merchant` is the only mirror |
| Duplicate / suspended | `metadata.duplicateLocation`, `voiceOfMerchantState.hasBusinessAuthority` | flags exist but fixture never sets them |
| Profile photo/cover/logo as actual items | `media.list` with `locationAssociation.category` = PROFILE / COVER / LOGO | summary booleans only; note Google distinguishes LOGO from PROFILE |
| Street address | `storefrontAddress.addressLines` | column exists, fixture never fills it |

## 4. Traps

**Absence means unknown, not missing**
- `attributes`: no row = never answered; `[false]` = explicitly no. `SEMANTICS["attributes"]`
  says the same. Never count `[false]` as a gap, and never count "unset" as "does not offer".
- `hours`: no row for a day = closed *or* unentered. Only "no rows at all" is "hours missing".
- `latitude/longitude`: Google may withhold `latlng`; null is not "no pin".
- `has_pending_edits`, `has_google_updated`, `is_duplicate`, `has_profile_photo`,
  `has_cover_photo`: non-nullable booleans defaulting to False. On fixture data (and on a Google
  sync that never read metadata) False is a *default*, not an observation. Gate on `source`.
- `has_voice_of_merchant`: on fixture rows this is the CSV `verified` flag, which the API note
  says is "better treated as derived state". Real Google verification is a Verifications API state.
- `media` row absent entirely = no rollup taken, not zero photos.

**Synthetic-only or synthesised fields**
- `primary_category_name` and `categories.category_name` are slugs the loader invents from the
  display name (`categories/gcid:cosmetic_dentist`). They are not real GCIDs; do not compare
  against Google's category list.
- `google_resource_name` is synthesised as `accounts/1…/locations/…`.
- `region_code` is hard-coded `US`.
- `address_lines` is never populated: the CSV has no street. `profile.address_incomplete` will
  fire on all 12 until the fixture or a real sync carries a street. Either accept that (the
  loader comment says the profile "really is" incomplete) or key the check on `source == google`.
- `place_id`, `maps_uri`, `new_review_uri` are always null on fixture rows.
- Phones are all `555-01xx` test numbers; a phone-format validity check would pass them, so
  do not use the fixture to validate a format rule.

**Join hazards**
- Catalog vs attribute ids do not match directly: catalog `external_attribute_id` is `attr_01`
  and `value_type` is lowercase `bool`; the location row has `attribute_id =
  "attributes/" + catalog.attribute_name` and `value_type = "BOOL"`. Join on
  `"attributes/" + attribute_name`, and normalise type case.
- `c.rows("catalog")` filters on a `location_id` the catalog lacks, so it is always empty; use
  `c.snapshot["catalog"]`. `applies_to_category` holds the display name `Dentist`, so match it
  against `primary_category_display`, not `primary_category_name`.

**Data quality oddities in the CSVs**
- `attr_15 language_assistance` is declared `enum` in the catalog but every value is
  `TRUE`/`FALSE`. The loader stores it as `ENUM` with values `["TRUE"]`/`["FALSE"]` (strings,
  upper-cased), so a `values == [True]` test silently misses it. Treat ENUM rows as "set" only.
- `description_length` in the CSV equals `len(description)` for all 12 (verified), so it is
  safely derivable and not stored, as the model intends.
- LOC-003 has no website and no description and is closed Saturday — the one deliberately thin
  profile. LOC-009 is the one unverified. LOC-008 and LOC-012 are attribute-sparse. LOC-007's
  last photo is 2025-12-04 (content worker's problem). LOC-012 opened 2025-11-03, so "new
  location" logic (if any) should read `opening_date` against `as_of`, not assume age.
- Category/attribute contradictions exist by construction: LOC-011 lists Orthodontist yet
  `orthodontic_care = FALSE`; LOC-012 lists Pediatric dentist with `pediatric_care` unset;
  LOC-001/005/006 answer `pediatric_care = TRUE` with no pediatric category.
- All 12 share one primary category, one open status and near-identical hours, so several
  checks (`hours_missing`, `primary_category_missing`, `phone_missing`) cannot be exercised as
  failures on the fixture. Mutation tests must build their own rows.
- `open_day` is stored upper-case (`MONDAY`) by the loader while the CSV says `Monday`; any
  weekday constant in a rule must use the Google form.
