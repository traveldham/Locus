# Demo profiles API

Code: `backend/app/api/demo_profiles.py`. Scoped with `CurrentUser`, `DbSession` and
`OrganizationId` like every other router — another tenant sees nothing.

## Catalogue

```
GET /api/v1/demo-profiles
```

```json
{"items": [
  {"key": "riverside-grill",
   "name": "Riverside Grill",
   "industry": "Restaurant",
   "city": "Austin, TX",
   "headline_problem": "Rating down to 2.7, 40+ complaints unanswered, no hours posted",
   "expected_grade": "poor",
   "imported": false,
   "location_id": null}
]}
```

`imported` and `location_id` reflect **what this organization already has**, so the picker can
disable what is already in.

## Import

```
POST /api/v1/demo-profiles/import
{"keys": ["riverside-grill", "bluebird-coffee"], "project_id": "<uuid>" | null}
```

```json
201
{"imported": [{"key": "riverside-grill", "location_id": "8f3c…"},
              {"key": "bluebird-coffee",  "location_id": "a91b…"}],
 "skipped":  ["already-imported-key"],
 "unknown":  ["key-that-does-not-exist"]}
```

The response is **keyed**, so the UI can name each new profile and link it to its own audit;
a count is `.length`.

### Rules

- **Idempotent.** A key this organization already holds is reported in `skipped`, never
  duplicated.
- **An unknown key does not fail the batch.** The valid keys import and the rest come back in
  `unknown` — one stale key from an out-of-date picker must not stop "select all".
- Only a structurally invalid request is a **422**: an empty `keys` list, more than 50 keys,
  or an unknown body field (`extra="forbid"`).
- `project_id` is validated against the caller's organization; another tenant's project is a
  **404**, exactly like everywhere else.
- **Importing never runs an audit.** The user triggers that themselves afterwards.

### Project scope

The dashboard is project-scoped, so a profile that belongs to no project would appear in
neither the profiles list nor the audit directory.

- With `project_id`, every imported profile is linked to that project.
- Without it, each archetype gets **its own project**, carrying its service list — which the
  relevance checks and the suggestion prompts read.

Either way a profile is never left project-less.
