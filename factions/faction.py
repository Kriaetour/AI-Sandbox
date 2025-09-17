from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional
import random
import logging


# Name generator for unique NPC names
def generate_unique_name(faction_name: str, used_names: set) -> str:
    """Generate a unique human-like name for an NPC."""
    # Name components inspired by various cultures and mythologies
    first_parts = [
        "Ael",
        "Bryn",
        "Cael",
        "Dara",
        "Ely",
        "Finn",
        "Gwen",
        "Hald",
        "Ira",
        "Jor",
        "Kael",
        "Lira",
        "Mael",
        "Nora",
        "Oren",
        "Pria",
        "Quil",
        "Rhea",
        "Soren",
        "Tara",
        "Ulf",
        "Vera",
        "Wynn",
        "Xara",
        "Yara",
        "Zane",
        "Arin",
        "Bela",
        "Cora",
        "Dain",
        "Elow",
        "Fara",
        "Gorr",
        "Hela",
        "Ivor",
        "Jala",
        "Kira",
        "Loth",
        "Mira",
        "Nael",
        "Orin",
        "Pael",
        "Quor",
        "Rael",
        "Sira",
        "Tael",
        "Uria",
        "Vael",
        "Wren",
        "Xael",
    ]

    second_parts = [
        "an",
        "el",
        "in",
        "or",
        "us",
        "a",
        "e",
        "i",
        "o",
        "u",
        "ar",
        "en",
        "il",
        "on",
        "ur",
        "ia",
        "ea",
        "io",
        "oa",
        "ua",
        "ath",
        "eth",
        "ith",
        "oth",
        "uth",
        "ara",
        "era",
        "ira",
        "ora",
        "ura",
    ]

    # Try up to 100 times to generate a unique name
    for _ in range(100):
        first = random.choice(first_parts)
        second = random.choice(second_parts)
        name = f"{first}{second}"

        # Add a tribal identifier if needed to ensure uniqueness
        if name not in used_names:
            return name

    # Fallback: add a number suffix
    counter = 0
    while True:
        name = f"{random.choice(first_parts)}{random.choice(second_parts)}{counter}"
        if name not in used_names:
            return name
        counter += 1


