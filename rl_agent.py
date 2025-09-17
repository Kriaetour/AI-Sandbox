import random
import json
from collections import defaultdict, deque
from typing import Tuple, Dict, List, Any, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv


from core_sim import _collect_diagnostics  # reuse diagnostics helper
from world.engine import WorldEngine

# NOTE: We are not using run_core_sim's full loop here; instead we construct a
# minimal environment wrapper stepping the underlying WorldEngine directly to
# allow per-tick RL control before integrating deeper.

ACTION_NAMES = [
    "repro_up",
    "repro_down",
    "mortality_amp_up",
    "mortality_amp_down",
    "noop",
]


class RLSandboxEnv:
    def __init__(
        self,
        seed: int = 42,
        intervention_interval: int = 1,
        init_pop_min: int = 300,
        init_pop_max: int = 370,
        enable_llm: bool = False,
        llm_reward_freq: int = 100,
        max_llm_calls: int = 100,
        llm_batch_only: bool = False,
    ):
        random.seed(seed)
        self.seed = seed
        self.interval = intervention_interval  # currently 1 (per tick) for direct control
        self.world: Optional[WorldEngine] = None
        self.tick = 0
        self.last_population = None
        self.pop_history = deque(maxlen=64)
        self.init_pop_min = init_pop_min
        self.init_pop_max = init_pop_max
        self.enable_llm = enable_llm
        self.llm_reward_freq = llm_reward_freq
        self.max_llm_calls = max_llm_calls
        self.llm_batch_only = llm_batch_only
        self.llm_call_count = 0

        # Q-learning attributes
        self.num_actions = len(ACTION_NAMES)
        self.lr = 0.1
        self.gamma = 0.95
        self.epsilon = 0.1
        self.q = defaultdict(lambda: [0.0] * self.num_actions)
        self.pop_bin_size = 10
        self.food_bin_size = 500
        self.births_cap = 5
        self.starv_cap = 5

    def _execute_action(self, world: WorldEngine, action_idx: int):
        """Execute the selected action on the world."""
        action = ACTION_NAMES[action_idx]
        try:
            if action == "repro_up":
                cur = world.balance_params.get("REPRO_BASE_CHANCE", 0.03)
                world.balance_params["REPRO_BASE_CHANCE"] = min(0.06, cur + 0.002)
            elif action == "repro_down":
                cur = world.balance_params.get("REPRO_BASE_CHANCE", 0.03)
                world.balance_params["REPRO_BASE_CHANCE"] = max(0.02, cur - 0.002)
            elif action == "mortality_amp_up" and hasattr(world, "mortality_wave_amplitude"):
                world.mortality_wave_amplitude = min(
                    0.20, getattr(world, "mortality_wave_amplitude", 0.08) + 0.01
                )
            elif action == "mortality_amp_down" and hasattr(world, "mortality_wave_amplitude"):
                world.mortality_wave_amplitude = max(
                    0.02, getattr(world, "mortality_wave_amplitude", 0.08) - 0.01
                )
            # noop does nothing
        except Exception:
            pass

    def reset(self):
        # Create a fresh world mirroring run_core_sim setup minimally
        self.world = WorldEngine(
            seed=self.seed, disable_faction_saving=True
        )  # Disable faction saving for RL training performance
        # If waves are enabled we keep existing override pattern
        # (not re-implemented fully here)
        # Apply conservative wave & reproduction clamp logic
        # similar to core_sim
        try:
            if getattr(self.world, "wave_enabled", False):
                self.world.abundance_cycle_length = 480
                self.world.fertility_wave_length = 360
                self.world.mortality_wave_length = 420
                self.world.resource_wave_amplitude = 0.15
                self.world.fertility_wave_amplitude = 0.12
                self.world.mortality_wave_amplitude = 0.08
                print("[RL-INIT] Wave overrides applied (conservative)")
            # Reproduction jitter & adaptive target band if available
            try:
                self.world.enable_repro_jitter = True
                self.world.repro_jitter_spread = 0.30
            except Exception:
                pass
            try:
                # Adaptive population targets based on training range
                target_center = (self.init_pop_min + self.init_pop_max) / 2
                target_range = max(20, target_center * 0.3)  # 30% range min 20
                self.world._pop_target_min = max(10, target_center - target_range)
                self.world._pop_target_max = target_center + target_range
                print(
                    f"[RL-INIT] Adaptive population targets: "
                    f"{self.world._pop_target_min}-"
                    f"{self.world._pop_target_max}"
                )
            except Exception:
                pass
        except Exception:
            pass

        # Prepare clamp helper replicating simplified version
        def _clamp_repro():
            try:
                bp = self.world.balance_params.get("REPRO_BASE_CHANCE", 0.03)
                cd = self.world.balance_params.get("REPRO_COOLDOWN", 200)
                bp = max(0.02, min(0.055, bp))
                cd = max(140, min(260, cd))
                self.world.balance_params["REPRO_BASE_CHANCE"] = bp
                self.world.balance_params["REPRO_COOLDOWN"] = cd
            except Exception:
                pass

        self._clamp_repro = _clamp_repro
        # Minimal tribe/NPC seeding (two small tribes like core_sim)
        try:
            from factions.faction import Faction
            from npcs.npc import NPC

            # Create a simple faction
            faction_name = "RLFaction"
            if faction_name not in self.world.factions:
                self.world.factions[faction_name] = Faction(name=faction_name, territory=[(0, 0)])

            # Activate the chunk
            self.world.activate_chunk(0, 0)

            # Bootstrap population to target
            target_population = random.randint(self.init_pop_min, self.init_pop_max)
            print(f"[RL-INIT] Bootstrapping to target population: " f"{target_population}")

            for i in range(target_population):
                try:
                    npc_name = f"rl_npc_{i}"
                    npc = NPC(name=npc_name, coordinates=(0, 0), faction_id=faction_name)
                    chunk = self.world.get_chunk(0, 0)
                    if npc not in chunk.npcs:
                        chunk.npcs.append(npc)
                    self.world.factions[faction_name].add_member(npc.name)
                except Exception as e:
                    print(f"[RL-INIT] Failed to create NPC {i}: {e}")
                    break

            final_pop = sum(len(ch.npcs) for ch in self.world.active_chunks.values())
            print(f"[RL-INIT] Bootstrap complete: {final_pop} NPCs created")

        except Exception as e:
            print(f"[RL-INIT] Bootstrap failed: {e}")
            # Fallback: just seed with minimum population
            try:
                self.world._auto_seed()
            except Exception as e2:
                print(f"[RL-INIT] Fallback seeding also failed: {e2}")
        # Initial clamp pass
        self._clamp_repro()
        self.tick = 0
        self.last_population = None
        self.pop_history.clear()

        # Debug: Show initial population
        initial_pop = self._get_population()
        print(
            f"[RL-INIT] Initial population: {initial_pop} (target range: {self.init_pop_min}-{self.init_pop_max})"
        )

        return self._get_state()

    def _get_population(self) -> int:
        if not self.world:
            return 0
        return sum(len(ch.npcs) for ch in self.world.active_chunks.values())

    def _collect(self) -> Dict[str, Any]:
        if not self.world:
            return {}
        try:
            return _collect_diagnostics(self.world)
        except Exception:
            return {}

    def _get_state(self) -> Dict[str, Any]:
        diag = self._collect()
        pop = diag.get("population", 0)
        food = diag.get("total_food", 0)
        births = diag.get("births", 0)
        deaths_starv = diag.get("deaths_starv", 0)
        deaths_nat = diag.get("deaths_natural", 0)

        # Include saying information from enhanced RL state
        from rl_env_state import get_rl_env_state

        enhanced_state = get_rl_env_state(self.world)
        recent_sayings = enhanced_state.get("recent_sayings", [])

        # Simple dict state for now; agent will discretize
        state = {
            "population": pop,
            "food": food,
            "births": births,
            "deaths_starv": deaths_starv,
            "deaths_nat": deaths_nat,
            "recent_sayings": recent_sayings,  # Include actual generated sayings
        }
        return state

    def _piecewise_population_reward(self, pop: int) -> Tuple[float, bool]:
        # Adaptive reward function based on target population range
        # Calculate target band based on initial population settings
        target_center = (self.init_pop_min + self.init_pop_max) / 2
        target_radius = min(
            50, target_center * 0.2
        )  # Adaptive radius: 20% of target or 50, whichever is smaller

        # Define reward zones relative to target
        ideal_min = target_center - target_radius
        ideal_max = target_center + target_radius
        minor_dev_min = target_center - target_radius * 3
        minor_dev_max = target_center + target_radius * 3
        moderate_dev_min = target_center - target_radius * 6

        # Ensure minimum viable population (very permissive for learning)
        max_viable = target_center * 15  # Allow up to 15x target before severe penalty

        if ideal_min <= pop <= ideal_max:
            return 10.0, False  # Ideal stability zone
        elif (minor_dev_min <= pop < ideal_min) or (ideal_max < pop <= minor_dev_max):
            return -1.0, False  # Minor deviation
        elif (moderate_dev_min <= pop < minor_dev_min) or (minor_dev_max < pop <= max_viable):
            return -5.0, False  # Moderate instability
        else:
            # Severe collapse (too low) or explosion (too high)
            return -50.0, True

    def step(self, action_index: int):
        assert self.world is not None, "Environment not reset"
        if action_index < 0 or action_index >= len(ACTION_NAMES):
            action_index = len(ACTION_NAMES) - 1
        action = ACTION_NAMES[action_index]

        # Log RL action for analytics
        try:
            with open("rl_actions.log", "a") as f:
                f.write(f"RL_ACTION: {action} source=RLAgent target=None result=True\n")
        except Exception:
            pass

        # Reproduction ramp: hold low early, then gradually allow baseline
        try:
            ramp_tick = self.tick
            if ramp_tick < 100:
                self.world.balance_params["REPRO_BASE_CHANCE"] = 0.02
            elif ramp_tick < 300:
                # Linear interpolate 0.02 -> 0.03 over ticks 100..300
                frac = (ramp_tick - 100) / 200.0
                self.world.balance_params["REPRO_BASE_CHANCE"] = 0.02 + 0.01 * frac
            # After 300 leave to agent adjustments (still bounded by actions)
            if ramp_tick in (0, 100, 300):
                print(
                    f"[RL-RAMP] tick={ramp_tick} repro_base={self.world.balance_params['REPRO_BASE_CHANCE']:.5f}"
                )
        except Exception:
            pass

        # Apply action (bounded adjustments) prior to world tick
        try:
            if action == "repro_up":
                cur = self.world.balance_params.get("REPRO_BASE_CHANCE", 0.03)
                self.world.balance_params["REPRO_BASE_CHANCE"] = min(0.06, cur + 0.002)
            elif action == "repro_down":
                cur = self.world.balance_params.get("REPRO_BASE_CHANCE", 0.03)
                self.world.balance_params["REPRO_BASE_CHANCE"] = max(0.02, cur - 0.002)
            elif action == "mortality_amp_up" and hasattr(self.world, "mortality_wave_amplitude"):
                self.world.mortality_wave_amplitude = min(
                    0.20, getattr(self.world, "mortality_wave_amplitude", 0.08) + 0.01
                )
            elif action == "mortality_amp_down" and hasattr(self.world, "mortality_wave_amplitude"):
                self.world.mortality_wave_amplitude = max(
                    0.02, getattr(self.world, "mortality_wave_amplitude", 0.08) - 0.01
                )
            # noop does nothing
        except Exception:
            pass

        # Advance one world tick
        try:
            pre_pop = sum(len(ch.npcs) for ch in self.world.active_chunks.values())
            self.world.world_tick()
            # Soft mortality boost: if population exceeds upper band, apply gentle cull percentage
            # Adaptive birth cap enforcement:
            #   If population > upper band -> cap = 0 (no net births kept)
            #   If within band (1330-1350) -> cap = 1% (min 2)
            #   If below lower band -> cap = 2% (min 3)
            try:
                post_pop = sum(len(ch.npcs) for ch in self.world.active_chunks.values())
                births = post_pop - pre_pop
                lower_band = 1330
                upper_band = 1350
                # Mortality boost executes before birth trimming uses post_pop
                if post_pop > upper_band:
                    # Cull fraction scales with distance above band up to 0.5% baseline to 1.5% max
                    over = post_pop - upper_band
                    frac = min(0.015, 0.005 + over / 1000.0)  # 0.5% -> up to 1.5%
                    to_cull = int(post_pop * frac)
                    culled = 0
                    if to_cull > 0:
                        for ch in self.world.active_chunks.values():
                            i = 0
                            while i < len(ch.npcs) and culled < to_cull:
                                npc = ch.npcs[i]
                                # Favor culling very old or very young to simulate natural pressures
                                age = getattr(npc, "age", 0)
                                if age <= 1 or age > 60:
                                    ch.npcs.pop(i)
                                    culled += 1
                                    continue
                                i += 1
                            if culled >= to_cull:
                                break
                        if culled > 0:
                            post_pop = sum(len(ch.npcs) for ch in self.world.active_chunks.values())
                            print(
                                f"[RL-MORT] pre_pop={pre_pop} post_pop_after_tick={post_pop + births} culled={culled} new_post_pop={post_pop} frac={frac:.4f}"
                            )
                if pre_pop > upper_band:
                    cap = 0
                elif pre_pop < lower_band:
                    cap = max(3, int(pre_pop * 0.02))
                else:
                    cap = max(2, int(pre_pop * 0.01))
                if births > cap:
                    # Remove excess newborns from chunks (last appended assumed youngest)
                    excess = births - cap
                    removed = 0
                    for ch in self.world.active_chunks.values():
                        # Sort or scan from end; simplistic strategy: remove recent additions heuristically
                        i = len(ch.npcs) - 1
                        while i >= 0 and removed < excess:
                            npc = ch.npcs[i]
                            # crude heuristic: name contains 'child' or 'boot_' or age==0
                            age = getattr(npc, "age", 0)
                            if age == 0 or "child" in npc.name:
                                ch.npcs.pop(i)
                                removed += 1
                            i -= 1
                        if removed >= excess:
                            break
                    if removed > 0:
                        print(
                            f"[RL-CAP] pre_pop={pre_pop} births={births} cap={cap} trimmed={removed}"
                        )
            except Exception:
                pass
            # Clamp after tick (in case adaptive logic affected params)
            self._clamp_repro()
        except Exception:
            # If tick fails, treat as terminal severe penalty
            return self._get_state(), -50.0, True, {"error": "tick_failed"}

        self.tick += 1
        state = self._get_state()
        pop = state["population"]

        # --- Multi-aspect shaped reward ---
        # Always use rule-based reward computation for RL training
        # LLM explanations are separate and don't affect the reward signal
        weights = {
            "cohesion": 1.0,
            "allies": 0.5,
            "hostiles": -0.5,
            "rumor": 0.3,
            "saying": 0.3,
            "pop_stability": 0.2,
            "deaths": -0.2,
            "births": 0.1,
        }
        # Compute all components for logging
        from rl_env_state import get_rl_env_state

        state_features = get_rl_env_state(self.world)
        cohesion = state_features.get("avg_opinion", 0)
        allies = state_features.get("total_allies", 0)
        hostiles = state_features.get("total_hostiles", 0)
        rumor = state_features.get("avg_rumor_count", 0)
        saying = state_features.get("avg_saying_count", 0)
        pop_stability = 1.0 - abs(state_features.get("population", 0) - 300) / 300
        deaths = state_features.get("deaths_starv_tick", 0)
        births = state_features.get("births_tick", 0)

        # Track previous values for penalties
        if not hasattr(self, "_prev_deaths"):
            self._prev_deaths = deaths
        if not hasattr(self, "_prev_pop_stability"):
            self._prev_pop_stability = pop_stability

        # Calculate rapid change penalties
        death_delta = deaths - self._prev_deaths
        popstab_delta = pop_stability - self._prev_pop_stability
        penalty = 0.0
        if death_delta > 0:
            penalty -= 2.0 * death_delta  # Penalize rapid increases in deaths
        if popstab_delta < 0:
            penalty += (
                5.0 * popstab_delta
            )  # Penalize drops in pop stability (popstab_delta is negative)

        reward = (
            weights["cohesion"] * cohesion
            + weights["allies"] * allies
            + weights["hostiles"] * hostiles
            + weights["rumor"] * rumor
            + weights["saying"] * saying
            + weights["pop_stability"] * pop_stability
            + weights["deaths"] * deaths
            + weights["births"] * births
        ) + penalty

        # Update previous values
        self._prev_deaths = deaths
        self._prev_pop_stability = pop_stability

        # LLM explanations are separate from reward computation
        if self.enable_llm and not self.llm_batch_only and self.llm_call_count < self.max_llm_calls:
            # Log LLM explanation based on frequency and significance
            should_explain = (
                self.llm_reward_freq > 0 and self.tick % self.llm_reward_freq == 0
            ) or (abs(reward) > 5.0 and self.llm_call_count < self.max_llm_calls)
            if should_explain:
                from rl_reward_shaping import compute_shaped_reward_with_explanation

                _, reward_explanation, _ = compute_shaped_reward_with_explanation(
                    self.world, action_taken=ACTION_NAMES[action_index]
                )
                print(f"[LLM-REWARD] {reward_explanation}")
                self.llm_call_count += 1
                if self.llm_call_count % 10 == 0:  # Log every 10 calls
                    print(
                        f"[LLM-USAGE] Episode API calls: {self.llm_call_count}/{self.max_llm_calls}"
                    )

        # Log all components to CSV
        try:
            with open("reward_components.csv", "a") as f:
                if self.tick == 1:
                    f.write(
                        "tick,cohesion,allies,hostiles,rumor,saying,pop_stability,deaths,births,reward\n"
                    )
                f.write(
                    f"{self.tick},{cohesion},{allies},{hostiles},{rumor},{saying},{pop_stability},{deaths},{births},{reward}\n"
                )
        except Exception:
            pass

        # Log to rewards.csv for analytics export (tick,population,reward format)
        try:
            with open("rewards.csv", "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([self.tick, pop, reward])
        except Exception:
            pass
        # Adaptive terminal condition based on training range
        target_center = (self.init_pop_min + self.init_pop_max) / 2
        min_viable = max(5, target_center * 0.1)  # At least 5 or 10% of target
        max_viable = target_center * 5  # Allow up to 5x target before forced termination
        done = pop < min_viable or pop > max_viable
        if done:
            try:
                self.world.shutdown()
            except Exception:
                pass
        return state, reward, done, {"action": action, "tick": self.tick}

    def _discretize_state(self, state: Dict[str, Any]) -> Tuple:
        # Bucket key metrics into configurable bins
        pop_bin = int(state["population"] // self.pop_bin_size)
        food_bin = int(state["food"] // self.food_bin_size)
        births_bin = min(self.births_cap, int(state["births"]))
        starv_bin = min(self.starv_cap, int(state["deaths_starv"]))

        # Include saying features for discretization
        recent_sayings = state.get("recent_sayings", [])
        saying_count = len(recent_sayings)
        saying_diversity = len(set(recent_sayings)) if recent_sayings else 0

        return (
            pop_bin,
            food_bin,
            births_bin,
            starv_bin,
            saying_count,
            saying_diversity,
        )

    def select_action(self, state: Dict[str, Any]) -> int:
        key = self._discretize_state(state)
        if random.random() < self.epsilon:
            return random.randrange(self.num_actions)
        qvals = self.q[key]
        max_q = max(qvals)
        # tie-break randomly among best
        best_actions = [i for i, v in enumerate(qvals) if v == max_q]
        return random.choice(best_actions)

    def update(
        self,
        prev_state: Dict[str, Any],
        action: int,
        reward: float,
        next_state: Dict[str, Any],
        done: bool,
    ):
        s_key = self._discretize_state(prev_state)
        ns_key = self._discretize_state(next_state)
        current_q = self.q[s_key][action]
        target = reward
        if not done:
            target += self.gamma * max(self.q[ns_key])
        self.q[s_key][action] = current_q + self.lr * (target - current_q)


class TabularQLearningAgent:
    def __init__(
        self,
        num_actions: int,
        lr: float = 0.1,
        gamma: float = 0.95,
        epsilon: float = 0.2,
        pop_bin_size: int = 10,
        food_bin_size: int = 500,
        births_cap: int = 5,
        starv_cap: int = 5,
    ):
        self.num_actions = num_actions
        self.lr = lr
        self.gamma = gamma
        self.epsilon = epsilon
        self.q = defaultdict(lambda: [0.0] * num_actions)
        self.pop_bin_size = max(1, int(pop_bin_size))
        self.food_bin_size = max(1, int(food_bin_size))
        self.births_cap = max(1, int(births_cap))
        self.starv_cap = max(1, int(starv_cap))

    def _discretize_state(self, state: Dict[str, Any]) -> Tuple:
        # Bucket key metrics into configurable bins
        pop_bin = int(state["population"] // self.pop_bin_size)
        food_bin = int(state["food"] // self.food_bin_size)
        births_bin = min(self.births_cap, int(state["births"]))
        starv_bin = min(self.starv_cap, int(state["deaths_starv"]))

        # Include saying features for discretization
        recent_sayings = state.get("recent_sayings", [])
        saying_count = len(recent_sayings)
        saying_diversity = len(set(recent_sayings)) if recent_sayings else 0

        return (
            pop_bin,
            food_bin,
            births_bin,
            starv_bin,
            saying_count,
            saying_diversity,
        )

    def select_action(self, state: Dict[str, Any]) -> int:
        key = self._discretize_state(state)
        if random.random() < self.epsilon:
            return random.randrange(self.num_actions)
        qvals = self.q[key]
        max_q = max(qvals)
        # tie-break randomly among best
        best_actions = [i for i, v in enumerate(qvals) if v == max_q]
        return random.choice(best_actions)

    def update(
        self,
        prev_state: Dict[str, Any],
        action: int,
        reward: float,
        next_state: Dict[str, Any],
        done: bool,
    ):
        s_key = self._discretize_state(prev_state)
        ns_key = self._discretize_state(next_state)
        current_q = self.q[s_key][action]
        target = reward
        if not done:
            target += self.gamma * max(self.q[ns_key])
        self.q[s_key][action] = current_q + self.lr * (target - current_q)


def run_simple_rl_episode(
    max_ticks: int = 500,
    init_pop_min: int = 300,
    init_pop_max: int = 370,
    pop_bin_size: int = 10,
    food_bin_size: int = 500,
    births_cap: int = 5,
    starv_cap: int = 5,
    lr: float = 0.1,
    gamma: float = 0.95,
    intervention_interval: int = 1,
):
    env = RLSandboxEnv(
        init_pop_min=init_pop_min,
        init_pop_max=init_pop_max,
        intervention_interval=intervention_interval,
    )
    state = env.reset()
    agent = TabularQLearningAgent(
        num_actions=len(ACTION_NAMES),
        lr=lr,
        gamma=gamma,
        pop_bin_size=pop_bin_size,
        food_bin_size=food_bin_size,
        births_cap=births_cap,
        starv_cap=starv_cap,
    )
    total_reward = 0.0
    # Log initial state
    print(f"[RL] start tick=0 pop={state['population']}")
    for _ in range(max_ticks):
        action = agent.select_action(state)
        next_state, reward, done, info = env.step(action)
        agent.update(state, action, reward, next_state, done)
        total_reward += reward
        state = next_state
        tick_val = info.get("tick", -1)
        if tick_val != -1 and (tick_val % 50 == 0 or done):
            print(
                f"[RL] tick={tick_val} pop={state['population']} action={ACTION_NAMES[action]} reward={reward} cum={total_reward:.1f}"
            )
        if done and tick_val != -1:
            print(
                f"[RL] episode complete at tick={tick_val} final_pop={state['population']} total_reward={total_reward:.1f}"
            )
            break
    return total_reward


def run_rl_training(
    episodes: int = 10,
    max_ticks: int = 500,
    epsilon_start: float = 0.3,
    epsilon_min: float = 0.05,
    epsilon_decay: float = 0.92,
    save_path: str | None = None,
    load_path: str | None = None,
    init_pop_min: int = 300,
    init_pop_max: int = 370,
    pop_bin_size: int = 10,
    food_bin_size: int = 500,
    births_cap: int = 5,
    starv_cap: int = 5,
    lr: float = 0.1,
    gamma: float = 0.95,
    intervention_interval: int = 1,
    enable_llm: bool = False,
    llm_reward_freq: int = 100,
    max_llm_calls: int = 100,
    llm_batch_only: bool = False,
    parallel_processes: int = 1,
):
    """Run multiple RL episodes with epsilon decay and optional Q-table persistence.

    Args:
        episodes: Number of episodes to run.
        max_ticks: Max ticks per episode.
        epsilon_start: Initial exploration rate.
        epsilon_min: Floor for exploration rate.
        epsilon_decay: Multiplicative decay applied after each episode.
        save_path: If provided, serialize Q-table JSON at end.
        load_path: If provided, load existing Q-table JSON before training.
        intervention_interval: How often (in ticks) the RL agent makes decisions.
    """
    agent = TabularQLearningAgent(
        num_actions=len(ACTION_NAMES),
        epsilon=epsilon_start,
        lr=lr,
        gamma=gamma,
        pop_bin_size=pop_bin_size,
        food_bin_size=food_bin_size,
        births_cap=births_cap,
        starv_cap=starv_cap,
    )
    # Load existing table if requested
    if load_path:
        try:
            with open(load_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # data: {state_key_str: [qvalues]}
            for k, qvals in data.items():
                # state key stored as repr tuple string -> eval safe because we created it; fallback safe parse
                try:
                    state_key = (
                        tuple(int(x) for x in k.strip("()").split(",")) if k.startswith("(") else k
                    )
                except Exception:
                    state_key = k
                agent.q[state_key] = qvals
            print(f"[RL-TRAIN] Loaded Q-table with {len(agent.q)} states from {load_path}")
        except Exception as e:
            print(f"[RL-TRAIN] Failed to load Q-table: {e}")

    episode_rewards: List[float] = []
    episode_lengths: List[int] = []
    episode_populations: List[float] = []

    if parallel_processes > 1:
        # Parallel execution
        print(
            f"[RL-TRAIN] Running {episodes} episodes with {parallel_processes} parallel processes"
        )

        # Calculate epsilon values for each episode
        epsilon_values = []
        current_epsilon = epsilon_start
        for ep in range(1, episodes + 1):
            epsilon_values.append(current_epsilon)
            current_epsilon = max(epsilon_min, current_epsilon * epsilon_decay)

        # Run episodes in parallel
        with ProcessPoolExecutor(max_workers=parallel_processes) as executor:
            futures = []
            for ep in range(1, episodes + 1):
                future = executor.submit(
                    run_single_episode,
                    ep,
                    max_ticks,
                    epsilon_values[ep - 1],
                    lr,
                    gamma,
                    pop_bin_size,
                    food_bin_size,
                    births_cap,
                    starv_cap,
                    init_pop_min,
                    init_pop_max,
                    intervention_interval,
                    enable_llm,
                    llm_reward_freq,
                    max_llm_calls,
                    llm_batch_only,
                )
                futures.append(future)

            # Collect results and update Q-table
            for future in as_completed(futures):
                result = future.result()
                episode_rewards.append(result["reward"])
                episode_lengths.append(result["length"])
                episode_populations.append(result["avg_population"])

                # Update Q-table with experiences from this episode
                for state, action, reward, next_state, done in result["experiences"]:
                    agent.update(state, action, reward, next_state, done)

                print(
                    f"[RL-EP] {result['episode']}/{episodes} reward={result['reward']:.1f} len={result['length']} epsilon={result['final_epsilon']:.3f} (process {result.get('process_id', 'unknown')})"
                )

    else:
        # Sequential execution (original code)
        for ep in range(1, episodes + 1):
            env = RLSandboxEnv(
                seed=42 + ep,
                intervention_interval=intervention_interval,
                init_pop_min=init_pop_min,
                init_pop_max=init_pop_max,
                enable_llm=enable_llm,
                llm_reward_freq=llm_reward_freq,
                max_llm_calls=max_llm_calls,
                llm_batch_only=llm_batch_only,
            )  # vary seed & start
            state = env.reset()
            total_reward = 0.0
            pop_sum = 0.0
            pop_count = 0
            for _ in range(max_ticks):
                action = agent.select_action(state)
                next_state, reward, done, info = env.step(action)
                agent.update(state, action, reward, next_state, done)
                total_reward += reward
                state = next_state
                pop_sum += state["population"]
                pop_count += 1
                tick_val = info.get("tick", -1)
                if tick_val != -1 and (tick_val % 500 == 0 or done):
                    print(
                        f"[RL] ep={ep} tick={tick_val} pop={state['population']} action={ACTION_NAMES[action]} reward={reward} cum={total_reward:.1f}"
                    )
                if done:
                    break
            episode_rewards.append(total_reward)
            episode_lengths.append(tick_val if tick_val != -1 else max_ticks)
            # Track average population for this episode
            episode_populations.append(pop_sum / pop_count if pop_count > 0 else float("nan"))
            print(
                f"[RL-EP] {ep}/{episodes} reward={total_reward:.1f} len={episode_lengths[-1]} epsilon={agent.epsilon:.3f} (sequential)"
            )
            # Decay epsilon
            agent.epsilon = max(epsilon_min, agent.epsilon * epsilon_decay)

    avg_reward = sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0.0
    avg_length = sum(episode_lengths) / len(episode_lengths) if episode_lengths else 0.0
    print(
        f"[RL-SUMMARY] episodes={episodes} avg_reward={avg_reward:.2f} avg_length={avg_length:.1f} final_epsilon={agent.epsilon:.3f}"
    )

    if save_path:
        try:
            serializable = {str(k): v for k, v in agent.q.items()}
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(serializable, f)
            print(f"[RL-TRAIN] Saved Q-table with {len(agent.q)} states to {save_path}")
        except Exception as e:
            print(f"[RL-TRAIN] Failed to save Q-table: {e}")

    return {
        "episode_rewards": episode_rewards,
        "episode_lengths": episode_lengths,
        "avg_reward": avg_reward,
        "avg_length": avg_length,
        "final_epsilon": agent.epsilon,
        "states": len(agent.q),
        "episode_populations": episode_populations,
    }


def select_qtable_for_population(pop_min: int, pop_max: int) -> str:
    """
    Automatically select the appropriate Q-table based on population range.

    Args:
        pop_min: Minimum population in the range
        pop_max: Maximum population in the range

    Returns:
        Path to the appropriate Q-table file
    """
    # Define the population ranges used in training
    pop_ranges = [
        (50, 100),  # Small population range
        (100, 300),  # Medium-small population range
        (300, 500),  # Medium population range
        (500, 1000),  # Medium-large population range
        (1000, 1800),  # Large population range
    ]

    # Calculate the center of the requested range
    pop_center = (pop_min + pop_max) / 2

    # Find the closest matching range
    best_match = None
    min_distance = float("inf")

    for range_min, range_max in pop_ranges:
        range_center = (range_min + range_max) / 2
        distance = abs(pop_center - range_center)

        if distance < min_distance:
            min_distance = distance
            best_match = (range_min, range_max)

    if best_match:
        qtable_path = f"artifacts/models/qtable_pop_{best_match[0]}_{best_match[1]}.json"

        # Check if the Q-table file exists
        import os

        if os.path.exists(qtable_path):
            return qtable_path
        else:
            print(
                f"[RL-CONTROL] Warning: Q-table {qtable_path} not found, will use closest available"
            )

            # Find the closest existing Q-table
            existing_qtables = [
                f
                for f in os.listdir("artifacts/models")
                if f.startswith("qtable_pop_") and f.endswith(".json")
            ]
            if existing_qtables:
                # Sort by population range center distance
                existing_qtables.sort(key=lambda f: abs(pop_center - get_qtable_center(f)))
                return existing_qtables[0]
            else:
                raise ValueError(f"No Q-table files found for population range {pop_min}-{pop_max}")

    raise ValueError(f"Could not find appropriate Q-table for population range {pop_min}-{pop_max}")


def get_qtable_center(qtable_filename: str) -> float:
    """Extract the population center from a Q-table filename."""
    try:
        parts = qtable_filename.replace("qtable_pop_", "").replace(".json", "").split("_")
        if len(parts) == 2:
            pop_min, pop_max = int(parts[0]), int(parts[1])
            return (pop_min + pop_max) / 2
    except (ValueError, IndexError):
        pass
    return float("inf")


def run_simulation_with_rl_control(
    num_ticks: int = 2000,
    qtable_path: str = None,
    control_interval: int = 10,
    init_pop_min: int = 330,
    init_pop_max: int = 350,
):
    """
    Run the core simulation with periodic RL agent control decisions.

    Args:
        num_ticks: Total ticks to simulate
        qtable_path: Path to trained Q-table file (if None, auto-select based on population)
        control_interval: Ticks between RL decisions
        init_pop_min/max: Initial population range
    """
    # Auto-select Q-table if not provided
    if not qtable_path:
        qtable_path = select_qtable_for_population(init_pop_min, init_pop_max)
        print(f"[RL-CONTROL] Auto-selected Q-table: {qtable_path}")

    if not qtable_path:
        raise ValueError(
            "Must provide qtable_path or enable auto-selection with valid population range"
        )

    # Load trained Q-table
    agent = TabularQLearningAgent(
        num_actions=len(ACTION_NAMES),
        epsilon=0.0,  # No exploration - use trained policy
        lr=0.0,  # No learning
        gamma=0.95,
        pop_bin_size=10,
        food_bin_size=500,
        births_cap=5,
        starv_cap=5,
    )

    try:
        with open(qtable_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, qvals in data.items():
            try:
                state_key = (
                    tuple(int(x) for x in k.strip("()").split(",")) if k.startswith("(") else k
                )
            except Exception:
                state_key = k
            agent.q[state_key] = qvals
        print(f"[RL-CONTROL] Loaded Q-table with {len(agent.q)} states from {qtable_path}")
    except Exception as e:
        raise ValueError(f"Failed to load Q-table from {qtable_path}: {e}")

    print(f"[RL-CONTROL] Starting simulation with RL control every {control_interval} ticks")
    print(f"[RL-CONTROL] Using Q-table: {qtable_path}")
    print(f"[RL-CONTROL] Initial population range: {init_pop_min}-{init_pop_max}")

    # Create a simplified simulation loop with RL control
    from core_sim import _configure_environment_flags, _parse_features
    from world.engine import WorldEngine
    import time

    # Setup environment (similar to core_sim)
    features = _parse_features()
    _configure_environment_flags(features)

    # Create world
    world = WorldEngine(seed=42)

    # Apply conservative wave settings like core_sim
    if getattr(world, "wave_enabled", False):
        world.abundance_cycle_length = 480
        world.fertility_wave_length = 360
        world.mortality_wave_length = 420
        world.resource_wave_amplitude = 0.15
        world.fertility_wave_amplitude = 0.12
        world.mortality_wave_amplitude = 0.08

    # Bootstrap initial population
    from tribes.tribal_manager import TribalManager
    from tribes.tribe import TribalRole
    from npcs.npc import NPC

    # Create tribal manager if world doesn't have one
    if not hasattr(world, "tribal_manager"):
        tm = TribalManager()
        # Create a default tribe for bootstrapping
        default_tribe_name = "rl_control_tribe"
        founder_id = "rl_founder"
        founder = NPC(name=founder_id, coordinates=(0, 0), faction_id=default_tribe_name)
        world.get_chunk(0, 0).npcs.append(founder)
        from factions.faction import Faction

        world.factions[default_tribe_name] = Faction(name=default_tribe_name, territory=[(0, 0)])
        world.factions[default_tribe_name].add_member(founder.name)
        tm.create_tribe(default_tribe_name, founder_id, (0, 0))
        tm.tribes[default_tribe_name].add_member(founder_id, TribalRole.LEADER)
    else:
        tm = world.tribal_manager

    target_population = random.randint(init_pop_min, init_pop_max)
    current_pop = sum(len(ch.npcs) for ch in world.active_chunks.values())
    spawn_needed = max(0, target_population - current_pop)

    roles = list(TribalRole)
    tribe_names = list(tm.tribes.keys())
    ri = 0
    while spawn_needed > 0 and tribe_names:
        tname = tribe_names[ri % len(tribe_names)]
        loc = getattr(tm.tribes[tname], "location", (0, 0))
        npc_id = f"{tname.lower()}_boot_{spawn_needed}"
        npc = NPC(name=npc_id, coordinates=loc, faction_id=tname)
        try:
            tm.tribes[tname].add_member(npc_id, random.choice(roles))
            world.factions[tname].add_member(npc.name)
            world.get_chunk(*loc).npcs.append(npc)
            world.activate_chunk(
                *loc
            )  # Activate the chunk so it's included in population calculations
        except Exception:
            pass
        spawn_needed -= 1
        ri += 1

    # Provision food
    for ch in world.active_chunks.values():
        ch.resources["food"] = max(ch.resources.get("food", 0), 200)
        ch.resources["plant"] = max(ch.resources.get("plant", 0), 150)

    print(
        f"[RL-CONTROL] Starting simulation with {sum(len(ch.npcs) for ch in world.active_chunks.values())} initial population"
    )

    # Main simulation loop with RL control
    start_time = time.time()
    population_history = []

    for tick in range(num_ticks):
        # Standard world tick
        world.world_tick()

        # RL control decision every N ticks
        if tick % control_interval == 0:
            try:
                # Use same state collection as training environment
                diag = _collect_diagnostics(world)
                state_features = {
                    "population": diag.get("population", 0),
                    "food": diag.get("total_food", 0),
                    "births": diag.get("births", 0),
                    "deaths_starv": diag.get("deaths_starv", 0),
                    "deaths_nat": diag.get("deaths_natural", 0),
                }
                action_idx = agent.select_action(state_features)
                action_name = ACTION_NAMES[action_idx]

                # Apply RL action
                if action_name == "repro_up":
                    cur = world.balance_params.get("REPRO_BASE_CHANCE", 0.03)
                    world.balance_params["REPRO_BASE_CHANCE"] = min(0.06, cur + 0.002)
                elif action_name == "repro_down":
                    cur = world.balance_params.get("REPRO_BASE_CHANCE", 0.03)
                    world.balance_params["REPRO_BASE_CHANCE"] = max(0.02, cur - 0.002)
                elif action_name == "mortality_amp_up" and hasattr(
                    world, "mortality_wave_amplitude"
                ):
                    world.mortality_wave_amplitude = min(
                        0.20, getattr(world, "mortality_wave_amplitude", 0.08) + 0.01
                    )
                elif action_name == "mortality_amp_down" and hasattr(
                    world, "mortality_wave_amplitude"
                ):
                    world.mortality_wave_amplitude = max(
                        0.02, getattr(world, "mortality_wave_amplitude", 0.08) - 0.01
                    )

                # Track population
                current_pop = sum(len(ch.npcs) for ch in world.active_chunks.values())
                population_history.append(current_pop)

                # Log progress
                if tick % (control_interval * 20) == 0:  # Every 20 RL decisions
                    avg_pop = (
                        sum(population_history[-20:]) / min(20, len(population_history))
                        if population_history
                        else 0
                    )
                    print(
                        f"[RL-CONTROL] tick={tick} pop={current_pop} avg_recent={avg_pop:.1f} action={action_name}"
                    )

            except Exception as e:
                if tick % (control_interval * 100) == 0:  # Log errors occasionally
                    print(f"[RL-CONTROL] Error at tick {tick}: {e}")

    # Final statistics
    end_time = time.time()
    final_pop = sum(len(ch.npcs) for ch in world.active_chunks.values())
    avg_pop = sum(population_history) / len(population_history) if population_history else 0
    pop_stability = (
        1.0 - (sum(abs(p - 300) for p in population_history) / len(population_history)) / 300
        if population_history
        else 0
    )

    print("[RL-CONTROL] Simulation complete!")
    print(f"[RL-CONTROL] Total time: {end_time - start_time:.1f} seconds")
    print(f"[RL-CONTROL] Final population: {final_pop}")
    print(f"[RL-CONTROL] Average population: {avg_pop:.1f}")
    print(f"[RL-CONTROL] Population stability (target: 300): {pop_stability:.3f}")
    print(f"[RL-CONTROL] RL decisions made: {len(population_history)}")


def run_single_episode(
    ep: int,
    max_ticks: int,
    epsilon: float,
    lr: float,
    gamma: float,
    pop_bin_size: int,
    food_bin_size: int,
    births_cap: int,
    starv_cap: int,
    init_pop_min: int,
    init_pop_max: int,
    intervention_interval: int,
    enable_llm: bool,
    llm_reward_freq: int,
    max_llm_calls: int,
    llm_batch_only: bool,
) -> Dict[str, Any]:
    """Run a single RL episode and return the results."""
    import os

    process_id = os.getpid()  # Get process ID for logging

    print(f"[RL-PROCESS-{process_id}] Starting episode {ep}")

    agent = TabularQLearningAgent(
        num_actions=len(ACTION_NAMES),
        epsilon=epsilon,
        lr=lr,
        gamma=gamma,
        pop_bin_size=pop_bin_size,
        food_bin_size=food_bin_size,
        births_cap=births_cap,
        starv_cap=starv_cap,
    )

    env = RLSandboxEnv(
        seed=42 + ep,
        intervention_interval=intervention_interval,
        init_pop_min=init_pop_min,
        init_pop_max=init_pop_max,
        enable_llm=enable_llm,
        llm_reward_freq=llm_reward_freq,
        max_llm_calls=max_llm_calls,
        llm_batch_only=llm_batch_only,
    )

    state = env.reset()
    total_reward = 0.0
    pop_sum = 0.0
    pop_count = 0
    experiences = []  # Store (state, action, reward, next_state, done) tuples

    for tick in range(max_ticks):
        action = agent.select_action(state)
        next_state, reward, done, info = env.step(action)

        # Store experience for later Q-table updates
        experiences.append((state, action, reward, next_state, done))

        total_reward += reward
        state = next_state
        pop_sum += state["population"]
        pop_count += 1

        if done:
            break

    tick_val = info.get("tick", max_ticks)
    avg_population = pop_sum / pop_count if pop_count > 0 else float("nan")

    print(
        f"[RL-PROCESS-{process_id}] Episode {ep} completed: reward={total_reward:.1f}, length={tick_val}, avg_pop={avg_population:.1f}"
    )

    return {
        "episode": ep,
        "reward": total_reward,
        "length": tick_val,
        "avg_population": avg_population,
        "experiences": experiences,
        "final_epsilon": agent.epsilon,
        "process_id": process_id,
    }


if __name__ == "__main__":
    run_simple_rl_episode()
