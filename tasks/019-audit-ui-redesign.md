# Audit experience redesign

Scope: `/recommendations` and all location audit screens. Mode: Operate.

The user explicitly requested implementation with sub-agents: understandable audit
progress, useful category visualizations, clear current state and recommendations,
and purposeful animation. Preserve the existing Locus visual system and real report
contracts. This is an audit feature redesign inside the established application.

## Direction contract

THESIS: Make the audit a readable diagnosis and action plan. Customers should know
what is being reviewed, what the saved evidence says, and what to do next.

OWN-WORLD: Inherit the application's typography, semantic light/dark colors,
restrained brand accent, 12–16px surfaces, and maintained controls. Use status color
with explicit labels; give comparison charts meaningful scales and dates.

STORY: Start or refresh one location's audit, follow six named review areas, then
read overall findings, explore an area, and review evidence and optional AI drafts.

FIRST VIEWPORT: Location and primary audit action lead; active progress explains
the current stage without worker jargon. Results lead with interpretation and
evidence coverage, followed by comparable category status and prioritized actions.

FORM: Customer-facing operational report within the existing brand. The user's
specified six-category workflow defines structure; no replacement brand world.

MOTION: Animate only real state transitions: active review indicator, progress
changes and disclosure/navigation feedback. Honor reduced motion; no fake timers,
estimated uplift or celebration unrelated to an actual outcome.

FINISH: Verify types, lint, build and relevant pipeline tests; independent code
review and document the resulting UI. Browser screenshots depend on an available
supported browser connection; do not start user-managed servers.

## Verification and handoff

Pending implementation and verification.
