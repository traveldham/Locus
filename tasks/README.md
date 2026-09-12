# Task Documentation

Working record of what is being built, why, and how to verify it.

## Files

| File | What it holds |
|---|---|
| `STATUS.md` | The live board. What is done, in flight, and blocked. Update this first. |
| `ARCHITECTURE.md` | How the system fits together, and the decisions that shaped it. |
| `ROADMAP.md` | Every step of the end-to-end build, in order, with what each depends on. |
| `NNN-*.md` | One file per task: goal, scope, files touched, contract, verification. |

## Conventions

- One task file per unit of work, numbered in the order the work was started.
- A task file is written **when the task starts**, not after — it is the brief, and the result is appended to it.
- Every task states how to verify it. "It compiles" is not verification.
- Record the gotchas that cost time. That is the highest-value part of these files.
- Status vocabulary: `PLANNED` · `IN PROGRESS` · `BUILT (unverified)` · `DONE` · `BLOCKED`.

`BUILT (unverified)` means the code exists and its own checks pass, but it has not been exercised against a running system. Most of this project sits there until the Google API access is approved — that is expected, not a defect.

## Related documents

- `../PRODUCT.md` — product definition
- `../PROJECT_MEMORY.md` — long-running handoff record
- `../researched/` — the GBP API research this build is based on
