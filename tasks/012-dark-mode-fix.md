# 012 — Dark mode was never actually working

**Status:** FIXED

## What was wrong

`src/app/css/dark.css` defines every dark token under `[data-theme="dark"]`.

Nothing ever set `data-theme`.

`ThemeProvider` in `src/app/layout.tsx` was mounted without an `attribute` prop, and next-themes defaults to `attribute="class"` — so it was putting `class="dark"` on `<html>` while the stylesheet was waiting for `data-theme="dark"`. The two never met, so **the entire dark palette was dead code**. Toggling the theme changed nothing.

This predates all of the Business Profile work; it came in with the template adaptation.

## Fix

1. `layout.tsx` — `<ThemeProvider attribute="data-theme" …>`, so next-themes writes the attribute the CSS actually keys on.
2. `globals.css` — added a custom variant so `dark:` utilities follow the app's theme rather than the operating system:
   ```css
   @custom-variant dark (&:where([data-theme="dark"], [data-theme="dark"] *));
   ```
   Tailwind v4's built-in `dark:` keys off `prefers-color-scheme`, which would ignore the in-app toggle — a user switching the app to dark on a light OS would get half a theme.

## Related: the brand logo on permanently dark surfaces

The brand assets are dark-on-transparent, so they need inverting on any dark surface.

But the **sidebar is dark in both themes**. A `dark:`-conditional inversion leaves the logo invisible there whenever the app is in light mode — which is exactly the bug originally reported for the collapsed sidebar icon.

So `BrandLogo` / `BrandMark` now take an `onDark` prop:

| Surface | Treatment |
|---|---|
| Sidebar (dark in both themes) | `onDark` → always inverted |
| Header, auth form side (follow the theme) | `dark:` conditional |
| Auth panel (always maroon) | always inverted |

## Correction to an earlier claim

Task 006 recorded that the `cyan` / `sky` / `violet` / `purple` / `pink` / `rose` badge tokens were missing from `dark.css`. **That was wrong.** All 11 badge colours have full three-token parity between `default.css` and `dark.css`, verified by counting both files. The claim was an inference by one agent that got repeated into later briefs. It caused no bug — the palette was merely kept smaller than necessary — but it should not be repeated as fact.

## Verification

`npx tsc --noEmit` and `npm run lint` clean.

**Not verified:** the theme toggle has not been exercised in a browser. This needs a visual pass in both themes — it is the single highest-value thing to look at first, since this surface has never once rendered correctly in dark.
