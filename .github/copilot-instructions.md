# AI Sandbox – AI Coding Agent Instructions

Concise, project-specific guidance for autonomous coding agents. Focus on existing patterns; do not introduce speculative architectures.

## Core Architecture
- World loop anchored in `world.engine.WorldEngine.world_tick()`; higher-level orchestration (tribal, dialogue, weather, events, combat) happens in wrappers: `main.py` (demo modes) and `core_sim.run_core_sim()` (balanced long-run harness).
- Spatial model: infinite procedurally generated chunk grid (`world/chunk.py`, noise-based terrain in `world/terrain.py`). Active chunks tracked in `WorldEngine.active_chunks`; use `world.get_chunk(x,y)` (auto-creates & seeds) and `world.activate_chunk()` before populating NPCs.
- Time & seasons: minute-level ticks -> hour/day/season/year counters on `WorldEngine`; seasons drive resource multipliers and appear in diagnostics.
- Population control: faction-level harvesting (`Faction.gather_resources`), consumption (`Faction.consume_resources`), reproduction & mortality influenced by adaptive parameters in `WorldEngine.balance_params` plus population wave multipliers (resource/fertility/mortality waves).
- Factions vs Tribes: Factions (`factions/faction.py`) manage territory/resources/memory; Tribes (`tribes/tribal_manager.py`, `tribes/tribe.py`) add cultural, diplomatic, ritual, language layers. Sim code often mirrors both (e.g., create faction for each tribe). Maintain parity if adding population-affecting features.
- Dialogue & Markov: NPC speech via `npc.generate_dialogue(...)` optionally enriched with Markov models (`markov_behavior.py`, `markov_dialogue.py`). Keep calls wrapped with safe guards (see `_generate_dialogue_pair` and `safe_call` in `core_sim.py`).
- Persistence: Two parallel systems: lightweight world_data JSON (chunks/factions) and enhanced snapshot via `PersistenceManager` (file `persistence_manager.py`) storing world, weather, events, tribes, Markov chains under `persistence/`.
- Feature flags: `SANDBOX_FEATURES` env (comma list or bundles: core, social, worldfull, all) toggles optional subsystems (dialogue_full, diplomacy, trade, culture, persist, adapt_export, weather, events, environmental_ai, combat). `core_sim` parses then sets env gating (e.g., `SANDBOX_ALLOW_REPRO`). Respect this mechanism in new code.

## Key Balancing & Safety Patterns
- Reproduction & mortality tuning must pass population stability tests (`tests/population/` & `tests/balance/`). Always adjust via `WorldEngine.balance_params` or controlled wrappers; do not hardcode inside faction logic.
- Harvesting: Modify fractional logic only in `Faction.gather_resources`; tests assume linear depletion with cap (current max 15%). Keep resource type mapping consistent (plant|animal|fish -> food, mineral -> Ore, Wood unchanged).
- Starvation & demographics: Use faction `_starvation_pressure` and thresholds from `balance_params`; avoid adding direct population removals elsewhere.
- Wave system overrides: `core_sim.run_core_sim` may override engine wave amplitudes for test parity; align new long-run harness logic with test expectations in `tests/balance/test_controlled_waves.py` & `tests/population/test_population_waves.py`.

## Testing Conventions
- Run from project root so relative imports resolve.
- Individual test: `python -m tests.population.test_simple_population` or direct path `python tests/population/test_simple_population.py`.
- Category batch (PowerShell examples): `Get-ChildItem tests\balance\*.py | ForEach-Object { python $_.FullName }`.
- `tests/run_tests.py --category population` provides structured execution; it sets `PYTHONPATH` automatically.
- When adding tests place in correct folder; filename `test_<feature>.py`; update `tests/README.md`.

## Extension Guidelines
- New subsystem? Provide thin integration point called from simulation loop (e.g., pattern: weather/events/combat invoked every tick or at interval). Keep per-tick cost minimal; accumulate timing similar to `timing[...]` in `core_sim` for diagnostics.
- Add new feature flag: extend `_parse_features` map in `core_sim.py`; set any controlling env vars in `_configure_environment_flags`.
- Persistence: Extend `PersistenceManager` with new `_serialize_*` helpers and include in `save_world_state`; ensure failures are caught (wrap in try/except returning bool).
- NPC attributes: Add optional fields guarded by `getattr`; never assume presence in dialogue/combat to avoid breaking existing tests.
- Dialogue additions: Maintain proximity check pattern `_npcs_are_close`; limit noisy console prints (respect `DIALOGUE_PRINT_LIMIT`).

## Performance & Parallelism
- Parallel execution toggle via `SANDBOX_USE_PARALLELISM`; code adding executors should honor `os.environ.get('SANDBOX_DISABLE_PARALLELISM')`.
- Avoid heavy per-tick reflection or deep scans over all chunks/NPCs; prefer tracking rolling windows (see `_econ_history`, `_births_history`).

## Logging & Diagnostics
- Core diagnostics every 10 ticks in `core_sim`: replicate style `[DIAG] tick=... total_food=... population=...` when adding metrics.
- Dialogue logging: use dedicated `dialogue` logger (see `setup_dialogue_logger`). Avoid polluting root logger.
- If adding adaptive tuning, append structured dicts to `_adaptation_history` (capped) and expose via export function like `export_adaptation_history`.

## Do / Avoid
- Do: Guard optional imports (weather/events/combat) with try/except and feature checks.
- Do: Use existing helper patterns (`safe_call`, `safe_getattr`).
- Do: Keep new balance params centralized in `WorldEngine.balance_params`.
- Avoid: Direct file I/O in tight loops; blocking calls inside tick; modifying test harness assumptions (harvest fraction signature, balance param keys).

## Quick Run Recipes
- Balanced core sim (1000 ticks): `python core_sim.py 1000`
- Demo menu modes: `python main.py`
- All balance tests: `Get-ChildItem tests\balance\*.py | ForEach-Object { python $_.FullName }`

Refine this file as architecture evolves; keep under ~50 lines of actionable guidance.
- [ ] Clarify Project Requirements
- [ ] Scaffold the Project
- [ ] Customize the Project
- [ ] Install Required Extensions
- [ ] Compile the Project
- [ ] Create and Run Task
- [ ] Launch the Project
- [ ] Ensure Documentation is Complete
