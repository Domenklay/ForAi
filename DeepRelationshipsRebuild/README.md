# Deep Relationships — rebuild v0.8 (development branch)

**Not installable in The Sims 4 yet.** The old v0.7.x archives remain separate.
This directory is a new codebase; no incremental zzzz patch modules, no automatic save migration, no old hooks.

## Architecture

1. `engine/` — pure Python 3.7 code: directed story stages, moodlet diffing, event-driven stage coordinator, read-only legacy-save reader. Grievance/event mechanics still need porting.
2. `adapter/` — experimental Sims 4 Buff API bridge and once-only zone/score observers. Still not wired to an installable gameplay bootstrap or state backend.
3. `engine/actions.py` — canonical ten-action catalogue and runner registry; actions cannot appear in game until real runner logic, UI interaction tuning and registration are ported.
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
Current work contains a stage selector, stage moodlet diff, pair coordinator, action catalogue, event dispatcher, read-only legacy reader, experimental Sims 4 Buff adapter and idempotent game hooks, with offline and mock-game tests. Missing: real gameplay record changes, registered action runners, UI tuning, dedicated save lifecycle, the v0.8 bootstrap and in-game smoke tests. No installable v0.8 release yet.