@dataclass
class Faction:
    """Represents a single faction or civilization."""

    name: str
    npc_ids: set = field(default_factory=set)
    territory: List[Tuple[int, int]] = field(default_factory=list)
    resources: Dict[str, float] = field(
        default_factory=lambda: {"food": 0.0, "Wood": 0.0, "Ore": 0.0}
    )
    ambition: Optional[str] = None

    # New: Relationships with other factions
    relationships: Dict[str, float] = field(default_factory=dict)

    # Technology system integration
    tribe_id: Optional[str] = None  # Link to tribal technology system

    memory: Dict[str, Any] = field(
        default_factory=lambda: {
            "events": [],
            "rumors": [],
            "opinions": {},
            "sayings": [],
            "grudges": {},  # Long-term negative attitudes toward other factions
            "alliances": {},  # Historical alliance data
        }
    )

    wars_fought: int = 0  # Number of wars this faction has participated in

    # Economy instrumentation (not serialized yet to keep persistence lean)
    def __post_init__(self):  # keep existing logger init but extend
        self.logger = logging.getLogger(f"Faction.{self.name}")
        # Last recorded resource totals for delta computation
        self._econ_last = {"food": 0.0, "Wood": 0.0, "Ore": 0.0}
        # Rolling history of last N deltas
        self._econ_history = []  # list of dicts: {tick, dFood, dWood, dOre, pop}
        self._econ_history_limit = 300
        # Starvation pressure accumulator (consumption deficits add, surplus decays)
        self._starvation_pressure = 0.0
        # Opinion decay accumulator to apply periodic soft reversion to neutral (0.0)
        self._opinion_decay_counter = 0

    # ================= OPINION SYSTEM =================
    def ensure_opinion_entry(self, other: str):
        if other == self.name:
            return
        opinions = self.memory.setdefault("opinions", {})
        if other not in opinions:
            opinions[other] = 0.0  # neutral baseline

    def adjust_opinion(self, other: str, delta: float, clamp: float = 1.0):
        """Adjust opinion toward another faction with clamping and diminishing returns.

        Non-linear taper: as |opinion| approaches clamp, effective delta shrinks.
        """
        try:
            if other == self.name:
                return
            self.ensure_opinion_entry(other)
            opinions = self.memory["opinions"]
            cur = opinions[other]
            # Taper factor (1 - (|cur|/clamp)^p)
            p = 1.3
            taper = max(0.0, 1.0 - (abs(cur) / max(1e-6, clamp)) ** p)
            effective = delta * taper
            new_val = max(-clamp, min(clamp, cur + effective))
            opinions[other] = new_val
            # Record as event (compact)
            try:
                self.record_event(
                    None,
                    kind="opinion_change",
                    data={
                        "other": other,
                        "delta": round(effective, 3),
                        "new": round(new_val, 3),
                    },
                )
            except Exception:
                pass
        except Exception:
            pass

    def decay_opinions(self, rate: float = 0.01):
        """Softly decay all opinions toward neutral (0) each call."""
        try:
            opinions = self.memory.get("opinions")
            if not opinions:
                return
            for k, v in list(opinions.items()):
                if abs(v) < 1e-4:
                    continue
                sign = 1 if v > 0 else -1
                mag = max(0.0, abs(v) - rate)
                opinions[k] = mag * sign
        except Exception:
            pass

    def econ_snapshot(self, tick: int):
        """Capture per-faction resource delta since last snapshot for audit."""
        cur = {
            "food": self.resources.get("food", 0.0),
            "Wood": self.resources.get("Wood", 0.0),
            "Ore": self.resources.get("Ore", 0.0),
        }
        delta = {k: cur[k] - self._econ_last.get(k, 0.0) for k in cur}
        entry = {
            "tick": tick,
            "dFood": delta["food"],
            "dWood": delta["Wood"],
            "dOre": delta["Ore"],
            "pop": len(self.npc_ids),
        }
        self._econ_history.append(entry)
        if len(self._econ_history) > self._econ_history_limit:
            self._econ_history.pop(0)
        self._econ_last = cur
        return entry

    def process_tick(self, world):
        """Process one tick of faction logic - moved from WorldEngine._faction_tick"""
        self.logger.debug(f"process_tick called for {self.name}")

        # ===== RESOURCE GATHERING =====
        # Gather resources from faction's territory
        self.gather_resources(world)
        # ===== CONSUMPTION =====
        self.consume_resources(world)
        # ===== DEMOGRAPHICS (Mortality & Birth) =====
        self._process_demographics(world)

    def gather_resources(self, world):
        """Harvest a fraction of available stock from chunks in territory (depletion-aware).

        Harvest Model:
        - Harvest fraction depends on population pressure: base 5% + (pop * 0.2%) capped at 25% per tick
        - Each resource type harvested independently; chunk stock reduced by harvested amount
        - Mapping: plant/animal/fish -> food; mineral -> Ore; Wood stays Wood
        """
        if (not self.territory) and world:
            # Infer territory from active chunk NPC presence (fallback for factions created without explicit territory)
            try:
                inferred = []
                for ch in world.active_chunks.values():
                    for npc in ch.npcs:
                        if getattr(npc, "faction_id", None) == self.name:
                            inferred.append(ch.coordinates)
                            break
                if inferred:
                    for coord in inferred:
                        if coord not in self.territory:
                            self.territory.append(coord)
                            try:
                                self.record_event(
                                    world,
                                    kind="territory_gain",
                                    data={"coords": coord, "mode": "inferred"},
                                )
                            except Exception:
                                pass
                    self.logger.debug(f"Inferred territory for {self.name}: {self.territory}")
            except Exception:
                pass
        if not self.territory or not world:
            self.logger.debug(
                f"gather_resources called for {self.name}, territory: {self.territory}"
            )
            return
        pop = len(self.npc_ids)
        # More generous harvest fraction to allow sustainable population
        harvest_fraction = min(0.03 + pop * 0.001, 0.15)  # base 3% + 0.1% per NPC, max 15%
        total_food = total_wood = total_ore = 0.0
        for chunk_coords in self.territory:
            chunk = world.get_chunk(chunk_coords[0], chunk_coords[1])
            if not chunk or not chunk.resources:
                continue
            # Iterate over a copy to compute harvests
            for rtype, stock in list(chunk.resources.items()):
                if stock <= 0:
                    continue
                take = stock * harvest_fraction
                if rtype in ["plant", "animal", "fish"]:
                    total_food += take
                elif rtype == "mineral":
                    total_ore += take
                elif rtype == "Wood":
                    total_wood += take
                # Deplete stock
                chunk.resources[rtype] = max(0.0, stock - take)
        self.resources["food"] += total_food
        self.resources["Wood"] += total_wood
        self.resources["Ore"] += total_ore

        # Apply technology multipliers
        self._apply_technology_multipliers()

        self.logger.debug(
            f"{self.name} harvested (hf={harvest_fraction*100:.1f}%) Food:{total_food:.2f} Wood:{total_wood:.2f} Ore:{total_ore:.2f}"
        )

    def _apply_technology_multipliers(self):
        """Apply technology multipliers to faction resources."""
        if not self.tribe_id:
            return

        try:
            from technology_system import technology_manager

            multipliers = technology_manager.calculate_tribe_multipliers(self.tribe_id)

            # Apply resource multipliers
            for resource_key in ["food", "Wood", "Ore"]:
                if resource_key in self.resources:
                    multiplier = multipliers.get(resource_key.lower(), 1.0)
                    if multiplier != 1.0:
                        original = self.resources[resource_key]
                        self.resources[resource_key] *= multiplier
                        gained = self.resources[resource_key] - original
                        if gained > 0:
                            self.logger.debug(
                                f"{self.name} technology bonus: +{gained:.2f} {resource_key} ({multiplier:.2f}x)"
                            )
        except ImportError:
            # Technology system not available
            pass
        except Exception as e:
            self.logger.debug(f"Technology multiplier application failed: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert faction to dictionary for serialization (safe, non-recursive, excludes private/non-serializable fields)"""
        return {
            "name": self.name,
            "npc_ids": list(self.npc_ids),
            "territory": list(self.territory),
            "resources": dict(self.resources),
            "ambition": self.ambition,
            "relationships": dict(self.relationships),
            "memory": dict(self.memory),
            "wars_fought": self.wars_fought,
        }

    def serialize(self) -> Dict[str, Any]:
        """Convert faction to lightweight dictionary for web API visualization."""
        return {
            "id": id(self),  # Use object ID for unique identification
            "name": self.name,
            "population": len(self.npc_ids),
            "territory_count": len(self.territory),
            "resources": dict(self.resources),
            "ambition": self.ambition,
            "relationship_count": len(self.relationships),
        }

    # ================= CONSUMPTION LOGIC (Step D) =================
    def consume_resources(self, world, tick_scale: int = 1):
        """Apply per-tick resource consumption based on population.

        Model:
        - Base daily requirement per NPC (24h = 1440 ticks if 1 tick = 1 minute):
            food: 1.0 units/day -> per tick = 1/1440
            Wood/Ore not consumed metabolically (reserved for future crafting), but we track deficits.
        - Starvation counter increments when faction food < requirement.
        - If persistent deficit exceeds threshold, future mortality system will act (not yet implemented).
        - Scales linearly with population; supports batch scaling via tick_scale (e.g., hourly consumption) later.
        """
        pop = len(self.npc_ids)
        if pop == 0:
            return
        params = getattr(world, "balance_params", {}) if world else {}
        FOOD_PER_DAY = params.get("FOOD_PER_DAY_PER_NPC", 1.0)
        # Per-NPC per-tick food need
        TICKS_PER_DAY = (
            world.MINUTES_PER_HOUR * world.HOURS_PER_DAY
            if hasattr(world, "MINUTES_PER_HOUR")
            else 1440
        )
        food_need_per_tick = (FOOD_PER_DAY / TICKS_PER_DAY) * pop * tick_scale

        # Apply technology effects to food consumption
        tech_food_multiplier = 1.0
        if self.tribe_id:
            try:
                from technology_system import technology_manager
                multipliers = technology_manager.calculate_tribe_multipliers(self.tribe_id)
                # Technologies might reduce consumption (e.g., farming efficiency)
                tech_food_multiplier = multipliers.get("food_consumption", 1.0)
            except ImportError:
                pass
            except Exception:
                pass

        food_need_per_tick *= tech_food_multiplier

        current_food = self.resources.get("food", 0.0)
        if current_food >= food_need_per_tick:
            self.resources["food"] = current_food - food_need_per_tick
            # Reset/decay starvation pressure (simple decay placeholder)
            starvation = getattr(self, "_starvation_pressure", 0.0)
            decay = params.get("STARV_DECAY_PER_TICK", 0.1)
            self._starvation_pressure = max(0.0, starvation - decay)
        else:
            # All food consumed; deficit adds to starvation pressure
            self.resources["food"] = 0.0
            deficit = food_need_per_tick - current_food
            starvation = getattr(self, "_starvation_pressure", 0.0)
            self._starvation_pressure = starvation + deficit
            # Hook for audit (world will poll later when mortality added)
        if pop > 0 and self._econ_history:
            # Annotate last econ history entry with consumption for debugging (non-persistent)
            try:
                self._econ_history[-1]["consumed_food"] = round(food_need_per_tick, 4)
                self._econ_history[-1]["starv_pressure"] = round(
                    getattr(self, "_starvation_pressure", 0.0), 4
                )
            except Exception:
                pass

    # ================= DEMOGRAPHICS (Mortality & Birth Cycle) =================
    def _process_demographics(self, world):
        """Apply starvation-based mortality and capacity-driven reproduction.

        Mortality (unchanged for now):
        - Starvation pressure beyond threshold generates per-NPC death probability with adaptive relief.

        Reproduction (refactored):
        - Estimate sustainable capacity from recent net food deltas (moving window) -> faction_capacity_est.
        - Effective global fertility factor (published to world) derived from resource adequacy & low pressure.
        - Expected births: pop * fertility_factor * (1 - pop / capacity_est).
          * If capacity_est <= pop, growth term -> 0 (no births under deficit/crowding).
        - Sample births via integer + fractional probability; cap burst per tick.
        - Starvation pressure reduces fertility smoothly; severe pressure can zero births.

        Test Compatibility:
        - Existing tests expect at least one birth under surplus after multiple attempts; fractional sampling preserves this.
        """
        try:
            pop = len(self.npc_ids)
            # No artificial minimum population floor: allow population to drop below 100 if resources are insufficient
            if pop == 0:
                return
            pressure = getattr(self, "_starvation_pressure", 0.0)
            # Global grace period to prevent immediate deaths early in simulation
            params = getattr(world, "balance_params", {}) if world else {}
            grace_ticks = params.get("MORTALITY_GRACE_TICKS", 1000)
            world_tick = getattr(world, "_tick_count", 0)
            in_grace = world_tick < grace_ticks
            # Crisis system deprecated: intrinsic ecological controls now handle stabilization.
            small_pop_clamp = params.get("LOW_FACTION_POP_PRESSURE_CLAMP", 5)
            # Clamp pressure for very small factions to avoid runaway deaths
            if pop <= small_pop_clamp:
                STARV_THRESHOLD_BASE = params.get("STARV_THRESHOLD", 3.0)
                pressure = min(pressure, STARV_THRESHOLD_BASE + 2.0)
                self._starvation_pressure = pressure
            # --- Carrying Capacity Soft Pressure ---
            # Estimate sustainable population from recent food delta (use last econ history entries)
            # If harvesting < consumption, apply overcrowd penalty that feeds starvation pressure.
            try:
                sustainable_pop = None
                if self._econ_history:
                    # Use last K entries to estimate average net food gain per tick
                    K = 20
                    recent = self._econ_history[-K:]
                    avg_dfood = sum(e.get("dFood", 0.0) for e in recent) / max(1, len(recent))
                    # Per-tick consumption currently ~ pop * (1/1440); invert to find sustainable pop
                    per_capita_need = 1.0 / (world.MINUTES_PER_HOUR * world.HOURS_PER_DAY)
                    if per_capita_need > 0 and avg_dfood > 0:
                        sustainable_pop = max(0.0, avg_dfood / per_capita_need)
                if sustainable_pop is not None and sustainable_pop < pop and not in_grace:
                    # Overcrowd ratio
                    ratio = pop / max(1.0, sustainable_pop + 1e-6)
                    # Add overcrowd penalty scaled by how far over capacity we are
                    slope = params.get("CAP_OVER_PENALTY_SLOPE", 0.05)
                    overcrowd_penalty = (ratio - 1.0) * slope
                    if overcrowd_penalty > 0:
                        self._starvation_pressure += overcrowd_penalty
                        pressure = self._starvation_pressure
            except Exception:
                pass
            # --- Starvation Mortality ---
            STARV_DEATH_THRESHOLD = params.get("STARV_THRESHOLD", 3.0)
            STARV_DEATH_RATE = params.get("STARV_DEATH_RATE", 0.02)
            STARV_DEATH_CHANCE_MAX = params.get("STARV_DEATH_CHANCE_MAX", 0.35)
            # Staged starvation gating (Stage 0->3)
            # Stage definitions relative to threshold
            #   Stage 0: pressure < 0.4 * threshold (normal)
            #   Stage 1: 0.4..1.0 * threshold (fertility dampening)
            #   Stage 2: threshold .. threshold+2 (fertility zero, mortality ramp begins late)
            #   Stage 3: > threshold+2 (full mortality severity)
            starvation_stage = 0
            if pressure >= 0.4 * STARV_DEATH_THRESHOLD:
                starvation_stage = 1
            if pressure >= STARV_DEATH_THRESHOLD:
                starvation_stage = 2
            if pressure >= STARV_DEATH_THRESHOLD + 2.0:
                starvation_stage = 3
            # Adaptive relief state (stored on faction lazily)
            adapt_window = params.get("ADAPT_DEATH_SPIKE_WINDOW", 150)
            adapt_count_thresh = params.get("ADAPT_DEATH_SPIKE_COUNT", 5)
            relief_duration = params.get("ADAPT_RELIEF_DURATION", 400)
            relief_mult = params.get("ADAPT_RELIEF_MULT", 0.6)
            now_tick = getattr(world, "_tick_count", 0)
            if not hasattr(self, "_recent_starv_deaths"):
                self._recent_starv_deaths = []  # list of (tick, count)
            if not hasattr(self, "_relief_until"):
                self._relief_until = -1
            ramp_ticks = params.get("MORTALITY_RAMP_TICKS", 2000)
            deaths = 0
            # Only allow starvation deaths if there was an active food deficit this tick
            had_deficit_this_tick = False
            if self._econ_history:
                last_entry = self._econ_history[-1]
                # If consumed_food > dFood, there was a deficit
                if last_entry.get("consumed_food", 0) > last_entry.get("dFood", 0):
                    had_deficit_this_tick = True
            if pressure > STARV_DEATH_THRESHOLD and not in_grace and had_deficit_this_tick:
                # Per-pop death probability with linear ramp after grace
                excess = pressure - STARV_DEATH_THRESHOLD
                base_p = excess * STARV_DEATH_RATE
                # Linear ramp factor from end of grace to grace + ramp_ticks
                if world_tick < grace_ticks + ramp_ticks:
                    progress = (world_tick - grace_ticks) / max(1, ramp_ticks)
                    progress = max(0.0, min(1.0, progress))
                    base_p *= 0.25 + 0.75 * progress  # starts at 25% of full severity
                # Apply adaptive relief multiplier if active
                if now_tick <= getattr(self, "_relief_until", -1):
                    base_p *= relief_mult

                # Apply technology effects to mortality
                if self.tribe_id:
                    try:
                        from technology_system import technology_manager
                        multipliers = technology_manager.calculate_tribe_multipliers(self.tribe_id)
                        mortality_reduction = multipliers.get("mortality", 0.0)
                        base_p *= (1.0 - mortality_reduction)
                    except ImportError:
                        pass
                    except Exception:
                        pass

                # Apply population wave multiplier for mortality
                try:
                    if hasattr(world, "calculate_mortality_wave_multiplier") and getattr(
                        world, "wave_enabled", False
                    ):
                        mortality_wave_mult = world.calculate_mortality_wave_multiplier()
                        base_p *= mortality_wave_mult
                except Exception:
                    pass

                # (Former crisis mortality dampening removed)
                p = min(STARV_DEATH_CHANCE_MAX, base_p)
                # Expected deaths ~ binomial(pop, p)
                # Sample deaths individually for now (could approximate to speed up)
                survivors = []
                for npc_id in list(self.npc_ids):
                    if random.random() < p:
                        # Remove NPC globally
                        self._demog_remove_npc(npc_id, world, reason="starvation")
                        deaths += 1
                    else:
                        survivors.append(npc_id)
                self.npc_ids = survivors
                if deaths > 0:
                    try:
                        world._audit_starvation_deaths += deaths
                        world._audit_starvation_deaths_tick += deaths
                    except Exception:
                        pass
                    self.logger.warning(
                        f"{self.name}: {deaths} NPCs died of starvation (pressure={pressure:.2f}, p={p:.2f})."
                    )
                    # Track recent starvation deaths for adaptive relief
                    self._recent_starv_deaths.append((now_tick, deaths))
                    # Prune window
                    self._recent_starv_deaths = [
                        (t, d)
                        for (t, d) in self._recent_starv_deaths
                        if now_tick - t <= adapt_window
                    ]
                    total_recent = sum(d for _, d in self._recent_starv_deaths)
                    if total_recent >= adapt_count_thresh and now_tick > getattr(
                        self, "_relief_until", -1
                    ):
                        # Trigger relief period
                        self._relief_until = now_tick + relief_duration
                        self.logger.info(
                            f"{self.name}: Adaptive relief triggered (recent_deaths={total_recent}) until tick {self._relief_until}."
                        )
            # --- Capacity-Based Reproduction ---
            food_total = self.resources.get("food", 0.0)
            # Estimate recent net food delta (production - consumption) to infer sustainable capacity
            capacity_est = None
            try:
                if self._econ_history:
                    window = 30
                    recent = self._econ_history[-window:]
                    avg_dfood = sum(e.get("dFood", 0.0) for e in recent) / max(1, len(recent))
                    per_cap_need = (
                        (
                            params.get("FOOD_PER_DAY_PER_NPC", 1.0)
                            / (world.MINUTES_PER_HOUR * world.HOURS_PER_DAY)
                        )
                        if world
                        else (1.0 / 1440.0)
                    )
                    if per_cap_need > 0:
                        if avg_dfood > 0:
                            addl_support = avg_dfood / per_cap_need
                            capacity_est = pop + addl_support
                        else:
                            capacity_est = pop
                if capacity_est is None:
                    food_per_capita = food_total / max(1, pop)
                    capacity_est = pop + max(0.0, food_per_capita * 2.0)
                # Option B: Reserve-informed slack boost when large stored food relative to population
                if pop > 0:
                    food_per_capita = food_total / pop
                    reserve_threshold = params.get("RESERVE_SLACK_THRESHOLD", 25.0)
                    if food_per_capita > reserve_threshold:
                        # Add virtual slack up to 5x population or capped by reserves / (threshold*2)
                        virtual_slack = min(pop * 5.0, (food_per_capita - reserve_threshold) * 0.5)
                        capacity_est += virtual_slack
            except Exception:
                capacity_est = float(pop)
            # Publish partial contribution to world capacity estimate (simple sum later)
            try:
                # Accumulate on world for later averaging (lazy init list)
                if not hasattr(world, "_cap_samples"):
                    world._cap_samples = []
                world._cap_samples.append(capacity_est)
            except Exception:
                pass
            # Fertility factor baseline scales with surplus (capacity slack) & low starvation pressure
            slack = max(0.0, capacity_est - pop)
            slack_ratio = slack / max(1.0, capacity_est)
            # Pressure penalty (soft until 50% threshold then steep)
            threshold = params.get("STARV_THRESHOLD", 3.0)
            pressure_penalty = 1.0
            if pressure > 0:
                rel = pressure / max(0.1, threshold)
                if rel > 0.5:
                    pressure_penalty = max(
                        0.0, 1.0 - (rel - 0.5) * 0.8
                    )  # up to 80% reduction as pressure climbs
                else:
                    pressure_penalty = 1.0 - rel * 0.3  # mild reduction under low pressure
            fertility_factor = slack_ratio * pressure_penalty

            # Apply population wave multiplier for fertility
            try:
                if hasattr(world, "calculate_fertility_wave_multiplier") and getattr(
                    world, "wave_enabled", False
                ):
                    fertility_wave_mult = world.calculate_fertility_wave_multiplier()
                    fertility_factor *= fertility_wave_mult
            except Exception:
                pass
            # Apply staged starvation gating adjustments (acts before low-pop boost)
            if starvation_stage == 1:
                fertility_factor *= 0.6  # dampen reproduction early instead of deaths
            elif starvation_stage == 2:
                fertility_factor *= 0.15  # near-zero fertility, mortality starting
            elif starvation_stage == 3:
                fertility_factor = 0.0  # complete reproductive halt under severe starvation
            # Low-population boost (encourage recovery) similar to previous design
            low_pop_thresh = params.get("LOW_POP_THRESHOLD", 25)
            if pop < low_pop_thresh:
                fertility_factor *= params.get("LOW_POP_REPRO_MULT", 1.5)
            # (Former crisis fertility boost removed)
            # Clamp fertility
            fertility_factor = max(0.0, min(2.0, fertility_factor))
            # Fertility floor for populations - LESS AGGRESSIVE for more realistic growth
            if pop > 0:
                if pop <= 10 and fertility_factor < 0.15 and pressure < threshold * 0.4:
                    fertility_factor = 0.15
                elif pop <= 30 and fertility_factor < 0.08 and pressure < threshold * 0.3:
                    fertility_factor = 0.08
                elif pop <= 100 and fertility_factor < 0.04:
                    fertility_factor = 0.04
                elif pop <= 200 and fertility_factor < 0.02:
                    fertility_factor = 0.02
                # No upper limit fertility floor for high populations
            # Apply global reproduction throttle (world-level growth moderation)
            try:
                throttle = getattr(world, "_repro_throttle", 1.0)
                if throttle < 0.999:
                    pre = fertility_factor
                    fertility_factor *= throttle
                    if pre > 0 and fertility_factor / pre < 0.8 and random.random() < 0.05:
                        self.logger.debug(
                            f"{self.name}: fertility throttled {pre:.3f}->{fertility_factor:.3f} (global factor {throttle:.2f})"
                        )
            except Exception:
                pass
            # Defensive: ensure npc_ids remains a set (persistence or external code may coerce it)
            if not isinstance(self.npc_ids, set):
                try:
                    self.npc_ids = set(self.npc_ids)
                except Exception:
                    self.npc_ids = set()

            # Gentler early carrying blend: smooth ramp, capped at 0.25 minimum
            if pop < 240:
                # carrying_term = max(0.25, 1.0 - (pop / 240.0) ** 1.2)
                pass
            else:
                # carrying_term = 0.0
                if capacity_est > 0:
                    # carrying_term = max(0.0, 1.0 - (pop / capacity_est))
                    pass

            # Robust reserve-based slack/fertility: combine slack ratio and per-capita reserves
            food_per_capita = food_total / max(1, pop)
            reserve_threshold_scaled = 12.0
            slack_ratio = max(
                (food_per_capita / reserve_threshold_scaled),
                (capacity_est - pop) / max(1.0, capacity_est),
            )
            # Add reserve-based boost curve
            fertility_factor = slack_ratio * pressure_penalty
            fertility_factor += min(0.15, (food_per_capita / 200.0))

            # Apply technology effects to fertility
            if self.tribe_id:
                try:
                    from technology_system import technology_manager
                    multipliers = technology_manager.calculate_tribe_multipliers(self.tribe_id)
                    reproduction_bonus = multipliers.get("reproduction", 0.0)
                    fertility_factor += reproduction_bonus
                except ImportError:
                    pass
                except Exception:
                    pass

            # -------- LOGISTIC REPRODUCTION EQUILIBRIUM --------
            # Replace layered fertility floors with a transparent logistic model:
            # births = pop * r_eff * (1 - pop / K_eff) where:
            #   r_eff = r_base * fertility_factor * pressure_penalty (bounded)
            #   K_eff = capacity_est (augmented by reserves already)
            # Tiny population rescue: if pop < rescue_thresh and no starvation deficit, clamp to min births.
            # TUNING NOTES:
            # r_base controls intrinsic growth when population is far below carrying capacity (capacity_est).
            # Lower r_base -> slower recovery; higher r_base -> faster rebounds and larger oscillations.
            # Typical stable range with current mortality + starvation gating: 0.010 - 0.020.
            # Prefer world-level adaptive intrinsic growth if available
            r_base = getattr(world, "_adaptive_r_base", params.get("REPRO_R_BASE", 0.015))
            # Effective capacity
            K_eff = max(pop + 1.0, capacity_est)
            # Effective growth rate scales with fertility_factor (already includes reserves & pressure)
            r_eff = r_base * max(0.0, min(1.5, fertility_factor)) * pressure_penalty
            # Logistic term (ensure non-negative)
            growth_term = max(0.0, 1.0 - (pop / K_eff))
            expected_births = pop * r_eff * growth_term
            # Mild jitter (optional, low amplitude)
            if getattr(world, "enable_repro_jitter", False):
                spread = getattr(world, "repro_jitter_spread", 0.15)
                expected_births *= random.uniform(1.0 - spread, 1.0 + spread)
            # Rescue for very small pops if no active deficit this tick
            rescue_thresh = params.get("LOGISTIC_RESCUE_THRESHOLD", 12)
            if pop > 0 and pop <= rescue_thresh and pressure_penalty > 0.6:
                # Rescue threshold ensures extinction avoidance without inflating mid-band growth.
                expected_births = max(expected_births, 0.6)
            # Hard cap births relative to pop to avoid spikes: 8% per tick (<500) else 3%
            # Birth cap scaling: 8% (low-mid pops) / 3% (large pops) stabilizes against runaway exponential bursts.
            if pop < 500:
                max_births_tick = max(1, int(pop * 0.08))
            elif pop < 2000:
                max_births_tick = max(1, int(pop * 0.03))
            else:
                max_births_tick = max(1, int(pop * 0.01))  # For very high pops, stricter cap
            births = int(expected_births)
            fractional = expected_births - births
            if random.random() < fractional:
                births += 1
            births = min(births, max_births_tick)
            if births > 0 and pressure_penalty > 0.5:
                for _ in range(births):
                    self._demog_spawn_npc(world)
                    try:
                        world._audit_total_births += 1
                        world._audit_births_tick += 1
                    except Exception:
                        pass
            # Publish fertility factor (last faction wins; later we will aggregate explicitly)
            try:
                world.set_fertility_factor(fertility_factor)
            except Exception:
                pass
        except Exception as e:
            self.logger.error(f"Demographics processing error: {e}")

    def _demog_remove_npc(self, npc_id: str, world, reason: str):
        """Remove NPC by id from world chunks and faction set."""
        try:
            # Remove from chunks (optimized: break after found)
            for chunk in world.active_chunks.values():
                for i, npc in enumerate(chunk.npcs):
                    if npc.name == npc_id:
                        del chunk.npcs[i]
                        break
            # Remove from faction set
            self.npc_ids.discard(npc_id)
            self.logger.debug(f"Removed NPC {npc_id} due to {reason}.")
            try:
                self.record_event(world, kind="death", data={"npc": npc_id, "reason": reason})
            except Exception:
                pass
        except Exception:
            pass

    def _demog_spawn_npc(self, world):
        """Spawn a new NPC for this faction (simple birth event, optimized for set)."""
        try:
            from npcs import NPC  # local import to avoid cycles at module import time

            # Choose spawn location
            if self.territory:
                spawn_coords = random.choice(self.territory)
            else:
                spawn_coords = (0, 0)
            world.activate_chunk(*spawn_coords)

            # Generate a unique human-like name
            new_name = generate_unique_name(self.name, self.npc_ids)

            npc = NPC(name=new_name, coordinates=spawn_coords, faction_id=self.name, age=0)
            chunk = world.get_chunk(*spawn_coords)
            if npc not in chunk.npcs:
                chunk.npcs.append(npc)
            self.npc_ids.add(npc.name)
            self.logger.info(f"{self.name}: Birth event -> {npc.name} at {spawn_coords}")
            try:
                self.record_event(
                    world, kind="birth", data={"npc": npc.name, "coords": spawn_coords}
                )
            except Exception:
                pass
        except Exception as e:
            self.logger.error(f"Failed to spawn new NPC: {e}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Faction":
        """Create faction from dictionary (convert npc_ids to set if needed)"""
        if "npc_ids" in data and not isinstance(data["npc_ids"], set):
            data["npc_ids"] = set(data["npc_ids"])
        return cls(**data)

    def add_member(self, npc_name: str):
        """Add an NPC to the faction."""
        if npc_name not in self.npc_ids:
            self.npc_ids.add(npc_name)

    def remove_member(self, npc_name: str):
        """Remove an NPC from the faction."""
        if npc_name in self.npc_ids:
            self.npc_ids.remove(npc_name)

    # ================= MEMORY RESTORATION (Phase 1: Events) =================
    def record_event(
        self,
        world,
        kind: str,
        data: Optional[Dict[str, Any]] = None,
        max_events: int = 500,
    ):
        """Record a structured event in faction memory.

        Parameters:
            world: world reference (optional, for tick/time capture)
            kind: short event type ("birth", "death", "territory_gain", etc.)
            data: dict of extra fields (npc, coords, cause, etc.)
            max_events: ring buffer cap
        """
        try:
            tick = getattr(world, "_tick_count", None)
            evt = {"tick": tick, "type": kind, "data": data or {}}
            mem = self.memory.setdefault("events", [])
            mem.append(evt)
            if len(mem) > max_events:
                del mem[0 : len(mem) - max_events]
        except Exception:
            pass

    def memory_summary(self, sample_events: int = 3) -> Dict[str, Any]:
        """Return a lightweight summary of memory for logging/export."""
        try:
            events = self.memory.get("events", [])
            sample = events[-sample_events:]
            return {
                "events_total": len(events),
                "events_sample": sample,
                "rumors_total": len(self.memory.get("rumors", [])),
                "opinions_total": len(self.memory.get("opinions", {})),
                "sayings_total": len(self.memory.get("sayings", [])),
            }
        except Exception:
            return {"events_total": 0}
