# Locus Workspace Memory

Last updated: 2026-09-12

## Workspace structure

- `frontend/`: existing NextAdmin v2 template using Next.js 16, React 19, TypeScript, Tailwind CSS 4, Tailgrids components, TanStack Query/Table, Recharts, and mock API patterns.
- `backend/`: currently empty; reserved for the FastAPI application.
- `locus-intelligence-assignment/`: assignment documentation and the 14 supplied CSV datasets.

## Objective

Build a location-intelligence prototype for the supplied Brightpath Dental synthetic dataset. The system must produce defensible, evidence-backed recommendations for an individual location and real output covering all 12 locations.

## Required deliverables

- Generated recommendation output for all 12 locations.
- The code that produced the output, with concise run instructions.
- `locus-intelligence-assignment/NOTES.md`, no longer than two pages, explaining the decision system, trust boundaries, omissions and next steps, and unreliable or ambiguous data.
- A small web UI is recommended but not mandatory.

## Current state

- The assignment documentation and data are present in `locus-intelligence-assignment/`.
- A Next.js admin template is present in `frontend/`; adapt it rather than replacing or redesigning it from scratch.
- `backend/` is empty.
- The user selected a foundation-first implementation approach.
- No recommendation engine or final output has been created yet.

## Established constraints

- Read `locus-intelligence-assignment/DATA.md` before interpreting columns.
- Recommendations must be location-specific, actionable, prioritized, and directly traceable to dataset evidence.
- The dataset is synthetic; do not research a real-world business matching its name.
- If an LLM is used, document exactly what the LLM decides and what deterministic code decides.
- Preserve real generated output because reviewers will inspect the output and code rather than run the prototype.

## Decisions

- Workspace-wide durable instructions live in `/AGENTS.md` at the `Locus` root.
- Evolving project context and handoff information live in `/PROJECT_MEMORY.md` at the `Locus` root.
- The assignment is a decision-support system, not merely a dashboard: for a selected clinic, it must prioritize what should be done next and explain the supporting evidence.
- A strong solution should combine deterministic metrics and scoring with an inspectable presentation layer. An LLM is optional and must not invent evidence or own opaque numerical decisions.
- The recommended product shape is a small location-selector web UI backed by a reproducible analysis pipeline and committed machine-readable output for all 12 clinics.
- Foundation-first sequence: establish FastAPI, PostgreSQL with SQLAlchemy, Alembic migrations, a basic authentication/session contract, the frontend API client, and a protected application shell before implementing intelligence features.
- Do not spend the foundation milestone on recommendation scoring, CSV ingestion, analytics dashboards, or extensive visual customization.

## Next steps

1. Inventory and profile every supplied data file.
2. Identify reliable join keys, time ranges, missing values, and ambiguous fields.
3. Define a transparent scoring and prioritization framework.
4. Generate and validate recommendations across all 12 locations.
5. Build the selected presentation layer and complete `NOTES.md`.

## Handoff log

- 2026-09-12: Inspected Codex memory behavior. Global durable Codex memory contained zero extracted entries.
- 2026-09-12: Created repository-owned agent instructions and project memory, then moved them to the `Locus` workspace root at the user's request.
- 2026-09-12: Analyzed `README.md`, `DATA.md`, and all 14 supplied CSV files. Confirmed that the core deliverable is an evidence-backed, prioritized recommendation engine covering all 12 clinics, plus readable generated output, source code and run instructions, and a maximum-two-page `NOTES.md`.
- 2026-09-12: Inspected the added `frontend/` NextAdmin template and confirmed `backend/` is empty. User chose FastAPI, SQL ORM/Alembic, basic authentication, and frontend integration as the first foundation milestone.
