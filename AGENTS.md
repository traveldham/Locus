# Agent Instructions

These instructions apply to the entire `Locus` workspace and all projects under it.

## Start here

Before making changes:

1. Read `PROJECT_MEMORY.md` for shared context, decisions, progress, and handoff notes.
2. Identify the relevant project directory and read its documentation.
3. Inspect the working tree and preserve unrelated user changes.

For `locus-intelligence-assignment` specifically:

1. Read `locus-intelligence-assignment/README.md` for the assignment and deliverables.
2. Read `locus-intelligence-assignment/DATA.md` before interpreting any dataset field.

## Project principles

- Build recommendations that are specific, actionable, and traceable to evidence in the supplied synthetic dataset.
- Every recommendation must explain why the location, why the action, and which data supports it.
- Clearly separate deterministic analysis from any LLM-generated interpretation.
- Prefer a small, complete, inspectable system over broad unfinished functionality.
- Preserve real generated output for all 12 locations; do not leave only code that promises to generate it.
- Keep `locus-intelligence-assignment/NOTES.md` within the assignment's two-page limit.
- Do not search for a real Brightpath Dental business; the dataset is synthetic.

## Persistent workspace memory

Use `PROJECT_MEMORY.md` as the shared handoff record for future agents.

- Update it after material decisions, completed milestones, discoveries, or unresolved blockers.
- Record concise facts and decisions rather than raw chat transcripts or speculation.
- Include relevant file paths and verification commands.
- Never store passwords, API keys, access tokens, credentials, or personal/private data.
- Revise stale entries instead of allowing contradictory notes to accumulate.

## Verification

- Run the narrowest relevant checks after changes.
- Verify generated recommendations against the documented dataset fields.
- Report checks that were run and any checks that could not be run.

