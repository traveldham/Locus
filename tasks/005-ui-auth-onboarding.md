# 005 — Auth + onboarding UI

**Status:** BUILT (unverified in a browser)

## Goal

"Continue with Google" on both auth pages, the OAuth return page, and the organization-naming screen a brand-new Google user lands on.

## Screens

| Route | Purpose |
|---|---|
| `/login`, `/register` | Google button above the email form, with a divider |
| `/auth/callback` | Reads `status` from the redirect: `success` → dashboard, `onboarding` → `/onboarding`, `error` → message + "Try again" |
| `/onboarding` | One question: what is your organization called |

## Notes

- The Google button uses an **inline** four-colour `G` SVG. No remote image, no icon CDN — an external request here would be blocked or slow and the mark must render offline.
- A caption under the button states that Google is only confirming identity, and that connecting a Business Profile is a separate step. The scope separation is surfaced to the user rather than hidden.
- `AuthGuard` redirects a signed-in user with zero organizations to `/onboarding` instead of rendering an empty workspace.
- `/auth/callback` is excluded from the auth provider's automatic session load so the page owns the single refresh call. Two concurrent calls against a rotating refresh token would invalidate each other.
- Validation is attached to the field via `FieldError` with `validationBehavior="aria"`, so no native browser bubble appears.
- The error `message` param is truncated and rendered as text, never as markup.

## Verification

`npm run lint` and `npx tsc --noEmit` both clean.

**Not verified:** never opened in a browser — no dev server is started in this project by agreement. Needs a visual pass at desktop and 400px, in light and dark themes, plus a real Google consent round-trip.
