# Locus Intelligence frontend

The authenticated web application for Locus Intelligence, built with Next.js, React, TypeScript, and Tailwind CSS.

## Local development

1. Copy `.env.example` to `.env.local` and adjust the FastAPI URL if needed.
2. Install the locked dependencies with `npm ci`.
3. Start the app with `npm run dev`.

The frontend expects these API endpoints under `NEXT_PUBLIC_API_URL`:

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`

Login and registration return an `access_token`. Refresh/logout may use an HTTP-only cookie; all API requests include credentials.

## Checks

Run `npm run lint` and `npm run build` before handing off changes.
