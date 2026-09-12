# 002 — Google sign-in + onboarding API

**Status:** BUILT (unverified end to end)

## Goal

Let a user sign in with Google, and give a brand-new account a way to name its organization.

## Why sign-in does NOT request Business Profile access

Sign-in asks only for `openid email profile`.

`business.manage` is a Google-restricted scope requiring app verification. If it were bundled into the sign-in button, **nobody could log in at all** until Google approved the app. Business Profile access is therefore a separate, later consent (task 003), using incremental authorization so it stacks on the same Google identity.

Do not "simplify" these into one button.

## Endpoints

| Method | Path | Returns |
|---|---|---|
| GET | `/api/v1/auth/google/authorize` | `{ authorization_url }`, or 503 if credentials are unconfigured |
| GET | `/api/v1/auth/google/callback` | **302** to `{frontend}/auth/callback?status=success\|onboarding\|error` |
| POST | `/api/v1/onboarding/organization` | `TokenResponse` — 409 if the user already has an organization |

The callback returns a redirect, not JSON — the browser arrives there directly from Google.

## User resolution order

1. `UserIdentity` matching the Google `sub` → that user.
2. Otherwise a `User` with that email → **link** a new identity to it. This is the account-linking case: someone registered with a password and later signs in with Google. Creating a second user here would be a real bug.
3. Otherwise create a user with `password_hash = None`.

## Security

- State is validated through `consume_state(state, "google_signin")`; a bad, expired or wrong-purpose state produces an error redirect.
- The `id_token` is verified against Google's JWKS with audience and issuer checked.
- **An unverified `email_verified` claim is rejected** — otherwise someone could claim an existing account by asserting its email address.
- Inactive users are refused.
- The refresh cookie is set on the `RedirectResponse` itself, so it actually reaches the browser with the 302.

## Verification

7 tests in `backend/tests/test_google_auth.py`, all Google network calls monkeypatched (never hits the real Google): scope contents and absence of `business.manage`, the 503 path, bad/wrong-purpose state, `error=access_denied`, unverified email rejection, new user → `onboarding` with a null password hash, password-account linking leaving exactly one user row, returning user → `success`, and onboarding create / 409 / 422 / 401.

**Not verified:** no real round-trip through Google's consent screen has been performed. That needs the redirect URIs registered in Google Cloud Console.
