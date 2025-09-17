# Reinforcement Learning Integration Design

## 1. Overview
This document defines how to layer a Reinforcement Learning (RL) control loop onto the existing AI Sandbox simulation to dynamically stabilize population dynamics while avoiding starvation collapse and runaway growth. The RL agent will periodically adjust selected simulation parameters (primarily reproduction & mortality modifiers) based on a compact state vector derived from existing diagnostics.

## 2. Core RL Components
| RL Concept | Mapping in Sandbox |
|------------|--------------------|
| Agent | New controller object (e.g. `RLLifecycleAgent`) deciding parameter adjustments. |
| Environment | Existing simulation loop (`run_core_sim` / `WorldEngine`) producing transitions. |
| State (S_t) | Vector from `_collect_diagnostics` + selected wave/adaptation indicators. |
| Action (A_t) | Discrete adjustment to reproduction base chance or mortality amplitude (plus no-op). |
| Reward (R_t) | Scalar measuring population stability, avoiding starvation, staying within target band. |
| Episode | Fixed number of ticks (e.g. 1,000) or until terminal failure (extinction or explosive overflow). |
| Step Interval | Agent intervenes every N ticks (e.g. every 20) instead of every tick to reduce noise. |

## 3. State Vector Design
Goal: Provide a concise, normalized snapshot capturing resource sufficiency, demographic pressure, and recent volatility.

### 3.1 Raw Features
| Name | Source | Rationale |
|------|--------|-----------|
| population | `_collect_diagnostics.population` | Core controlled variable. |
| total_food | `_collect_diagnostics.total_food` | Food availability buffer. |
| births_last | `_collect_diagnostics.births` | Reproductive activity (tick-level). |
| deaths_starv_last | `_collect_diagnostics.deaths_starv` | Starvation indicator. |
| deaths_natural_last | `_collect_diagnostics.deaths_natural` | Baseline mortality. |
| age_avg | `_collect_diagnostics.avg` | Demographic aging trend. |
| age_max | `_collect_diagnostics.max` | Survivability extremes. |
| wave_res_mult | `world.get_wave_status()['resource_multiplier']` (fallback=1) | Phase of resource oscillation. |
| wave_fert_mult | same | Fertility wave phase for context. |
| wave_mort_mult | same | Mortality pressure phase. |
| repro_base | `world.balance_params['REPRO_BASE_CHANCE']` | Current reproduction setting (affected by agent + scaling). |
| repro_cd | `world.balance_params['REPRO_COOLDOWN']` | Cooldown reflecting agent influence & clamps. |
| starvation_ratio | `deaths_starv_last / max(1, population)` | Instant starvation pressure. |
| food_per_capita | `total_food / max(1, population)` | Resource sufficiency per NPC. |
| target_band_mid | Derived from `(world._pop_target_min + world._pop_target_max)/2` if present | Adaptive target anchor. |
| band_deviation | `(population - target_band_mid)` | Distance from adaptive target center. |
| rolling_pop_delta | EMA or diff over last intervention interval | Short-term momentum. |

### 3.2 Normalization Strategy
| Feature Class | Method |
|---------------|--------|
| Counts (population, births, deaths) | Divide by `POP_NORM = 500` (expected safe upper bound). |
| Food totals | Divide by `FOOD_NORM = 10000` (empirically chosen; adjust after logging distributions). |
| Age stats | Divide by `AGE_NORM = 400` (above typical max lifespan). |
| Multipliers / ratios | Already ~O(1); clamp to [-2, 2] then scale to [-1,1]. |
| Reproduction base chance | Map `[0.02, 0.06] -> [0,1]`. |
| Reproduction cooldown | Map `[120, 260] -> [0,1]` then invert (lower cooldown = higher value). |
| Deviation | Scale by dividing by `(world._pop_target_max - world._pop_target_min)` if available else 200. |
| Momentum (rolling_pop_delta) | Divide by 50 (empirical; adjust). |

Produce final numpy-style float32 vector. Missing optional fields fallback to neutral (0 or 1) before normalization.

### 3.3 Rolling & Derived Variables
Maintain a small circular buffer of recent population values (length = intervention interval * 3) to compute momentum and optionally variance (variance could be added later to reward shaping if needed).

## 4. Action Space
Initial discrete action set (A=5):
1. `repro_up`: Increase `REPRO_BASE_CHANCE` by +0.002 (capped by clamp logic).
2. `repro_down`: Decrease `REPRO_BASE_CHANCE` by -0.002 (floored).
3. `mortality_amp_up`: Increase `world.mortality_wave_amplitude` by +0.01 (capped ≤ 0.20).
4. `mortality_amp_down`: Decrease `world.mortality_wave_amplitude` by -0.01 (≥ 0.02 floor).
5. `noop`: No adjustment this step.

Optional extension (later): adjust fertility amplitude, resource amplitude, or reproduction cooldown offset directly.

All actions applied just before tick loop segment after collecting a state snapshot at each intervention boundary.

## 5. Reward Function
Primary objective: Keep population tightly within 330–350. Simplicity and strong directional signal take priority over secondary shaping.

### 5.1 Piecewise Population Reward (Per Tick or Per Intervention Step)
Let `P` be current population. Apply the first matching bracket:

| Range | Reward |
|-------|--------|
| 330 <= P <= 350 | +10 (ideal stability zone) |
| 300 <= P < 330 OR 351 <= P <= 380 | -1 (minor deviation) |
| 200 <= P < 300 OR 381 < P <= 500 | -5 (moderate instability) |
| P < 200 OR P > 500 | -50 (severe collapse or explosion; terminal by default) |

Terminal condition triggered when severe bracket hit unless explicitly continuing for analysis.

### 5.2 Supplemental Shaping (Optional Layer)
Add only if learning oscillates or converges slowly; otherwise start with pure piecewise rule above.
```
R_total = R_piecewise
      - 20 * starvation_ratio            # discourage even small starvation presence
      - 0.001 * (pop_momentum ** 2)      # damp rapid oscillations (optional)
```
Where `pop_momentum` is the change in population over the last intervention interval (not per tick). Apply clipping to, e.g., `[-100, +100]` to prevent outlier distortion.

### 5.3 Implementation Order of Operations
1. Compute base piecewise reward using current population.
2. If severe bracket: set `done=True`, reward stays at -50 (do not add shaping bonuses).
3. Else (not severe): optionally layer starvation & momentum adjustments if enabled.
4. Log components for diagnostics (e.g., `[RL] pop=342 zone=ideal r=10 starv=0.00 mom=+4 final=10`).

### 5.4 Rationale
- Large positive plateau removes overfitting to exact single value while focusing on corridor occupancy.
- Symmetric minor penalty band keeps gradient signal mild around edges without overshadowing catastrophic penalties.
- Severe penalty creates a powerful deterrent to both collapse and explosion, anchoring the policy search space.
- Optional shaping is isolated so experimentation can toggle it without redefining core reward semantics.

### 5.5 Suggested Training Progression
Phase 1: Pure piecewise reward only.
Phase 2: Enable starvation penalty if agent sometimes enters ideal band while starvation events occur upstream.
Phase 3: Enable momentum penalty if oscillations between bands become persistent (>10 alternations per 1k ticks).

### 5.6 Potential Extensions
- Add small positive persistence bonus for consecutive ticks inside ideal band (e.g., +0.5 after 25 uninterrupted ticks) to encourage sustained occupancy.
- Replace fixed thresholds with adaptive ones tied to internal targets once stable policy exists.
- Introduce partial credit gradient inside 330–350 by adding a gentle center-seeking reward if agent plateaus at boundaries.

## 6. Episode & Step Mechanics
| Parameter | Default | Notes |
|-----------|---------|-------|
| ticks_per_episode | 1000 | Training episodes; can scale up later. |
| intervention_interval | 20 | Agent acts every 20 ticks. |
| warmup_ticks | 40 | Optionally skip actions first 40 ticks for stable baseline. |
| max_episodes | Configurable | Controlled by training script. |

At each intervention boundary (tick % interval == 0):
1. Gather state.
2. Compute reward from last interval (using aggregated counters difference-based if needed).
3. If training: store (prev_state, action, reward, new_state, done) in replay buffer.
4. Select next action (policy or epsilon-greedy) and apply.

## 7. Integration Points
- Add `rl` subcommand: `python main.py rl --ticks 1000 --interval 20` launching an RL loop wrapper.
- Create `rl_agent.py` with:
  - `RLSandboxEnv` class exposing `reset()`, `step(action)` (Gym-like interface) internally driving `WorldEngine` ticks.
  - `DiscreteAgent` placeholder (random policy / epsilon-greedy stub).
- Extract state via refactored helper: move `_collect_diagnostics` to share or wrap it with RL-specific aggregator.

## 8. Data Structures
```python
class RLSandboxEnv:
    def __init__(self, ticks_per_episode=1000, interval=20, seed=42): ...
    def reset(self): ...  # returns state
    def step(self, action_index: int):
        # advances simulation interval ticks, applies action at start
        # returns (next_state, reward, done, info)
```
Replay (future): simple list of tuples. Optionally integrate with PyTorch later.

## 9. Safety & Constraints
- All parameter changes flow through existing clamps (`_clamp_reproduction_params`) preserving hard safety bounds.
- Mortality amplitude adjustments re-clamped: `[0.02, 0.20]`.
- Reproduction base constrained `[0.02, 0.06]` (effective ceiling slightly dynamic already). Agent never directly edits cooldown to reduce complexity initially.

## 10. Metrics & Logging
Log every intervention:
```
[RL] step=k pop=... dev=... action=REPRO_UP base=0.034 mort_amp=0.09 reward=0.82
```
Aggregate episode summary:
```
[RL] episode=12 avg_reward=0.73 final_pop=128 starvation_events=0 overflow=0
```
Store raw transitions optionally in `persistence/rl/episode_<n>.jsonl`.

## 11. Future Extensions
- Continuous action space (PPO/DDPG) adjusting multiple parameters simultaneously.
- Curriculum: progressively relax amplitude clamps after stability proven.
- Multi-objective reward incorporating culture growth or dialogue richness.
- Adaptive intervention interval (shorten during instability).

## 12. Immediate Next Steps
1. Implement `rl_agent.py` scaffolding with env + random agent.
2. Add `rl` subcommand to `main.py`.
3. Refactor shared diagnostics accessor for RL state building.
4. Add basic logging and JSONL transition dump.
5. Run a few episodes to validate reward distribution (inspect histogram).

---
*This document is a living spec; adjust coefficients and normalization after first empirical logging pass.*
