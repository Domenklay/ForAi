# Deep Relationships — rebuild v0.8 (development branch)

**Not installable in The Sims 4 yet.** The old v0.7.x archives remain separate.
This directory is a new codebase; no incremental zzzz patch modules, no automatic save migration, no old hooks.

## Architecture

1. `engine/` — pure Python 3.7 code: directed story stages, moodlet diffing, event-driven stage coordinator, read-only legacy-save reader. Grievance/event mechanics still need porting.
2. `adapter/` (next milestone) — exactly one hook per EA game event, one refresh dispatcher, one event/action registry. No chained function monkey-patches.
3. `ui/` (next milestone) — Sims 4 interactions/report display, notifications.
4. `resources/` (next milestone) — validated Buff IDs/strings/icons and tuning package.
5. `tests/` — offline regressions for stages, relationships, save/load, moodlet diffing, interactions.

## Feature contract (full release, not the current prototype)

- Existing relationship progression, actions, grievance memories, jealousy, infidelity.
- Conflicts, pauses, breakups, ex-partners, reunion, forgiveness and second chances.
- Exactly one story-stage moodlet for a selected active relationship, supplementary moodlets independent.
- Ten story stages with unchanged stage labels and IDs where possible.
- No duplicate interactions or moods after zone reload.
- Read existing save data **without** deleting it and migrate only after backup.
- Logging must never drop errors or registration and add/remove results.
- One `.ts4script` and one `.package` for installation.

## Testing gate

No user-facing "complete" zip unless import graph, Python 3.7 bytecode, resource IDs,
interaction registrations, migration tests and the in-game smoke test have all passed.
Current work contains the pure stage selector, stage moodlet diff, pair coordinator, and read-only legacy reader, with offline tests. No EA adapter, interactions, gameplay persistence or installable v0.8 release yet.
