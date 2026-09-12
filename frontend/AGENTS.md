# Locus Intelligence frontend instructions

This directory contains the authenticated Locus Intelligence web application.

## Product boundaries

- Keep the current milestone focused on authentication, organization context, and the protected application shell.
- Do not present invented analytics, recommendations, location counts, customer outcomes, or integration status.
- Preserve the typed API contract in `src/services/api/` and authentication state in `src/contexts/`.
- Store public first-party brand assets in `public/brand/`; never depend on the marketing site at runtime.

## Implementation conventions

- Use the Next.js App Router and keep authenticated routes under `(with-layouts)`.
- Prefer Server Components unless hooks, event handlers, or browser APIs require `"use client"`.
- Use semantic Tailwind tokens from `src/app/globals.css`; keep light and dark themes accessible.
- Reuse maintained primitives in `src/components/tailgrids/core/` before adding another component library.
- Keep interactive targets at least 44 by 44 pixels, keyboard reachable, and visibly focused.
- Use clear labels, semantic form errors, and product-specific copy.
- Keep components focused and type external data boundaries.

## Maintenance and verification

- Remove demo routes, mock data, and dependencies that are not part of the active product.
- Preserve unrelated user changes.
- Run `npm run lint` and `npm run build` after frontend changes.
