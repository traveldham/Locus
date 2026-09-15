# Tenancy and authentication

## There is no registration

The application ships **one pre-seeded account**. There is no sign-up endpoint, no
password-reset flow and no SSO route anywhere. `app/seed.py` writes the single user, its
organization and its Google connection; `POST /auth/login` is the only way in.

The OAuth flows and the live Google API client were removed when the Cloud project was not
approved, which is why `AuthProvider.google` and the `user_identities` table exist in the
schema but nothing writes them.

## The four endpoints

| Method | Path | Auth | Returns |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/login` | none | `TokenResponse` |
| `POST` | `/api/v1/auth/refresh` | refresh cookie | `TokenResponse` |
| `POST` | `/api/v1/auth/logout` | none | `{"message": "Signed out"}` |
| `GET` | `/api/v1/auth/me` | bearer | `UserResponse` with organizations |

`login` rejects with `401 "Invalid email or password"` when the user is missing, has no
password hash, or the password fails; and `403 "Account is inactive"` when `is_active` is
false.

## Two tokens, two mechanisms

**Access token** — a JWT, `HS256`, signed with `SECRET_KEY`. Claims are `sub` (user id),
`"type": "access"`, a random `jti`, `iat` and `exp`. Lifetime `ACCESS_TOKEN_MINUTES`,
**default 15**. Sent as `Authorization: Bearer`. `decode_access_token` rejects a token whose
`type` is anything but `access`.

**Refresh token** — **not** a JWT. `secrets.token_urlsafe(48)`, and only its SHA-256 digest is
stored, in `refresh_sessions.token_digest`. Lifetime `REFRESH_TOKEN_DAYS`, **default 30**. It
travels as an HTTP-only cookie:

```
name      locus_refresh
httponly  true
secure    COOKIE_SECURE            ← must be true behind HTTPS
samesite  lax
path      /api/v1/auth             ← sent to no other route
max_age   REFRESH_TOKEN_DAYS × 86400
```

**Refresh rotates.** The old session is marked `revoked_at` and a brand-new one is issued, so
a stolen refresh token is usable at most once before the real user's next refresh invalidates
it.

Passwords are hashed with `PasswordHash.recommended()` from `pwdlib` — Argon2.

## Organization scoping

```python
OrganizationId = Annotated[UUID, Depends(get_organization_id)]
```

`get_organization_id` selects the caller's **first membership**, ordered by
`(created_at, id)`. There is no header, path parameter or token claim for organization
selection — a multi-organization user always resolves to their oldest membership.

A user in no organization gets **`400 "User does not belong to an organization"`**.

Every tenant-scoped query hangs off this dependency. `project_locations` validates a project
against the organization *before* building its subquery, so a cross-tenant project id is a
404 rather than a silent read.

## 404, never 403

Every owned-row helper filters on `organization_id` **in the same statement that fetches the
row**:

```python
select(Location).where(Location.id == location_id,
                       Location.organization_id == organization_id)
```

A miss raises `404 "Location not found"`. "Not yours" and "not there" are indistinguishable
from outside, so an attacker cannot enumerate ids.

## On the browser

Client-side only. There is **no `middleware.ts`**, so nothing is protected at the edge.

- The access token lives in `localStorage` under `locus_access_token` and is injected as a
  bearer header by `services/api/client.ts`.
- Every request carries `credentials: "include"` so the refresh cookie travels.
- A `401` triggers **one** refresh and **one** replay — except on `/auth/refresh` and
  `/auth/login` themselves. Concurrent refreshes are de-duplicated by a module-level promise.
- `AuthGuard` wraps the whole authenticated tree; while loading it shows "Opening your
  workspace…", and once loading finishes with no user it redirects to
  `/login?next=<encoded path>`.
- `activeOrganization` is simply `user.organizations[0]` — there is no organization picker.

## The demo account

Seeded by `app/seed.py`, printed on the sign-in page and prefilled into the form:

```
pawanpatrapp@gmail.com  /  Pawan 2000
```

Sign-in still goes through the real `POST /auth/login`.

## Project scope is separate

Tenancy is the organization. **Project** scope is a UI concept layered on top:
`?project=` in the URL is the source of truth, `localStorage` (`locus.active-project`) only
seeds it on first load, and a remembered id is honoured only while it is still in the list.
Most data hooks pass the active project id down as a filter.
