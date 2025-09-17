from typing import Dict, Tuple, List, Any
import logging
from concurrent.futures import ThreadPoolExecutor
import json
import os
import random
import time
from .chunk import Chunk
from .terrain import TerrainType
from npcs import NPC
from factions import Faction

# ===== ADD PERLIN NOISE IMPORT =====
try:
    from noise import pnoise2
except ImportError:
    pnoise2 = None  # Handle gracefully if noise is not installed

# Import faction name generator
try:
    from main import generate_faction_name
except ImportError:
    # Fallback faction name generator if main.py is not available
    def generate_faction_name(specialization: str = None) -> str:
        """Simple fallback faction name generator."""
        prefixes = ["United", "Grand", "Supreme", "Royal", "Imperial"]
        suffixes = ["Alliance", "Empire", "Federation", "Order", "Domain"]
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        return f"{prefix} {suffix}"

# Import NPC name generator
try:
    from factions.faction import generate_unique_name
except ImportError:
    # Fallback NPC name generator
    def generate_unique_name(faction_name: str, used_names: set) -> str:
        """Simple fallback NPC name generator."""
        first_parts = ["Ael", "Bryn", "Cael", "Dara", "Ely"]
        second_parts = ["an", "el", "in", "or", "us"]
        for _ in range(10):
            name = f"{random.choice(first_parts)}{random.choice(second_parts)}"
            if name not in used_names:
                return name
        return f"NPC{random.randint(1000, 9999)}"


class WorldEngine:
    # === Food diagnostics instrumentation ===
    def food_diagnostics(self, window: int = 600) -> dict:
        """Aggregate rolling food production and consumption across all factions."""
        prod = 0.0
        cons = 0.0
        for f in self.factions.values():
            if hasattr(f, "_econ_history") and f._econ_history:
                recent = [e for e in f._econ_history if self._tick_count - e["tick"] <= window]
                prod += sum(e.get("dFood", 0.0) for e in recent if e.get("dFood", 0.0) > 0)
                cons += sum(e.get("consumed_food", 0.0) for e in recent)
        return {
            "window": window,
            "food_produced": round(prod, 3),
            "food_consumed": round(cons, 3),
            "net": round(prod - cons, 3),
        }

    """Manages the world simulation, including chunks, NPCs, and factions."""

    # Class constants for directory paths
    CHUNK_DIR = "world_data/chunks"
    FACTION_DIR = "world_data/factions"
    FACTIONS_FILE = "world_data/factions.json"  # Added for compatibility with clear_persistence

    # Time constants
    MINUTES_PER_HOUR = 60
    HOURS_PER_DAY = 24
    DAYS_PER_SEASON = 90  # 4 seasons per year
    SEASONS_PER_YEAR = 4

    def __init__(
        self,
        seed: int = None,
        auto_seed: bool = True,
        auto_seed_threshold: int = 30,
        min_population: int = 20,
        zero_pop_warning_interval: int = 100,
        disable_faction_saving: bool = False,
    ):
        self.seed = seed
        if seed is not None:
            random.seed(seed)

        self.logger = logging.getLogger("WorldEngine")
        self.chunks: Dict[Tuple[int, int], Chunk] = {}
        self.active_chunks: Dict[Tuple[int, int], Chunk] = {}
        self.factions: Dict[str, Faction] = {}
        self._tick_count = 0
        self._previous_faction_states: Dict[str, Dict] = (
            {}
        )  # Track previous faction states for change detection

        # Global Clock System
        self.total_minutes = 0
        self.current_minute = 0
        self.current_hour = 0
        self.current_day = 0
        self.current_season = 0
        self.current_year = 0
        self.season_names = ["Spring", "Summer", "Autumn", "Winter"]

        # Parallelism control (can be disabled for testing/debugging)
        self.use_parallelism = True

        # Logging throttles
        self._no_action_count = 0  # Track consecutive ticks with no actions
        self._last_no_action_report = -1

        # Configuration
        self.auto_seed = auto_seed
        self.auto_seed_threshold = auto_seed_threshold  # ticks with 0 pop before seeding
        self.min_population = min_population  # target minimum when seeding
        self.zero_pop_warning_interval = zero_pop_warning_interval
        self.disable_faction_saving = (
            disable_faction_saving  # Disable faction saving for RL training
        )
        # Internal auto-seed state
        self._zero_pop_ticks = 0
        self._auto_seeded = False
        self._repopulated_existing = False  # Tracks if we used faction-based repopulation path
        self._auto_seed_attempts = 0  # number of auto-seed attempts performed
        # Recovery attempt tracking (covers both auto-seed and repopulation). Allows cooldown-based retries.
        self._last_recovery_tick = -1
        self._repopulate_attempts = 0

        # Diagnostics counters
        self._diag_total_npcs_last = 0
        self._diag_idle_npcs_last = 0
        self._diag_actionable_npcs_last = 0
        self._diag_last_tick_reported = 0
        self._diag_idle_classifications = (
            0  # Count of ticks where NPC produced explicit idle fallback
        )

        # Opinion / social cohesion configuration (tunable)
        self.opinion_decay_interval = 1  # days between decay applications (was 20 ticks/minutes)
        self.opinion_decay_rate = 0.01  # magnitude reduced toward 0 per decay step
        self.social_positive_interval = 1  # days between passive socialization scan (was 25)
        self.social_positive_min = 0.01
        self.social_positive_max = 0.03
        self._last_social_positive_tick = 0

        # Rumor propagation configuration
        self.rumor_interval = 1  # days between propagation cycles (was 10 ticks/minutes)
        self.rumor_max_per_cycle = 3  # cap rumors created per cycle
        self.rumor_spread_chance = 0.4  # chance a known rumor spreads to adjacent faction
        self.rumor_forget_chance = 0.02  # chance to forget very old rumor
        self.rumor_max_age = 30  # days after which rumor may be forgotten (was 600 ticks)
        self._last_rumor_tick = 0
        # Optional injected rumor generator callable: (faction, world, tick) -> str
        self.rumor_generator = None
        # Sayings generation configuration
        self.saying_interval = 1  # days between saying generation attempts (was 10 ticks)
        self.saying_max_per_cycle = 2  # cap sayings per cycle
        self._last_saying_tick = 0
        self.saying_history_cap = 150  # per-faction cap
        # Optional injected saying generator callable: (faction, world, tick, context) -> str
        self.saying_generator = None

        # Population Wave System
        self.wave_enabled = True  # Enable population wave mechanics
        self.abundance_cycle_length = (
            90  # Days for full abundance cycle (was 800 ticks, now ~3 months)
        )
        self.fertility_wave_length = 60  # Days for fertility wave cycle (was 600 ticks)
        self.mortality_wave_length = 70  # Days for mortality wave cycle (was 700 ticks)
        self.resource_wave_amplitude = 0.6  # +/- 60% resource variation
        self.fertility_wave_amplitude = 0.4  # +/- 40% fertility variation
        self.mortality_wave_amplitude = 0.3  # +/- 30% mortality variation

        # Balance audit instrumentation
        # Per-tick aggregates (updated each world_tick)
        self._audit_starvation_deaths = 0
        self._audit_combat_deaths = (
            0  # existing combat deaths already logged; counting here for ratios
        )
        self._audit_total_births = 0  # placeholder (birth system not yet implemented)
        # New detailed per-tick demographic counters
        self._audit_births_tick = 0
        self._audit_starvation_deaths_tick = 0
        self._audit_natural_deaths_cum = 0
        self._audit_natural_deaths_tick = 0
        # Rolling histories for growth analysis (net growth throttling)
        self._demo_window = 800
        self._births_history = []  # list of (tick, births_this_tick)
        self._natural_deaths_history = []
        self._starv_deaths_history = []
        self._audit_tick_resource_delta = {"food": 0.0, "Wood": 0.0, "Ore": 0.0}
        # Rolling windows (store last N tick summaries) for later moving averages
        self._audit_window = 500
        self._audit_history = []  # append dicts with metrics snapshots
        # Balance tuning parameters (exposed for dynamic adjustment & tests)
        self.balance_params = {
            "FOOD_PER_DAY_PER_NPC": 1.0,
            "STARV_THRESHOLD": 3.0,
            # Softer mortality & longer ramp
            "STARV_DEATH_RATE": 0.012,  # lowered base scaling
            "STARV_DEATH_CHANCE_MAX": 0.20,  # cap per-tick deaths
            "STARV_DECAY_PER_TICK": 0.1,  # keep original decay to satisfy tests
            # Much more conservative reproduction to prevent explosive growth
            "REPRO_COOLDOWN": 200,  # longer cooldown (was 140)
            "REPRO_FOOD_MIN": 2.5,  # higher food requirement (was 1.6)
            "REPRO_BASE_CHANCE": 0.03,  # lower base chance (was 0.07)
            "REPRO_SURPLUS_CAP": 4.0,  # reduced scaling cap (was 6.0)
            # Capacity penalty gentler
            "CAP_OVER_PENALTY_SLOPE": 0.035,
            # Mortality ramp extended & grace a bit longer
            "MORTALITY_GRACE_TICKS": 1300,
            "MORTALITY_RAMP_TICKS": 2600,
            # New adaptive safety valves
            "ADAPT_DEATH_SPIKE_WINDOW": 150,  # ticks window to watch deaths
            "ADAPT_DEATH_SPIKE_COUNT": 5,  # if starvation deaths exceed -> relief
            "ADAPT_RELIEF_DURATION": 400,  # ticks of relief
            "ADAPT_RELIEF_MULT": 0.6,  # multiplier to death probability
            "LOW_POP_THRESHOLD": 25,  # population threshold for boost
            "LOW_POP_REPRO_MULT": 1.3,  # reduced reproduction multiplier (was 1.5)
            # (Deprecated crisis failsafe parameters removed; intrinsic gating now used)
            "REPRO_SECOND_TIER_PRESSURE": 0.5,  # fraction of STARV_THRESHOLD for tier-2 births
            "REPRO_SECOND_TIER_CHANCE_MULT": 0.4,  # birth chance multiplier tier-2
            "LOW_FACTION_POP_PRESSURE_CLAMP": 5,  # clamp pressure for very small factions
        }
        # Systemic capacity & fertility instrumentation (ensure instance-level init)
        self._global_capacity_estimate = 0.0
        self._fertility_factor = 0.0
        self._resource_utilization = {"plant": 0.0, "animal": 0.0, "fish": 0.0, "mineral": 0.0}
        self._utilization_accum = {
            "plant": {"regen": 0.0, "consumed": 0.0},
            "animal": {"regen": 0.0, "consumed": 0.0},
            "fish": {"regen": 0.0, "consumed": 0.0},
            "mineral": {"regen": 0.0, "consumed": 0.0},
        }
        self._utilization_smooth_window = 200
        self._utilization_history = []
        # Adaptive logistic reproduction controller state
        self._adaptive_r_base = 0.015
        self._adaptive_r_min = 0.009
        self._adaptive_r_max = 0.025
        self._adaptive_r_last_adjust = -1
        self._adaptive_r_interval = 240
        self._adaptive_r_history = []
        # Band recalibration state
        self._band_recalib_interval = 1800
        self._band_recalib_last = -1
        self._band_recalib_min_window = 2400
        self._band_recalib_target_std_mult = 1.2
        self._band_recalib_shrink_bias = 0.9
        self._band_recalib_history = []
        self._band_recalib_history_limit = 300
        self._band_recalib_enabled = True
        # === Tick-ordered log buffer ===
        self._tick_log_buffer = {}
        self._tick_log_flush_order = []

    def log_buffered(self, level, msg, tick=None):
        """Buffer log messages by tick for ordered flushing."""
        if tick is None:
            tick = getattr(self, '_tick_count', 0)
        if tick not in self._tick_log_buffer:
            self._tick_log_buffer[tick] = []
            self._tick_log_flush_order.append(tick)
        self._tick_log_buffer[tick].append((level, msg))

    def flush_tick_log(self, tick):
        """Flush all buffered log messages for a tick in order."""
        if tick in self._tick_log_buffer:
            for level, msg in self._tick_log_buffer[tick]:
                if level == 'info':
                    self.logger.info(msg)
                elif level == 'debug':
                    self.logger.debug(msg)
                elif level == 'warning':
                    self.logger.warning(msg)
                elif level == 'error':
                    self.logger.error(msg)
                else:
                    self.logger.info(msg)
            del self._tick_log_buffer[tick]
            self._tick_log_flush_order.remove(tick)
        # Extended adaptive tuning config (mortality & capacity)
        self.balance_params.update(
            {
                "ADAPT_MORTALITY_INTERVAL": 300,  # ticks between mortality/capacity reassessments
                "ADAPT_TARGET_STARV_MAX": 6.0,  # desired upper bound for peak starvation pressure
                "ADAPT_TARGET_STARV_AVG": 2.5,  # desired average starvation pressure
                "ADAPT_MORTALITY_RATE_MIN": 0.008,  # floor for STARV_DEATH_RATE
                "ADAPT_MORTALITY_RATE_MAX": 0.02,  # ceiling for STARV_DEATH_RATE
                "ADAPT_CAP_SLOPE_MIN": 0.02,  # floor for CAP_OVER_PENALTY_SLOPE
                "ADAPT_CAP_SLOPE_MAX": 0.07,  # ceiling for CAP_OVER_PENALTY_SLOPE
                "ADAPT_STARV_THRESHOLD_MIN": 2.2,  # min starvation threshold
                "ADAPT_STARV_THRESHOLD_MAX": 4.2,  # max starvation threshold
                "ADAPT_MORTALITY_SENSITIVITY": 0.15,  # proportional adjustment factor
                # Natural age-based mortality curve parameters
                "AGE_MIDPOINT": 600,  # age where base natural mortality noticeably ramps
                "AGE_MAX": 1000,  # hard cap (align with NPC.MAX_AGE)
                "AGE_MORTALITY_BASE": 0.0002,  # baseline natural death probability at young age
                "AGE_MORTALITY_MAX": 0.02,  # asymptotic natural death probability near AGE_MAX
            }
        )
        # Rolling population metrics for adaptive tuning
        self._pop_history = []  # list of (tick, total_pop)
        self._pop_history_limit = 5000
        self._adaptive_last_applied = -1
        # Target bands (can be tuned later)
        self._pop_target_min = 30
        self._pop_target_max = 120
        # Adaptation history for plotting/debug
        self._adaptation_history = []  # list of dict snapshots
        self._adaptation_history_limit = 5000
        # Crisis state deprecated; retained placeholders for compatibility
        self._in_crisis = False
        self._crisis_enter_tick = None
        self._crisis_exit_tick = None
        # === Systemic capacity & fertility instrumentation (Phase 1) ===
        # Aggregate carrying capacity estimate (dynamic once reproduction refactor lands)
        self._global_capacity_estimate = 0.0
        # Effective fertility factor (controller output) used to scale births each tick
        self._fertility_factor = 0.0
        # Rolling resource utilization metrics (fraction of available regenerated resources consumed)
        self._resource_utilization = {
            "plant": 0.0,
            "animal": 0.0,
            "fish": 0.0,
            "mineral": 0.0,
        }
        # Internal accumulators for utilization per tick (consumed vs regenerated) before ratio calc
        self._utilization_accum = {
            "plant": {"regen": 0.0, "consumed": 0.0},
            "animal": {"regen": 0.0, "consumed": 0.0},
            "fish": {"regen": 0.0, "consumed": 0.0},
            "mineral": {"regen": 0.0, "consumed": 0.0},
        }
        # Window for rolling utilization smoothing
        self._utilization_smooth_window = 200
        self._utilization_history = []  # list of ratio dicts
        # Adaptive logistic reproduction controller state
        self._adaptive_r_base = 0.015  # starts aligned with faction logistic default
        self._adaptive_r_min = 0.009  # lower safety bound (too low -> stagnation)
        self._adaptive_r_max = 0.025  # upper safety bound (too high -> volatility)
        self._adaptive_r_last_adjust = -1
        self._adaptive_r_interval = (
            240  # ticks between adjustments (~4 in-game hours if 1 tick=1 minute)
        )
        self._adaptive_r_history = []  # list of (tick, r_base, pop_avg)
        # TUNING GUIDE:
        #   _adaptive_r_base acts as intrinsic logistic growth rate r used by factions.
        #   Controller nudges r upward when rolling avg pop < target band, downward when above.
        #   Adjust _pop_target_min/_max to redefine equilibrium band.
        #   Narrow band => more frequent small adjustments; widen band => slower, smoother adaptation.
        #   Safety bounds (_adaptive_r_min/_max) prevent runaway oscillations.
        # Automatic population band recalibration state
        self._band_recalib_interval = (
            1800  # ticks between evaluation (~30 in-game hours if 1 tick=1 minute)
        )
        # Adjust this lower (e.g., 900) for more reactive band shifts; higher for stability.
        self._band_recalib_last = -1
        self._band_recalib_min_window = 2400  # require at least this many ticks of history
        # Ensure min_window > interval to accumulate enough variance context.
        self._band_recalib_target_std_mult = 1.2  # band half-width = std * multiplier
        # Raise to widen band (controller less active), lower to tighten.
        self._band_recalib_shrink_bias = (
            0.9  # apply slight shrink vs raw std to avoid runaway widening
        )
        # shrink_bias < 1.0 gently counters increasing variance in turbulent phases.
        self._band_recalib_history = []  # list of dict snapshots {tick, avg, std, new_min, new_max}
        self._band_recalib_history_limit = 300
        self._band_recalib_enabled = True

    def in_crisis(self) -> bool:
        # Always false; legacy API retained for compatibility with any external references.
        return False

    # ===== POPULATION WAVE SYSTEM =====
    def calculate_resource_wave_multiplier(self) -> float:
        """Calculate the current resource abundance multiplier based on cyclic waves."""
        if not self.wave_enabled:
            return 1.0

        import math

        # Primary abundance cycle (longer period for major resource swings)
        primary_cycle = math.sin(2 * math.pi * self._tick_count / self.abundance_cycle_length)

        # Secondary cycle for complexity (slightly different frequency)
        secondary_cycle = math.sin(
            2 * math.pi * self._tick_count / (self.abundance_cycle_length * 1.3)
        )

        # Combine cycles with weighted average
        combined_wave = primary_cycle * 0.7 + secondary_cycle * 0.3

        # Convert to multiplier (1.0 ± amplitude)
        multiplier = 1.0 + (combined_wave * self.resource_wave_amplitude)

        # Ensure reasonable bounds (between 0.2x and 2.0x)
        return max(0.2, min(2.0, multiplier))

    def calculate_fertility_wave_multiplier(self) -> float:
        """Calculate the current fertility multiplier for population waves."""
        if not self.wave_enabled:
            return 1.0

        import math

        # Fertility cycles (different phase from resource cycles)
        fertility_wave = math.sin(
            2 * math.pi * self._tick_count / self.fertility_wave_length + math.pi / 3
        )

        # Convert to multiplier
        multiplier = 1.0 + (fertility_wave * self.fertility_wave_amplitude)
        # Ensure reasonable bounds
        multiplier = max(0.3, min(1.8, multiplier))
        # Low-pop fertility floor: prevent prolonged suppression when population is critically low
        try:
            total_pop = sum(len(f.npc_ids) for f in self.factions.values())
            if total_pop < 150:
                multiplier = max(multiplier, 0.85)
        except Exception:
            pass
        return multiplier

    def calculate_mortality_wave_multiplier(self) -> float:
        """Calculate the current mortality multiplier for population waves."""
        if not self.wave_enabled:
            return 1.0

        import math

        # Mortality cycles (inverse relationship with fertility, different phase)
        mortality_wave = math.sin(
            2 * math.pi * self._tick_count / self.mortality_wave_length + math.pi
        )

        # Convert to multiplier (higher mortality during low fertility periods)
        multiplier = 1.0 + (mortality_wave * self.mortality_wave_amplitude)

        # Ensure reasonable bounds
        return max(0.5, min(1.5, multiplier))

    def get_wave_status(self) -> dict:
        """Get current wave status for diagnostics."""
        return {
            "tick": self._tick_count,
            "resource_multiplier": self.calculate_resource_wave_multiplier(),
            "fertility_multiplier": self.calculate_fertility_wave_multiplier(),
            "mortality_multiplier": self.calculate_mortality_wave_multiplier(),
            "wave_enabled": self.wave_enabled,
        }

    def _record_population_metric(self):
        try:
            total = sum(len(f.npc_ids) for f in self.factions.values())
            self._pop_history.append((self._tick_count, total))
            if len(self._pop_history) > self._pop_history_limit:
                self._pop_history.pop(0)
        except Exception:
            pass

    # ===== ADAPTIVE LOGISTIC REPRODUCTION CONTROLLER =====
    def update_adaptive_reproduction(self):
        """Adjust the intrinsic logistic growth base (r_base) toward target population band.

        Logic:
        - Evaluate every _adaptive_r_interval ticks.
        - Compute rolling population average (window 800 ticks) and difference from target band midpoint.
        - If below band: increase r_base proportionally to fractional shortfall (capped).
        - If above band: decrease r_base proportionally to fractional excess.
        - Apply smoothing to avoid oscillations (EMA with alpha).
        - Record adjustment history for diagnostics.
        """
        try:
            if self._tick_count - self._adaptive_r_last_adjust < self._adaptive_r_interval:
                return
            if not self.factions:
                return
            avg_pop = self._rolling_population_average(window=800)
            if avg_pop <= 0:
                return
            mid = 0.5 * (self._pop_target_min + self._pop_target_max)
            band_half = 0.5 * (self._pop_target_max - self._pop_target_min)
            # Fractional deviation (negative if below)
            deviation = (avg_pop - mid) / max(1.0, band_half)
            # Sensitivity scaling
            sens = 0.12  # global reproduction sensitivity
            adjust = 0.0
            if deviation < -0.05:  # below band
                # Boost scaled by |deviation| but capped
                adjust = min(0.004, -deviation * sens * self._adaptive_r_base)
            elif deviation > 0.05:  # above band
                adjust = -min(0.004, deviation * sens * self._adaptive_r_base)
            if adjust != 0.0:
                new_r = self._adaptive_r_base + adjust
                new_r = max(self._adaptive_r_min, min(self._adaptive_r_max, new_r))
                # EMA smoothing for stability
                alpha = 0.55
                smoothed = (alpha * new_r) + (1 - alpha) * self._adaptive_r_base
                if abs(smoothed - self._adaptive_r_base) > 1e-6:
                    prev = self._adaptive_r_base
                    self._adaptive_r_base = smoothed
                    self._adaptive_r_last_adjust = self._tick_count
                    self._adaptive_r_history.append(
                        {
                            "tick": self._tick_count,
                            "avg_pop": avg_pop,
                            "r_base_prev": prev,
                            "r_base_new": self._adaptive_r_base,
                            "deviation": deviation,
                        }
                    )
                    if len(self._adaptive_r_history) > 1000:
                        self._adaptive_r_history.pop(0)
                    try:
                        self.logger.info(
                            f"Adaptive r_base adjust: pop_avg={avg_pop:.1f} dev={deviation:.2f} r={prev:.4f}->{self._adaptive_r_base:.4f}"
                        )
                    except Exception:
                        pass
        except Exception:
            pass

    # ===== AUTOMATIC POPULATION BAND RECALIBRATION =====
    def _auto_recalibrate_population_band(self):
        """Recompute target population band from long-term variance.

        Method:
        - Run every _band_recalib_interval ticks if enabled and enough history collected.
        - Use last N (min_window) population samples; compute mean and std.
        - New half-width = std * target_std_mult * shrink_bias.
        - Clamp half-width to sensible bounds (min 5, max 0.75 * mean) to avoid extreme bands.
        - Update _pop_target_min/_max gradually using smoothing factor to prevent abrupt jumps.
        - Record snapshot in _band_recalib_history for export/plotting.
        """
        try:
            if not getattr(self, "_band_recalib_enabled", False):
                return
            if self._tick_count - self._band_recalib_last < self._band_recalib_interval:
                return
            if len(self._pop_history) < self._band_recalib_min_window:
                return
            # Collect relevant window (use last min_window ticks)
            window_ticks = self._band_recalib_min_window
            recent = [p for (t, p) in self._pop_history if self._tick_count - t <= window_ticks]
            if len(recent) < 50:
                return
            import math

            mean = sum(recent) / len(recent)
            var = sum((p - mean) ** 2 for p in recent) / max(1, len(recent) - 1)
            std = math.sqrt(var)
            half = std * self._band_recalib_target_std_mult * self._band_recalib_shrink_bias
            # Clamp half-width
            half = max(5.0, min(half, mean * 0.75))
            new_min = max(1.0, mean - half)
            new_max = max(new_min + 5.0, mean + half)
            # Smoothing (EMA) to avoid abrupt band jumps
            alpha = 0.35
            self._pop_target_min = alpha * new_min + (1 - alpha) * self._pop_target_min
            self._pop_target_max = alpha * new_max + (1 - alpha) * self._pop_target_max
            self._band_recalib_last = self._tick_count
            snap = {
                "tick": self._tick_count,
                "mean": round(mean, 3),
                "std": round(std, 3),
                "applied_min": round(self._pop_target_min, 2),
                "applied_max": round(self._pop_target_max, 2),
            }
            self._band_recalib_history.append(snap)
            if len(self._band_recalib_history) > self._band_recalib_history_limit:
                self._band_recalib_history.pop(0)
            try:
                self.logger.info(
                    f"Band recalibrated: mean={mean:.1f} std={std:.1f} -> min={self._pop_target_min:.1f} max={self._pop_target_max:.1f}"
                )
            except Exception:
                pass
        except Exception:
            pass

    def _rolling_population_average(self, window: int = 600):
        if not self._pop_history:
            return 0.0
        # Use last N entries within tick window
        recent = [p for (t, p) in self._pop_history if self._tick_count - t <= window]
        if not recent:
            recent = [p for _, p in self._pop_history[-window:]]
        if not recent:
            return 0.0
        return sum(recent) / len(recent)

    def _adaptive_reproduction_tuning(self):
        """Auto-adjust reproduction parameters based on rolling population average.

        Strategy:
        - If rolling average < target_min: gently boost REPRO_BASE_CHANCE (up to +50%) and lower REPRO_COOLDOWN floor.
        - If rolling average > target_max: dampen reproduction (reduce base chance, raise cooldown) but never below 50% defaults.
        - Apply at most once every 200 ticks to avoid oscillation.
        - Logs applied adjustments for audit.
        """
        try:
            if self._tick_count - self._adaptive_last_applied < 200:
                return
            avg = self._rolling_population_average(window=800)
            base = self.balance_params.get("REPRO_BASE_CHANCE", 0.07)
            cooldown = self.balance_params.get("REPRO_COOLDOWN", 140)
            changed = {}
            # Store original baselines (one-time) for boundary enforcement
            if not hasattr(self, "_repro_baseline_base"):
                self._repro_baseline_base = base
            if not hasattr(self, "_repro_baseline_cooldown"):
                self._repro_baseline_cooldown = cooldown
            baseline_base = self._repro_baseline_base
            baseline_cd = self._repro_baseline_cooldown
            if avg < self._pop_target_min:
                # Boost
                new_base = min(baseline_base * 1.5, base * 1.25)
                new_cd = max(int(baseline_cd * 0.6), int(cooldown * 0.8))
                if abs(new_base - base) > 1e-6:
                    self.balance_params["REPRO_BASE_CHANCE"] = new_base
                    changed["REPRO_BASE_CHANCE"] = (base, new_base)
                if new_cd != cooldown:
                    self.balance_params["REPRO_COOLDOWN"] = new_cd
                    changed["REPRO_COOLDOWN"] = (cooldown, new_cd)
            elif avg > self._pop_target_max:
                # Dampen
                new_base = max(baseline_base * 0.5, base * 0.85)
                new_cd = min(int(baseline_cd * 1.8), int(cooldown * 1.15))
                if abs(new_base - base) > 1e-6:
                    self.balance_params["REPRO_BASE_CHANCE"] = new_base
                    changed["REPRO_BASE_CHANCE"] = (base, new_base)
                if new_cd != cooldown:
                    self.balance_params["REPRO_COOLDOWN"] = new_cd
                    changed["REPRO_COOLDOWN"] = (cooldown, new_cd)
            if changed:
                self._adaptive_last_applied = self._tick_count
                try:
                    self.logger.info(f"Adaptive reproduction tuning (avg_pop={avg:.1f}): {changed}")
                except Exception:
                    pass
                    # Record adaptation snapshot
                    try:
                        self._record_adaptation_snapshot(
                            kind="reproduction", changes=changed, avg_pop=avg
                        )
                    except Exception:
                        pass
        except Exception:
            pass

    def _adaptive_mortality_capacity_tuning(self):
        """Adjust mortality and capacity pressure parameters to keep starvation pressures within target bands.

        Logic:
        - Run at most every ADAPT_MORTALITY_INTERVAL ticks.
        - Use recent audit snapshot (last entry) starvation max & avg.
        - If both max and avg well below targets, relax (increase STARV_THRESHOLD slightly or lower CAP_OVER_PENALTY_SLOPE).
        - If either exceeds target, tighten (raise CAP slope modestly or increase STARV_DEATH_RATE within bounds).
        - Adjust STARV_DEATH_RATE proportionally to deviation * sensitivity.
        Safeguards ensure parameters stay within configured min/max.
        """
        try:
            interval = self.balance_params.get("ADAPT_MORTALITY_INTERVAL", 300)
            if self._tick_count % interval != 0:
                return
            if not self._audit_history:
                return
            snap = self._audit_history[-1]
            starv_max = snap["starvation_pressure"]["max"]
            starv_avg = snap["starvation_pressure"]["avg"]
            # Targets & bounds
            tgt_max = self.balance_params.get("ADAPT_TARGET_STARV_MAX", 6.0)
            tgt_avg = self.balance_params.get("ADAPT_TARGET_STARV_AVG", 2.5)
            rate = self.balance_params.get("STARV_DEATH_RATE", 0.012)
            slope = self.balance_params.get("CAP_OVER_PENALTY_SLOPE", 0.035)
            threshold = self.balance_params.get("STARV_THRESHOLD", 3.0)
            sens = self.balance_params.get("ADAPT_MORTALITY_SENSITIVITY", 0.15)
            # Bounds
            rate_min = self.balance_params.get("ADAPT_MORTALITY_RATE_MIN", 0.008)
            rate_max = self.balance_params.get("ADAPT_MORTALITY_RATE_MAX", 0.02)
            slope_min = self.balance_params.get("ADAPT_CAP_SLOPE_MIN", 0.02)
            slope_max = self.balance_params.get("ADAPT_CAP_SLOPE_MAX", 0.07)
            th_min = self.balance_params.get("ADAPT_STARV_THRESHOLD_MIN", 2.2)
            th_max = self.balance_params.get("ADAPT_STARV_THRESHOLD_MAX", 4.2)
            changed = {}
            # Deviation signals
            over_max = starv_max - tgt_max
            over_avg = starv_avg - tgt_avg
            # Tighten if either significantly above target
            if over_max > 0.5 or over_avg > 0.4:
                # Increase mortality rate proportionally (within bounds)
                delta_rate = (
                    sens * max(over_max / max(tgt_max, 1.0), over_avg / max(tgt_avg, 1.0)) * rate
                )
                new_rate = min(rate_max, rate + delta_rate)
                if abs(new_rate - rate) > 1e-6:
                    self.balance_params["STARV_DEATH_RATE"] = new_rate
                    changed["STARV_DEATH_RATE"] = (rate, new_rate)
                # Increase capacity slope to amplify overcrowd penalty
                new_slope = min(slope_max, slope * (1.0 + sens * 0.6))
                if abs(new_slope - slope) > 1e-6:
                    self.balance_params["CAP_OVER_PENALTY_SLOPE"] = new_slope
                    changed["CAP_OVER_PENALTY_SLOPE"] = (slope, new_slope)
                # Lower threshold slightly to start mortality earlier if extreme
                if over_max > 1.0:
                    new_th = max(th_min, threshold - 0.05)
                    if abs(new_th - threshold) > 1e-6:
                        self.balance_params["STARV_THRESHOLD"] = new_th
                        changed["STARV_THRESHOLD"] = (threshold, new_th)
            # Relax if clearly below targets (both below by margin)
            elif starv_max < tgt_max * 0.55 and starv_avg < tgt_avg * 0.55:
                # Decrease mortality rate
                new_rate = max(rate_min, rate * (1.0 - sens * 0.5))
                if abs(new_rate - rate) > 1e-6:
                    self.balance_params["STARV_DEATH_RATE"] = new_rate
                    changed["STARV_DEATH_RATE"] = (rate, new_rate)
                # Decrease capacity slope
                new_slope = max(slope_min, slope * (1.0 - sens * 0.4))
                if abs(new_slope - slope) > 1e-6:
                    self.balance_params["CAP_OVER_PENALTY_SLOPE"] = new_slope
                    changed["CAP_OVER_PENALTY_SLOPE"] = (slope, new_slope)
                # Raise threshold slightly to allow higher pressure before deaths
                new_th = min(th_max, threshold + 0.05)
                if abs(new_th - threshold) > 1e-6:
                    self.balance_params["STARV_THRESHOLD"] = new_th
                    changed["STARV_THRESHOLD"] = (threshold, new_th)
            if changed:
                try:
                    self.logger.info(
                        f"Adaptive mortality/capacity tuning: starv_max={starv_max:.2f} starv_avg={starv_avg:.2f} changes={changed}"
                    )
                except Exception:
                    pass
                try:
                    self._record_adaptation_snapshot(
                        kind="mortality_capacity",
                        changes=changed,
                        starv_max=starv_max,
                        starv_avg=starv_avg,
                    )
                except Exception:
                    pass
        except Exception:
            pass

    def _record_adaptation_snapshot(self, **kwargs):
        snap = {
            "tick": self._tick_count,
            "STARV_DEATH_RATE": self.balance_params.get("STARV_DEATH_RATE"),
            "CAP_OVER_PENALTY_SLOPE": self.balance_params.get("CAP_OVER_PENALTY_SLOPE"),
            "STARV_THRESHOLD": self.balance_params.get("STARV_THRESHOLD"),
            "REPRO_BASE_CHANCE": self.balance_params.get("REPRO_BASE_CHANCE"),
            "REPRO_COOLDOWN": self.balance_params.get("REPRO_COOLDOWN"),
            "kind": kwargs.get("kind"),
            "meta": {k: v for k, v in kwargs.items() if k not in ("kind",)},
        }
        self._adaptation_history.append(snap)
        if len(self._adaptation_history) > self._adaptation_history_limit:
            self._adaptation_history.pop(0)

    def export_adaptation_history(self, path: str = "artifacts/data/adaptation_history.json"):
        import json

        try:
            data = {
                "generated_at_tick": getattr(self, "_tick_count", 0),
                "entries": self._adaptation_history,
                "adaptive_r_history": getattr(self, "_adaptive_r_history", []),
                "population_history": getattr(self, "_pop_history", []),
                "pop_target_band": [
                    getattr(self, "_pop_target_min", None),
                    getattr(self, "_pop_target_max", None),
                ],
                "band_recalibration_history": getattr(self, "_band_recalib_history", []),
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            try:
                self.logger.info(
                    f"Adaptation history exported to {path} ({len(self._adaptation_history)} entries)"
                )
            except Exception:
                pass
            return path
        except Exception as e:
            try:
                self.logger.error(f"Failed to export adaptation history: {e}")
            except Exception:
                pass
            return None

    def tune_balance(self, **overrides):
        """Runtime update of balance parameters.

        Usage: world.tune_balance(STARV_DEATH_RATE=0.015, REPRO_BASE_CHANCE=0.08)
        Only updates known keys; ignores unknown ones.
        Returns dict of (old, new) for applied keys for logging/audit.
        """
        changes = {}
        for k, v in overrides.items():
            if k in self.balance_params:
                old = self.balance_params[k]
                self.balance_params[k] = v
                changes[k] = (old, v)
        if changes:
            try:
                self.logger.info(f"Balance tuning applied: {changes}")
            except Exception:
                pass
        return changes

    def _perform_auto_seed(self):
        """Automatically seed the world with a minimal population to break zero-population stagnation."""
        # Choose an origin region (0,0) and surrounding ring
        base_coords = (0, 0)
        self.activate_chunk(*base_coords)
        spawned = 0
        # Generate a proper faction name instead of hardcoded "SeedFaction"
        faction_name = generate_faction_name()
        if faction_name not in self.factions:
            self.factions[faction_name] = Faction(name=faction_name, territory=[base_coords])
        
        # Track used NPC names to ensure uniqueness
        used_names = set()
        
        for i in range(self.min_population):
            try:
                # Generate a proper NPC name instead of "seed_{i}"
                npc_name = generate_unique_name(faction_name, used_names)
                used_names.add(npc_name)
                npc = NPC(name=npc_name, coordinates=base_coords, faction_id=faction_name)
                chunk = self.get_chunk(*base_coords)
                if npc not in chunk.npcs:
                    chunk.npcs.append(npc)
                self.factions[faction_name].add_member(npc.name)
                spawned += 1
            except Exception as e:
                self.logger.error(f"Failed to auto-seed NPC {i}: {e}")
        # Mark that at least one attempt occurred but allow future attempts if population dies out again
        self._auto_seeded = True
        self._auto_seed_attempts += 1
        self.logger.warning(
            f"Auto-seeded attempt#{self._auto_seed_attempts}: {spawned} NPCs after {self._zero_pop_ticks} zero-pop ticks (threshold={self.auto_seed_threshold})."
        )

    def _repopulate_existing_factions(self):
        """Repopulate existing factions with escalating NPC counts per attempt.

        Returns number of NPCs spawned. Subsequent attempts (after cooldown) increase per-faction
        spawn count up to a capped maximum to improve survival odds if earlier reseeds failed.
        """
        if not self.factions:
            return 0
        self._repopulate_attempts += 1
        # Escalate with attempts: 1,2,3,4 then cap
        per_faction = min(1 + self._repopulate_attempts - 1, 4)
        spawned_total = 0
        for fname, faction in self.factions.items():
            try:
                # Skip if faction already somehow has members (defensive under total pop=0)
                if faction.npc_ids:
                    continue
                if faction.territory:
                    spawn_coords = random.choice(faction.territory)
                else:
                    spawn_coords = (0, 0)
                self.activate_chunk(*spawn_coords)
                existing_ids = set(faction.npc_ids)
                for idx in range(per_faction):
                    npc_name = f"{fname.lower()}_revival_{idx}"
                    counter = idx
                    while npc_name in existing_ids:
                        counter += 1
                        npc_name = f"{fname.lower()}_revival_{counter}"
                    npc = NPC(name=npc_name, coordinates=spawn_coords, faction_id=fname)
                    chunk = self.get_chunk(*spawn_coords)
                    if npc not in chunk.npcs:
                        chunk.npcs.append(npc)
                    faction.add_member(npc.name)
                    existing_ids.add(npc.name)
                    spawned_total += 1
            except Exception as e:
                self.logger.error(f"Failed to repopulate faction {fname}: {e}")
        if spawned_total > 0:
            self.logger.warning(
                f"Repopulation attempt#{self._repopulate_attempts}: spawned {spawned_total} NPCs across {len(self.factions)} factions (per_faction={per_faction}) after {self._zero_pop_ticks} zero-pop ticks."
            )
        return spawned_total

    # === Diagnostics Helpers ===
    def diagnostics_snapshot(self) -> Dict[str, Any]:
        """Return current diagnostics about population and idle/actionable distribution.
        # Aggregate capacity samples this tick if present (published by factions); simple average
        try:
            if hasattr(self, '_cap_samples') and self._cap_samples:
                avg_cap = sum(self._cap_samples) / max(1, len(self._cap_samples))
                # Smooth capacity estimate (EMA) for stability
                alpha = 0.3
                self._global_capacity_estimate = (alpha * avg_cap) + (1 - alpha) * self._global_capacity_estimate
            # Reset samples after aggregation
            self._cap_samples = []
        except Exception:
            pass
        return {
        This is a lightweight aggregation over active chunks, counting NPCs that:
        - produced an actionable task this tick (tracked during tick assembly)
        - produced no task (implicit idle) or explicit idle fallback action
        The method itself only reads last stored counters updated in world_tick for O(1) access.
        """
        diag = {
            "tick": self._tick_count,
            "total_npcs": self._diag_total_npcs_last,
            "actionable_npcs": self._diag_actionable_npcs_last,
            "idle_npcs": self._diag_idle_npcs_last,
            "idle_pct": (
                (self._diag_idle_npcs_last / self._diag_total_npcs_last * 100.0)
                if self._diag_total_npcs_last
                else 0.0
            ),
            "idle_fallback_ticks": self._diag_idle_classifications,
            "no_action_streak": self._no_action_count,
            "auto_seeded": self._auto_seeded,
            "zero_pop_ticks": self._zero_pop_ticks,
            "repopulated_existing": self._repopulated_existing,
            # Starvation pressure aggregation (current values per diagnostics call)
            "starvation": self._aggregate_starvation_pressure(),
            # Balance audit high-level exported metrics (latest tick only)
            "audit": {
                "starvation_deaths": self._audit_starvation_deaths,
                "combat_deaths": self._audit_combat_deaths,
                "births": self._audit_total_births,
                "natural_deaths_cum": self._audit_natural_deaths_cum,
                "births_tick": self._audit_births_tick,
                "starvation_deaths_tick": self._audit_starvation_deaths_tick,
                "natural_deaths_tick": self._audit_natural_deaths_tick,
                "resource_delta": self._audit_tick_resource_delta,
                "history_len": len(self._audit_history),
            },
            # Systemic capacity & fertility controller metrics
            "capacity_estimate": self._global_capacity_estimate,
            "fertility_factor": self._fertility_factor,
            "resource_utilization": self._resource_utilization,
        }
        # Attach food diagnostics
        diag["food_diagnostics"] = self.food_diagnostics(window=600)
        return diag

    def get_chunk(self, x: int, y: int) -> Chunk:
        """Get or create a chunk at the given coordinates, with Perlin noise terrain generation."""
        if (x, y) not in self.chunks:
            # ===== PERLIN NOISE TERRAIN GENERATION =====
            terrain_type = TerrainType.PLAINS
            if pnoise2 is not None:
                # Parameters for Perlin noise
                scale = 50.0
                octaves = 4
                persistence = 0.5
                lacunarity = 2.0
                seed = self.seed if self.seed is not None else 0
                noise_val = pnoise2(
                    (x + seed) / scale,
                    (y + seed) / scale,
                    octaves=octaves,
                    persistence=persistence,
                    lacunarity=lacunarity,
                    repeatx=1024,
                    repeaty=1024,
                    base=0,
                )
                # Map noise value to terrain type using your 20 biomes
                if noise_val < -0.8:
                    terrain_type = TerrainType.GLACIER
                elif noise_val < -0.6:
                    terrain_type = TerrainType.TUNDRA
                elif noise_val < -0.4:
                    terrain_type = TerrainType.WATER
                elif noise_val < -0.2:
                    terrain_type = TerrainType.COASTAL  # Beach-like coastal areas
                elif noise_val < 0.0:
                    terrain_type = TerrainType.SWAMP
                elif noise_val < 0.1:
                    terrain_type = TerrainType.PLAINS
                elif noise_val < 0.2:
                    terrain_type = TerrainType.VALLEY
                elif noise_val < 0.3:
                    terrain_type = TerrainType.HILLS
                elif noise_val < 0.4:
                    terrain_type = TerrainType.FOREST
                elif noise_val < 0.5:
                    terrain_type = TerrainType.JUNGLE
                elif noise_val < 0.6:
                    terrain_type = TerrainType.TAIGA
                elif noise_val < 0.7:
                    terrain_type = TerrainType.MOUNTAINS
                elif noise_val < 0.8:
                    terrain_type = TerrainType.CANYON
                elif noise_val < 0.9:
                    terrain_type = TerrainType.VOLCANIC
                else:
                    terrain_type = TerrainType.DESERT
            # Create chunk with generated terrain
            chunk = Chunk(coordinates=(x, y), terrain=terrain_type)
            # Initialize depletion model capacities & regen based on terrain base table
            base = self._get_base_resources_for_terrain(terrain_type)
            # Capacity scales base* CAP_FACTOR (ensures headroom) ; regen is base * REGEN_FACTOR
            CAP_FACTOR = 40.0  # allows accumulation but finite
            REGEN_FACTOR = 1.0  # per-tick regen equals base seasonal-adjusted multiplier later
            for rtype, amt in base.items():
                # Set capacity if not present
                if rtype not in chunk.resource_capacity:
                    chunk.resource_capacity[rtype] = max(amt * CAP_FACTOR, amt * 10.0)
                if rtype not in chunk.resource_regen:
                    chunk.resource_regen[rtype] = amt * REGEN_FACTOR
                if rtype not in chunk.resources:
                    # Start at 50% capacity to avoid immediate saturation
                    chunk.resources[rtype] = chunk.resource_capacity[rtype] * 0.5
            self.chunks[(x, y)] = chunk
        return self.chunks[(x, y)]

    def activate_chunk(self, x: int, y: int):
        """Activate a chunk for processing."""
        chunk = self.get_chunk(x, y)
        self.active_chunks[(x, y)] = chunk
        chunk.activate()

    def deactivate_chunk(self, x: int, y: int):
        """Deactivate a chunk."""
        if (x, y) in self.active_chunks:
            chunk = self.active_chunks.pop((x, y))
            chunk.deactivate()
            self._save_chunk(chunk)

    def _save_chunk(self, chunk: Chunk):
        """Save a chunk to disk."""
        os.makedirs(self.CHUNK_DIR, exist_ok=True)  # Use class constant
        chunk_file = os.path.join(
            self.CHUNK_DIR, f"chunk_{chunk.coordinates[0]}_{chunk.coordinates[1]}.json"
        )  # Fixed: Use coordinates tuple
        with open(chunk_file, "w") as f:
            json.dump(chunk.to_dict(), f, indent=2)

    def _save_factions(self):
        """Save all factions to disk."""
        if self.disable_faction_saving:
            return  # Skip faction saving for RL training performance
        os.makedirs(self.FACTION_DIR, exist_ok=True)  # Use class constant
        for faction_name, faction in self.factions.items():
            faction_file = os.path.join(self.FACTION_DIR, f"{faction_name}.json")
            with open(faction_file, "w") as f:
                json.dump(faction.to_dict(), f, indent=2)

    def _move_npc(self, npc: NPC, new_coords: Tuple[int, int]):
        """Move an NPC to new coordinates."""
        old_chunk = self.chunks.get(npc.coordinates)
        if old_chunk:
            old_chunk.npcs.remove(npc)

        npc.coordinates = new_coords
        new_chunk = self.get_chunk(*new_coords)
        new_chunk.npcs.append(npc)

        # Activate the new chunk if it's not already active
        if new_coords not in self.active_chunks:
            self.activate_chunk(*new_coords)

    def _simulate_combat(self, chunk: Chunk):
        """Simulate combat in a chunk."""
        # Simple combat simulation - can be expanded
        combatants = [npc for npc in chunk.npcs if npc.health > 0]
        if len(combatants) < 2:
            return

        # Random combat resolution
        attacker, defender = random.sample(combatants, 2)
        damage = random.randint(5, 15)
        defender.health -= damage
        self.logger.info(f"Combat: {attacker.name} attacks {defender.name} for {damage} damage")

        if defender.health <= 0:
            self.logger.info(f"{defender.name} has died in combat")
            chunk.npcs.remove(defender)
            try:
                self._audit_combat_deaths += 1
            except Exception:
                pass
            # Opinion impact (aggressor vs victim factions)
            try:
                att_fac = getattr(attacker, "faction_id", None)
                def_fac = getattr(defender, "faction_id", None)
                if att_fac and def_fac and att_fac != def_fac:
                    fa = self.factions.get(att_fac)
                    fd = self.factions.get(def_fac)
                    if fa and hasattr(fa, "adjust_opinion"):
                        fa.adjust_opinion(def_fac, delta=-0.05)
                    if fd and hasattr(fd, "adjust_opinion"):
                        # Defender faction grows hostility toward attacker
                        fd.adjust_opinion(att_fac, delta=-0.08)
            except Exception:
                pass

    def world_tick(self):
        """Process one tick of world simulation.

        Fast / profiling controls via environment variables:
        - SANDBOX_WORLD_FAST=1 : Skip expensive context (nearby/all chunks every NPC), throttle resource distribution,
          suppress adaptive tuning frequency and lower logging verbosity.
        - SANDBOX_WORLD_PROFILE=1 : Collect sectional timing and cumulative counters printed every 200 ticks.
        - SANDBOX_WORLD_RESOURCE_FREQ (int) : Override resource distribution frequency in fast mode (default 10).
        """
        fast = bool(os.environ.get("SANDBOX_WORLD_FAST"))
        ultrafast = bool(os.environ.get("SANDBOX_WORLD_ULTRAFAST"))
        profile = bool(os.environ.get("SANDBOX_WORLD_PROFILE"))
        allow_repro = bool(os.environ.get("SANDBOX_ALLOW_REPRO"))
        allow_combat = bool(os.environ.get("SANDBOX_ALLOW_COMBAT"))
        if fast and getattr(self, "_fast_logger_adjusted", False) is False:
            # Suppress verbose logger noise in fast mode
            try:
                self.logger.setLevel(logging.WARNING)
                logging.getLogger("NPC").setLevel(logging.WARNING)
            except Exception:
                pass
            self._fast_logger_adjusted = True
        if profile and not hasattr(self, "_profile_sections"):
            self._profile_sections = {
                "adaptive": 0.0,
                "resource": 0.0,
                "npc_context": 0.0,
                "npc_update": 0.0,
                "post_actions": 0.0,
                "total_ticks": 0,
            }
        tick_start = time.time() if profile else None
        # ===== OPTIMIZATION: REDUCE FACTION SAVING FREQUENCY =====
        # Only save factions every 10 ticks instead of every tick
        self._tick_count = getattr(self, "_tick_count", 0) + 1
        # Reset per-tick demographic counters
        self._audit_births_tick = 0
        self._audit_starvation_deaths_tick = 0
        self._audit_natural_deaths_tick = 0
        # Record population metric early (before faction processing may change it this tick)
        self._record_population_metric()
        # Crisis evaluation removed.
        # Periodically adapt reproduction parameters
        adaptive_t0 = time.time() if profile else None
        # In fast mode, call adaptive reproduction far less frequently (every 300 ticks)
        if allow_repro and ((not (fast or ultrafast)) or (self._tick_count % 300 == 0)):
            self._adaptive_reproduction_tuning()
        if profile:
            self._profile_sections["adaptive"] += time.time() - adaptive_t0
        # Automatic population band recalibration (prior to adaptive r_base adjustment)
        try:
            self._auto_recalibrate_population_band()
        except Exception:
            pass
        # Adaptive logistic r_base controller (separate from legacy reproduction tuning)
        try:
            if allow_repro:
                self.update_adaptive_reproduction()
        except Exception:
            pass

        # ===== GLOBAL CLOCK UPDATE =====
        # Each world_tick() = 1 day of in-game time (changed from 1 minute)
        minutes_per_day = self.MINUTES_PER_HOUR * self.HOURS_PER_DAY
        self.total_minutes += minutes_per_day
        self.current_minute = self.total_minutes % self.MINUTES_PER_HOUR
        self.current_hour = (self.total_minutes // self.MINUTES_PER_HOUR) % self.HOURS_PER_DAY
        self.current_day = self.total_minutes // (self.MINUTES_PER_HOUR * self.HOURS_PER_DAY)
        self.current_season = (self.current_day // self.DAYS_PER_SEASON) % self.SEASONS_PER_YEAR
        self.current_year = self.current_day // (self.DAYS_PER_SEASON * self.SEASONS_PER_YEAR)

        # ===== SEASONAL RESOURCE DISTRIBUTION =====
        # Distribute resources based on terrain and current season
        resource_t0 = time.time() if profile else None
        resource_freq = 1  # distribute every tick by default
        try:
            if "SANDBOX_WORLD_RESOURCE_FREQ" in os.environ:
                resource_freq = max(1, int(os.environ["SANDBOX_WORLD_RESOURCE_FREQ"]))
        except Exception:
            pass
        resource_disabled = bool(os.environ.get("SANDBOX_WORLD_RESOURCE_DISABLE"))
        if (
            not ultrafast
            and not resource_disabled
            and ((not fast) or (self._tick_count % resource_freq == 0))
        ):
            self.distribute_resources()
        if profile:
            self._profile_sections["resource"] += time.time() - resource_t0

        # ===== RL INTEGRATION: Make strategic decisions after resource distribution =====
        try:
            if hasattr(self, 'rl_agent_manager') and self.rl_agent_manager:
                rl_decisions_t0 = time.time() if profile else None
                self.rl_agent_manager.make_rl_decisions(self)
                if profile:
                    self._profile_sections["rl_decisions"] = self._profile_sections.get("rl_decisions", 0) + (time.time() - rl_decisions_t0)
        except Exception as e:
            try:
                self.logger.error(f"[RLError] RL decision making failed at tick {self._tick_count}: {e}", exc_info=True)
            except Exception:
                pass

        # ===== Initialize pending_actions and diagnostics accumulators =====
        pending_actions = []
        actionable_npcs = 0
        idle_npcs = 0

        # Process all active chunks
        # Precompute all_active_chunks only once in normal mode (fast mode won't use it)
        all_active_chunks_cache = None if (fast or ultrafast) else list(self.active_chunks.values())

        def process_npc(npc, chunk, all_active_chunks_cache):
            npc_ctx_t0 = time.time() if profile else None
            if fast or ultrafast:
                world_context = {
                    "current_chunk": chunk,
                    **(
                        {
                            "time": {
                                "hour": self.current_hour,
                                "day": self.current_day,
                                "season": self.current_season,
                                "season_name": self.season_names[self.current_season],
                                "total_minutes": self.total_minutes,
                                "is_day": self.is_daytime(),
                                "time_of_day": self.get_time_of_day(),
                                "day_cycle": self.current_hour / 24.0,
                            }
                        }
                        if not ultrafast
                        else {}
                    ),
                }
                faction_memory = {}
                if npc.faction_id and npc.faction_id in self.factions:
                    faction_memory = self.factions[npc.faction_id].memory
            else:
                cx, cy = npc.coordinates
                nearby_chunks = [
                    self.active_chunks.get((cx + dx, cy + dy))
                    for dx in range(-1, 2)
                    for dy in range(-1, 2)
                    if not (dx == 0 and dy == 0) and (cx + dx, cy + dy) in self.active_chunks
                ]
                world_context = {
                    "current_chunk": chunk,
                    "nearby_chunks": nearby_chunks,
                    "all_chunks": all_active_chunks_cache,
                    "world_engine": self,
                    "time": {
                        "hour": self.current_hour,
                        "day": self.current_day,
                        "season": self.current_season,
                        "season_name": self.season_names[self.current_season],
                        "total_minutes": self.total_minutes,
                        "is_day": self.is_daytime(),
                        "time_of_day": self.get_time_of_day(),
                        "day_cycle": self.current_hour / 24.0,
                    },
                }
                faction_memory = {}
                if npc.faction_id and npc.faction_id in self.factions:
                    faction_memory = self.factions[npc.faction_id].memory
            if profile:
                self._profile_sections["npc_context"] += time.time() - npc_ctx_t0
            npc_update_t0 = time.time() if profile else None
            if ultrafast:
                npc.age += 1
                action = None
            else:
                action = npc.update(world_context, faction_memory)
            if profile:
                self._profile_sections["npc_update"] += time.time() - npc_update_t0
            return (npc, action)

        # Parallelize NPC updates per chunk (if enabled)
        from itertools import chain

        if self.use_parallelism:
            with ThreadPoolExecutor() as executor:
                results = list(
                    chain.from_iterable(
                        executor.map(
                            lambda chunk: [
                                process_npc(npc, chunk, all_active_chunks_cache)
                                for npc in list(chunk.npcs)
                            ],
                            list(self.active_chunks.values()),
                        )
                    )
                )
        else:
            # Sequential processing
            results = list(
                chain.from_iterable(
                    [process_npc(npc, chunk, all_active_chunks_cache) for npc in list(chunk.npcs)]
                    for chunk in self.active_chunks.values()
                )
            )

        for npc, action in results:
            if not action:
                idle_npcs += 1
                if not fast:
                    self.log_buffered('debug', f"Idle fallback: NPC {npc.name} at {npc.coordinates} produced no action.", tick=self._tick_count)
            else:
                actionable_npcs += 1
                if not fast:
                    self.log_buffered('debug', f"Action generated for NPC {npc.name}: {action}", tick=self._tick_count)
                pending_actions.append((npc, action))

        total_npcs = actionable_npcs + idle_npcs
        self._diag_total_npcs_last = total_npcs
        self._diag_actionable_npcs_last = actionable_npcs
        self._diag_idle_npcs_last = idle_npcs
        if idle_npcs == total_npcs and total_npcs > 0:
            self._diag_idle_classifications += 1

        self.log_buffered('debug', f"Pending actions count: {len(pending_actions)} | actionable={actionable_npcs} idle={idle_npcs} total={total_npcs}", tick=self._tick_count)
        try:
            self.log_buffered('info', f"[Heartbeat] pre-social tick={self._tick_count} pending={len(pending_actions)}", tick=self._tick_count)
        except Exception:
            pass
    # (Defer flush until end-of-tick to include social/combat systems for strict ordering)

        # === Social & Rumor Systems (moved earlier to avoid being skipped on idle ticks) ===
        # Each subsystem isolated so one failure does not suppress others.
        # Opinion Decay
        try:
            if self.factions and self._tick_count % self.opinion_decay_interval == 0:
                for f in self.factions.values():
                    try:
                        f.decay_opinions(rate=self.opinion_decay_rate)
                    except Exception:
                        pass
        except Exception as e:
            try:
                self.log_buffered('error', f"[SocialError:OpinionDecay] tick={self._tick_count} {e}", tick=self._tick_count)
            except Exception:
                pass
        # Passive Positive Socialization
        try:
            if (
                self.factions
                and (self._tick_count - self._last_social_positive_tick)
                >= self.social_positive_interval
            ):
                self._apply_passive_socialization()
                self._last_social_positive_tick = self._tick_count
        except Exception as e:
            try:
                self.log_buffered('error', f"[SocialError:PositiveSocial] tick={self._tick_count} {e}", tick=self._tick_count)
            except Exception:
                pass
        # Rumor Propagation
        try:
            if self.factions and (self._tick_count - self._last_rumor_tick) >= self.rumor_interval:
                self._process_rumors()
                self._last_rumor_tick = self._tick_count
        except Exception as e:
            try:
                self.log_buffered('error', f"[SocialError:Rumors] tick={self._tick_count} {e}", tick=self._tick_count)
            except Exception:
                pass
        # Sayings Generation
        try:
            if self.factions:
                try:
                    self.log_buffered('info',
                        f"[SayingsPre] tick={self._tick_count} delta={self._tick_count - self._last_saying_tick} interval={self.saying_interval}"
                    , tick=self._tick_count)
                except Exception:
                    pass
            if (
                self.factions
                and (self._tick_count - self._last_saying_tick) >= self.saying_interval
            ):
                try:
                    self.log_buffered('info',
                        f"[Sayings] Trigger condition met tick={self._tick_count} delta={self._tick_count - self._last_saying_tick}"
                    , tick=self._tick_count)
                except Exception:
                    pass
                self._process_sayings()
                self._last_saying_tick = self._tick_count
        except Exception as e:
            try:
                self.log_buffered('error', f"[SocialError:Sayings] tick={self._tick_count} {e}", tick=self._tick_count)
            except Exception:
                pass

        # === Auto-seed handler (before logging no-action) ===
        if total_npcs == 0:
            self._zero_pop_ticks += 1
            # Warning escalation
            if self._zero_pop_ticks == 1:
                self.logger.warning("Population=0 detected; world producing no actions.")
            elif self._zero_pop_ticks % self.zero_pop_warning_interval == 0:
                self.logger.warning(
                    f"Population still 0 after {self._zero_pop_ticks} ticks (auto_seed={'on' if self.auto_seed else 'off'})."
                )
            # Cooldown-driven recovery attempts
            cooldown = self.auto_seed_threshold // 2 if self.auto_seed_threshold > 10 else 50
            since_last = (
                (self._tick_count - self._last_recovery_tick)
                if self._last_recovery_tick >= 0
                else None
            )
            allow_attempt = (
                self.auto_seed
                and self._zero_pop_ticks >= self.auto_seed_threshold
                and (since_last is None or since_last >= cooldown)
            )
            if allow_attempt:
                try:
                    spawned = 0
                    if self.factions:
                        spawned = self._repopulate_existing_factions()
                        if spawned == 0:  # Fallback if nothing spawned (edge conditions)
                            self._perform_auto_seed()
                    else:
                        self._perform_auto_seed()
                    self._last_recovery_tick = self._tick_count
                except Exception as e:
                    self.logger.error(f"Population recovery failed: {e}")
        else:
            # Population recovered -> reset zero-pop counter to allow future detection
            if self._zero_pop_ticks > 0:
                self.log_buffered('info',
                    f"Population recovered to {total_npcs}; resetting zero-pop counters (prior streak {self._zero_pop_ticks})."
                , tick=self._tick_count)
            self._zero_pop_ticks = 0
            self._auto_seeded = False  # allow future attempts if a later crash occurs
            self._repopulate_attempts = 0
            self._last_recovery_tick = -1

        post_t0 = time.time() if profile else None
        if not pending_actions:
            self._no_action_count += 1
            if self._no_action_count == 1 or self._no_action_count % 100 == 0:
                if total_npcs == 0:
                    self.log_buffered('info',
                        f"No actions to execute (streak {self._no_action_count}). Population=0 (Spawn NPCs? Tribes created without entities)"
                    , tick=self._tick_count)
                else:
                    self.log_buffered('info',
                        f"No actions to execute (streak {self._no_action_count}). Population={total_npcs} idle={idle_npcs}"
                    , tick=self._tick_count)
            else:
                self.log_buffered('debug', "No actions to execute.", tick=self._tick_count)
            # Periodic diagnostics even during idle streaks
            if self._tick_count % 500 == 0 and total_npcs > 0:
                snap = self.diagnostics_snapshot()
                self.log_buffered('info',
                    f"[Diagnostics] Tick {snap['tick']}: total={snap['total_npcs']} actionable={snap['actionable_npcs']} idle={snap['idle_npcs']} idle%={snap['idle_pct']:.1f} no_action_streak={snap['no_action_streak']}"
                , tick=self._tick_count)
            return
        else:
            if self._no_action_count > 0:
                self.log_buffered('debug', f"Ending no-action streak at {self._no_action_count} ticks.", tick=self._tick_count)
            self._no_action_count = 0

        # Periodic diagnostics when actions present
        if self._tick_count % 500 == 0 and total_npcs > 0:
            snap = self.diagnostics_snapshot()
            self.log_buffered('info',
                f"[Diagnostics] Tick {snap['tick']}: total={snap['total_npcs']} actionable={snap['actionable_npcs']} idle={snap['idle_npcs']} idle%={snap['idle_pct']:.1f} no_action_streak={snap['no_action_streak']}"
            , tick=self._tick_count)

        # === Reproduction throttle pre-pass (calculates dampening factor before faction processing) ===
        # PATCH: Remove reproduction throttling for steady birth rate
        self._repro_throttle = 1.0
        if not ultrafast:
            for npc, action in pending_actions:
                if action["action"] == "move":
                    self._move_npc(npc, action["new_coords"])
                elif action["action"] == "die":
                    self.log_buffered('info', f"  -> {npc.name} has died. Reason: {action['reason']}", tick=self._tick_count)
                    try:
                        reason = action.get("reason", "")
                        if "starvation" in reason:
                            self._audit_starvation_deaths += 1
                            self._audit_starvation_deaths_tick += 1
                        elif (
                            reason in ("natural causes", "old age", "poor health")
                            or "natural" in reason
                        ):
                            self._audit_natural_deaths_cum += 1
                            self._audit_natural_deaths_tick += 1
                    except Exception:
                        pass
                    self.chunks[npc.coordinates].npcs.remove(npc)
                    if npc.faction_id and npc.name in self.factions[npc.faction_id].npc_ids:
                        self.factions[npc.faction_id].remove_member(npc.name)
                    self._save_factions()
                elif action["action"] == "socialize":
                    target_npc_name = action.get("target_npc_name")
                    if target_npc_name:
                        target_npc = None
                        for chunk in self.active_chunks.values():
                            for n in chunk.npcs:
                                if n.name == target_npc_name:
                                    target_npc = n
                                    break
                            if target_npc:
                                break
                        if target_npc:
                            relationship_boost = 5.0
                            current_relationship = max(
                                npc.relationships.get(target_npc.name, 0),
                                target_npc.relationships.get(npc.name, 0),
                            )
                            new_relationship = current_relationship + relationship_boost
                            npc.relationships[target_npc.name] = new_relationship
                            target_npc.relationships[npc.name] = new_relationship
                            self.logger.info(
                                f"  -> {npc.name} and {target_npc.name} socialized. Mutual relationship: {new_relationship:.1f}."
                            )
                elif action["action"] == "collect":
                    # Handle resource collection
                    resource_type = action.get("resource", "food")
                    amount = action.get("amount", 0)
                    current_chunk = self.chunks.get(npc.coordinates)

                    if current_chunk and amount > 0:
                        # Check if resource is available
                        available = current_chunk.resources.get(resource_type, 0)
                        actual_collected = min(amount, available)

                        if actual_collected > 0:
                            # Remove from chunk
                            current_chunk.resources[resource_type] = max(
                                0, available - actual_collected
                            )

                            # Add to faction inventory
                            if npc.faction_id and npc.faction_id in self.factions:
                                faction = self.factions[npc.faction_id]
                                if not hasattr(faction, "resources"):
                                    faction.resources = {}
                                faction.resources[resource_type] = (
                                    faction.resources.get(resource_type, 0) + actual_collected
                                )

                                self.logger.info(
                                    f"  -> {npc.name} collected {actual_collected:.1f} {resource_type} from {npc.coordinates}. Faction now has {faction.resources.get(resource_type, 0):.1f} {resource_type}."
                                )
                            else:
                                self.logger.warning(
                                    f"  -> {npc.name} collected {actual_collected:.1f} {resource_type} but has no faction to store it!"
                                )
                        else:
                            self.logger.debug(
                                f"  -> {npc.name} tried to collect {resource_type} at {npc.coordinates} but none available."
                            )
                    else:
                        self.logger.debug(
                            f"  -> {npc.name} collect action failed: chunk={current_chunk is not None}, amount={amount}"
                        )
                elif action["action"] == "switch_faction":
                    # Handle faction switching (e.g., to Predator faction)
                    new_faction = action.get("new_faction")
                    old_faction = action.get("old_faction", npc.faction_id)
                    reason = action.get("reason", "unknown")

                    if new_faction and new_faction in self.factions:
                        # Update faction memberships
                        if old_faction and old_faction in self.factions:
                            self.factions[old_faction].remove_member(npc.name)
                        self.factions[new_faction].add_member(npc.name)

                        # Update NPC faction_id
                        npc.faction_id = new_faction

                        self.logger.info(
                            f"  -> {npc.name} switched from {old_faction} to {new_faction} faction. Reason: {reason}"
                        )
                    else:
                        self.logger.warning(
                            f"  -> {npc.name} tried to switch to invalid faction '{new_faction}'"
                        )
                elif action["action"] == "attack":
                    # Handle predator attack
                    target_name = action.get("target")
                    reason = action.get("reason", "unknown")

                    if target_name:
                        # Find target NPC
                        target_npc = None
                        for chunk in self.active_chunks.values():
                            for n in chunk.npcs:
                                if n.name == target_name:
                                    target_npc = n
                                    break
                            if target_npc:
                                break

                        if target_npc and target_npc.health > 0:
                            # Calculate damage (predators are more effective hunters)
                            damage = (
                                random.randint(8, 20)
                                if npc.faction_id == "Predator"
                                else random.randint(5, 15)
                            )
                            target_npc.health -= damage

                            self.logger.info(
                                f"  -> {npc.name} attacked {target_name} for {damage} damage. Reason: {reason}"
                            )

                            # If target dies, predator gets food boost
                            if target_npc.health <= 0:
                                self.logger.info(f"  -> {target_name} was killed by {npc.name}!")
                                if npc.faction_id == "Predator":
                                    # Predator gets fed from the kill
                                    food_boost = random.randint(20, 40)
                                    npc.needs["food"] = min(
                                        100, npc.needs.get("food", 0) + food_boost
                                    )
                                    self.logger.info(
                                        f"  -> {npc.name} fed on the kill, food +{food_boost}"
                                    )
                        else:
                            self.logger.debug(
                                f"  -> {npc.name} attack failed: target {target_name} not found or already dead"
                            )
                elif action["action"] == "scavenge":
                    # Handle predator scavenging
                    target_name = action.get("target")
                    reason = action.get("reason", "unknown")

                    if target_name:
                        # Find dead NPC to scavenge
                        target_npc = None
                        for chunk in self.active_chunks.values():
                            for n in chunk.npcs:
                                if n.name == target_name and n.health <= 0:
                                    target_npc = n
                                    break
                            if target_npc:
                                break

                        if target_npc:
                            # Scavenge food from the corpse
                            food_gained = random.randint(10, 25)
                            npc.needs["food"] = min(100, npc.needs.get("food", 0) + food_gained)

                            # Remove the corpse after scavenging
                            chunk = self.chunks.get(target_npc.coordinates)
                            if chunk and target_npc in chunk.npcs:
                                chunk.npcs.remove(target_npc)
                                # Remove from faction if applicable
                                if target_npc.faction_id and target_npc.faction_id in self.factions:
                                    self.factions[target_npc.faction_id].remove_member(
                                        target_npc.name
                                    )

                            self.logger.info(
                                f"  -> {npc.name} scavenged {food_gained} food from {target_name}'s corpse. Reason: {reason}"
                            )
                        else:
                            self.logger.debug(
                                f"  -> {npc.name} scavenging failed: target {target_name} not found or alive"
                            )
                # Add other action types as needed
                else:
                    self.logger.debug(
                        f"  -> Unhandled action type: {action['action']} for NPC {npc.name}"
                    )

        # Simulate combat after movements
        if not ultrafast and allow_combat:
            for chunk in list(self.active_chunks.values()):
                self._simulate_combat(chunk)

        # Aggregated shelter summary (if any severe-weather shelter events recorded this tick by NPCs)
        if not ultrafast:
            try:
                if hasattr(self, "_shelter_events_tick") and self._shelter_events_tick > 0:
                    if self._tick_count % 50 == 0:  # summarize every 50 ticks max
                        self.logger.info(
                            f"Shelter events (last 50 ticks window approx): count={self._shelter_events_tick}"
                        )
                    self._shelter_events_tick = 0
            except Exception:
                pass
        if profile:
            self._profile_sections["post_actions"] += time.time() - post_t0
            self._profile_sections["total_ticks"] += 1
            if self._profile_sections["total_ticks"] % 200 == 0:
                try:
                    total_elapsed = time.time() - tick_start
                    ps = self._profile_sections
                    # Per-tick averages
                    denom = max(1, ps["total_ticks"])
                    avg = {
                        k: (ps[k] / denom)
                        for k in (
                            "adaptive",
                            "resource",
                            "npc_context",
                            "npc_update",
                            "post_actions",
                        )
                    }
                    self.logger.warning(
                        f"[WORLD_PROFILE] ticks={ps['total_ticks']} avg_ms: "
                        f"adaptive={avg['adaptive']*1000:.2f} resource={avg['resource']*1000:.2f} "
                        f"ctx={avg['npc_context']*1000:.2f} npc={avg['npc_update']*1000:.2f} post={avg['post_actions']*1000:.2f} "
                        f"loop={total_elapsed/denom*1000:.2f}"
                    )
                except Exception:
                    pass

        # ===== OPTIMIZED FACTION PROCESSING =====
        # Process factions less frequently
        if self._tick_count % 5 == 0:  # Every 5 ticks instead of every tick
            self._process_factions_efficiently()
        else:
            # Light processing without saving
            self._process_factions_light()

        # ===== OPTIMIZATION: REDUCE LOGGING FREQUENCY =====
        # Only log detailed faction info every 50 ticks instead of every tick
        if self._tick_count % 50 == 0:
            self._log_faction_status()

        if self._tick_count % 10 == 0:
            self.log_buffered('info', f"\n--- Faction Memory Summary (Tick {self._tick_count}) ---", tick=self._tick_count)
            for faction_name, faction in self.factions.items():
                self.log_buffered('info', f"Faction: {faction_name}", tick=self._tick_count)
                try:
                    summary = (
                        faction.memory_summary() if hasattr(faction, "memory_summary") else None
                    )
                except Exception:
                    summary = None
                if summary:
                    self.logger.info(
                        f"  Events: total={summary['events_total']} sample={summary['events_sample']}"
                    )
                    self.logger.info(f"  Rumors: total={summary['rumors_total']}")
                else:
                    self.log_buffered('info', f"  Events: {faction.memory.get('events')}", tick=self._tick_count)
                    self.log_buffered('info', f"  Rumors: {faction.memory.get('rumors')}", tick=self._tick_count)
                # ===== FIX: Use get_faction_npcs to access NPC objects =====
                faction_npcs = self.get_faction_npcs(faction_name)
                avg_combat_skill = sum(npc.skills.get("combat", 0) for npc in faction_npcs) / max(
                    len(faction_npcs), 1
                )
                self.log_buffered('info', f"  Average Combat Skill: {avg_combat_skill:.1f}", tick=self._tick_count)
                rounded_opinions = {
                    name: round(opinion, 2)
                    for name, opinion in faction.memory.get("opinions", {}).items()
                }
                if rounded_opinions:
                    vals = list(faction.memory.get("opinions", {}).values())
                    avg_op = sum(vals) / len(vals) if vals else 0.0
                    hostile = sum(1 for v in vals if v <= -0.25)
                    positive = sum(1 for v in vals if v >= 0.25)
                    mn = min(vals) if vals else 0.0
                    mx = max(vals) if vals else 0.0
                    self.log_buffered('info', f"  Opinions: {rounded_opinions} | stats(avg={avg_op:.2f} hostile={hostile} positive={positive} min={mn:.2f} max={mx:.2f})", tick=self._tick_count)
                else:
                    self.log_buffered('info', "  Opinions: {}", tick=self._tick_count)
                sayings = faction.memory.get("sayings", [])
                if sayings:
                    self.log_buffered('info', f"  Sayings: total={len(sayings)} last={sayings[-3:]}", tick=self._tick_count)
                else:
                    self.log_buffered('info', "  Sayings: []", tick=self._tick_count)
            # Saying interval diagnostics
            try:
                self.log_buffered('info', f"[SayingsDiag] tick={self._tick_count} last_saying={self._last_saying_tick} interval={self.saying_interval} delta={self._tick_count - self._last_saying_tick}", tick=self._tick_count)
            except Exception:
                pass

        # Final flush for this tick (after all subsystems)
        self.flush_tick_log(self._tick_count)

        # (Removed: social & rumor block relocated earlier so it executes even when no actions occur)

        # === Balance Audit Aggregation ===
        try:
            # Aggregate faction resource totals
            total_food = sum(f.resources.get("food", 0.0) for f in self.factions.values())
            total_wood = sum(f.resources.get("Wood", 0.0) for f in self.factions.values())
            total_ore = sum(f.resources.get("Ore", 0.0) for f in self.factions.values())
            # Starvation pressure stats
            starv_values = (
                [getattr(f, "_starvation_pressure", 0.0) for f in self.factions.values()]
                if self.factions
                else []
            )
            starv_total = sum(starv_values) if starv_values else 0.0
            starv_max = max(starv_values) if starv_values else 0.0
            starv_avg = (starv_total / len(starv_values)) if starv_values else 0.0
            # Capture per-faction economy snapshots
            per_faction_deltas = {}
            for fname, faction in self.factions.items():
                try:
                    snap = faction.econ_snapshot(self._tick_count)
                    per_faction_deltas[fname] = {
                        k: snap[k] for k in ("dFood", "dWood", "dOre", "pop")
                    }
                    # Attach starvation + consumption annotation if present
                    per_faction_deltas[fname]["starv"] = round(
                        getattr(faction, "_starvation_pressure", 0.0), 4
                    )
                    if faction._econ_history and "consumed_food" in faction._econ_history[-1]:
                        per_faction_deltas[fname]["consumed"] = faction._econ_history[-1][
                            "consumed_food"
                        ]
                except Exception:
                    pass
            # Compute deltas vs previous snapshot if available
            prev = self._audit_history[-1] if self._audit_history else None
            if prev:
                self._audit_tick_resource_delta = {
                    "food": total_food - prev["totals"]["food"],
                    "Wood": total_wood - prev["totals"]["Wood"],
                    "Ore": total_ore - prev["totals"]["Ore"],
                }
            snapshot = {
                "tick": self._tick_count,
                "totals": {"food": total_food, "Wood": total_wood, "Ore": total_ore},
                "delta": self._audit_tick_resource_delta.copy(),
                "per_faction": per_faction_deltas,
                "combat_deaths_cum": self._audit_combat_deaths,
                "starvation_deaths_cum": self._audit_starvation_deaths,
                "natural_deaths_cum": self._audit_natural_deaths_cum,
                "births_tick": self._audit_births_tick,
                "starvation_deaths_tick": self._audit_starvation_deaths_tick,
                "natural_deaths_tick": self._audit_natural_deaths_tick,
                "births_cum": self._audit_total_births,
                "starvation_pressure": {
                    "total": round(starv_total, 4),
                    "max": round(starv_max, 4),
                    "avg": round(starv_avg, 4),
                },
            }
            self._audit_history.append(snapshot)
            if len(self._audit_history) > self._audit_window:
                self._audit_history.pop(0)
            # Append per-tick histories (trim)
            self._births_history.append((self._tick_count, self._audit_births_tick))
            self._natural_deaths_history.append((self._tick_count, self._audit_natural_deaths_tick))
            self._starv_deaths_history.append(
                (self._tick_count, self._audit_starvation_deaths_tick)
            )
            if len(self._births_history) > self._demo_window:
                self._births_history.pop(0)
            if len(self._natural_deaths_history) > self._demo_window:
                self._natural_deaths_history.pop(0)
            if len(self._starv_deaths_history) > self._demo_window:
                self._starv_deaths_history.pop(0)
            # Periodic audit log (sparse)
            if self._tick_count % 200 == 0:
                self.logger.info(
                    f"[BalanceAudit] tick={self._tick_count} food={total_food:.1f} dF={self._audit_tick_resource_delta['food']:.2f} combatDeaths={self._audit_combat_deaths} starvDeaths={self._audit_starvation_deaths} starvMax={starv_max:.2f} starvAvg={starv_avg:.2f}"
                )
            # Run extended adaptive tuning (mortality & capacity) after audit snapshot
            self._adaptive_mortality_capacity_tuning()
        except Exception:
            pass

    # ============ Starvation Aggregation Helper ============
    def _aggregate_starvation_pressure(self) -> Dict[str, float]:
        if not self.factions:
            return {"total": 0.0, "max": 0.0, "avg": 0.0}
        vals = [getattr(f, "_starvation_pressure", 0.0) for f in self.factions.values()]
        total = sum(vals)
        mx = max(vals) if vals else 0.0
        avg = total / len(vals) if vals else 0.0
        return {"total": round(total, 4), "max": round(mx, 4), "avg": round(avg, 4)}

    def _process_factions_efficiently(self):
        """Process factions with optimized saving (parallelized if enabled)"""

        def process_faction_item(item):
            faction_name, faction = item
            faction.process_tick(self)
            if self._faction_data_changed(faction_name, faction):
                self._save_factions()

        if self.use_parallelism:
            with ThreadPoolExecutor() as executor:
                executor.map(process_faction_item, self.factions.items())
        else:
            # Sequential processing
            for item in self.factions.items():
                process_faction_item(item)

    def _process_factions_light(self):
        """Light faction processing without saving (parallelized if enabled)"""

        def process_faction_item(item):
            _, faction = item
            faction.process_tick(self)

        if self.use_parallelism:
            with ThreadPoolExecutor() as executor:
                executor.map(process_faction_item, self.factions.items())
        else:
            # Sequential processing
            for item in self.factions.items():
                process_faction_item(item)

    def _apply_passive_socialization(self):
        """Grant small positive opinion adjustments when multiple factions share chunks peacefully.

        Logic:
        - Scan active chunks; build mapping: chunk -> set(faction_ids present)
        - For each chunk with >=2 factions and no combat flagged this tick (heuristic: no recent combat deaths in involved factions this tick)
          apply a small random positive delta to pairwise opinions.
        - Delta sampled in [social_positive_min, social_positive_max] then tapered by each faction's adjust_opinion logic.
        Safeguards:
        - Skip if too many total pairs to avoid O(N^2) blow-up (>100 pairs short-circuit)
        - No logging here beyond possible future aggregate; rely on opinion_change events if enabled in adjust_opinion.
        """
        try:
            if not self.active_chunks or len(self.factions) < 2:
                return
            # Build faction presence per chunk
            presence = []  # list of sets
            for ch in self.active_chunks.values():
                fset = set()
                for npc in getattr(ch, "npcs", []):
                    fid = getattr(npc, "faction_id", None)
                    if fid and fid in self.factions:
                        fset.add(fid)
                if len(fset) >= 2:
                    presence.append(fset)
            if not presence:
                return
            # Count total potential pairs
            pairs = set()
            for fset in presence:
                flist = list(fset)
                for i in range(len(flist)):
                    for j in range(i + 1, len(flist)):
                        a, b = flist[i], flist[j]
                        if a > b:
                            a, b = b, a
                        pairs.add((a, b))
            if not pairs or len(pairs) > 100:
                return
            for a, b in pairs:
                fa = self.factions.get(a)
                fb = self.factions.get(b)
                if not fa or not fb:
                    continue
                delta = random.uniform(self.social_positive_min, self.social_positive_max)
                try:
                    fa.adjust_opinion(b, delta)
                except Exception:
                    pass
                try:
                    fb.adjust_opinion(a, delta)
                except Exception:
                    pass
        except Exception:
            pass

    def _process_rumors(self):
        """Create and spread simple rumor entries among factions.

        Rumor structure stored per faction: {'id': str, 'text': str, 'origin': faction_name, 'tick': created_tick, 'hops': int}
        Steps:
        1. Creation: Randomly select up to rumor_max_per_cycle factions to originate new rumors.
        2. Spread: For each faction, attempt to spread a subset of its rumors to others sharing chunks (proximity heuristic) or random other faction.
        3. Forgetting: Small chance to drop very old rumors exceeding max age.
        Safeguards: Cap total rumor list per faction (e.g., 100) to avoid growth.
        """
        try:
            # DEBUG: trace entry
            # Lightweight trace (can downgrade to debug later)
            if getattr(self, "_tick_count", 0) % (self.rumor_interval or 1) == 0:
                try:
                    self.logger.debug(
                        f"[Rumors] Process cycle tick={getattr(self, '_tick_count', '?')}"
                    )
                except Exception:
                    pass
            if not self.factions:
                return
            tick = self._tick_count
            factions_list = list(self.factions.values())
            random.shuffle(factions_list)

            # Helper: ensure rumor list exists
            def _rumor_list(fac):
                return fac.memory.setdefault("rumors", [])

            # 1. Creation
            create_count = 0
            created_ids = []
            for fac in factions_list:
                if create_count >= self.rumor_max_per_cycle:
                    break
                rlist = _rumor_list(fac)
                # Increase creation odds: always create if list empty; else 30% chance
                trigger_roll = random.random()
                cond = (not rlist) or (trigger_roll < 0.30)  # base probability
                if cond:
                    # Use injected generator if provided
                    text = None
                    if callable(getattr(self, "rumor_generator", None)):
                        try:
                            text = self.rumor_generator(fac, self, tick)
                        except Exception:
                            text = None
                    if not text:
                        # Attempt to import main.generate_rumor safely (avoid circular by local import)
                        try:
                            from main import generate_rumor  # type: ignore

                            text = generate_rumor(fac, self, tick)
                        except Exception:
                            text = None
                    if not text:
                        others = [f.name for f in factions_list if f.name != fac.name]
                        target = random.choice(others) if others else "Unknown"
                        text = f"Rumor: whispers say {target} gathers quiet strength."
                    rid = f"R{tick}_{fac.name}_{random.randint(0, 9999)}"
                    entry = {
                        "id": rid,
                        "text": text,
                        "origin": fac.name,
                        "tick": tick,
                        "hops": 0,
                    }
                    rlist.append(entry)
                    created_ids.append(rid)
                    if len(rlist) > 100:
                        del rlist[0 : len(rlist) - 100]
                    create_count += 1
                # (Skip detailed per-faction logging to keep output light)
            if created_ids:
                try:
                    self.logger.info(
                        f"[Rumors] Created {len(created_ids)} new rumors at tick {tick}"
                    )
                except Exception:
                    pass
            # 2. Build proximity map (factions sharing any chunk)
            shared_map = {f.name: set() for f in factions_list}
            for ch in self.active_chunks.values():
                present = set()
                for npc in getattr(ch, "npcs", []):
                    fid = getattr(npc, "faction_id", None)
                    if fid and fid in self.factions:
                        present.add(fid)
                if len(present) >= 2:
                    for a in present:
                        shared_map[a].update(present - {a})
            # 3. Spread
            for fac in factions_list:
                rlist = _rumor_list(fac)
                if not rlist:
                    continue
                # Choose subset to attempt spreading
                sample = random.sample(rlist, min(2, len(rlist)))
                targets = list(shared_map.get(fac.name, []))
                if not targets and len(self.factions) > 1:
                    # Fallback random other faction
                    targets = [f.name for f in factions_list if f.name != fac.name]
                    targets = random.sample(targets, min(1, len(targets)))
                if not targets:
                    continue
                for rumor in sample:
                    for tgt_name in targets:
                        if random.random() > self.rumor_spread_chance:
                            continue
                        tgt_fac = self.factions.get(tgt_name)
                        if not tgt_fac:
                            continue
                        tgt_list = _rumor_list(tgt_fac)
                        # Skip if already present (by id)
                        if any(r.get("id") == rumor["id"] for r in tgt_list):
                            continue
                        # Copy with incremented hops
                        copied = rumor.copy()
                        copied["hops"] = rumor.get("hops", 0) + 1
                        tgt_list.append(copied)
                        if len(tgt_list) > 100:
                            del tgt_list[0 : len(tgt_list) - 100]
            # 4. Forgetting
            for fac in factions_list:
                rlist = _rumor_list(fac)
                if not rlist:
                    continue
                # Remove with probability if too old
                kept = []
                for r in rlist:
                    age = tick - r.get("tick", tick)
                    if age > self.rumor_max_age and random.random() < self.rumor_forget_chance:
                        continue
                    kept.append(r)
                if len(kept) != len(rlist):
                    fac.memory["rumors"] = kept
        except Exception:
            pass

    def _process_sayings(self):
        """Generate cultural sayings derived from recent faction events or databank.

        Logic:
        - For each faction (shuffled), attempt to create up to saying_max_per_cycle sayings total.
        - Prefer transforming a recent event (last 50 ticks) into a proverb-like line.
        - Fallback: use injected saying_generator or databank random saying.
        - Maintain per-faction cap (saying_history_cap) trimming oldest.
        """
        try:
            if not self.factions:
                return
            tick = self._tick_count
            try:
                self.logger.info(f"[Sayings] Enter processing tick={tick}")
            except Exception:
                pass
            factions_list = list(self.factions.values())
            random.shuffle(factions_list)
            created = 0
            for fac in factions_list:
                if created >= self.saying_max_per_cycle:
                    break
                mem = fac.memory
                sayings = mem.setdefault("sayings", [])
                events = mem.get("events", [])
                recent_event = None
                # Find a recent birth/death/territory event
                for ev in reversed(events[-25:]):  # look back a bit
                    if ev.get("tick") is not None and tick - ev["tick"] <= 50:
                        if ev["type"] in ("birth", "death", "territory_gain"):
                            recent_event = ev
                            break
                text = None
                context = {"recent_event": recent_event}
                # Injected generator first
                if callable(getattr(self, "saying_generator", None)):
                    try:
                        text = self.saying_generator(fac, self, tick, context)
                    except Exception:
                        text = None
                if not text and recent_event:
                    etype = recent_event["type"]
                    if etype == "birth":
                        npc = (
                            recent_event["data"].get("npc")
                            if isinstance(recent_event.get("data"), dict)
                            else "life"
                        )
                        text = f"'{fac.name} says new life like {npc} is a ember for tomorrow.'"
                    elif etype == "death":
                        npc = (
                            recent_event["data"].get("npc")
                            if isinstance(recent_event.get("data"), dict)
                            else "one"
                        )
                        text = f"'{fac.name} remembers {npc}; absence carves wisdom.'"
                    elif etype == "territory_gain":
                        coords = (
                            recent_event["data"].get("coords")
                            if isinstance(recent_event.get("data"), dict)
                            else "the land"
                        )
                        text = f"'Land at {coords} listens now to {fac.name} fires.'"
                if not text:
                    # Databank draw
                    try:
                        from databank import get_databank

                        db = get_databank()
                        saying_list = db.get_random("sayings", 1, unique=True)
                        if saying_list:
                            base = saying_list[0]
                            text = f"'{base}'"
                    except Exception:
                        text = None
                if not text:
                    text = f"'The winds mark tick {tick} for {fac.name}.'"
                sayings.append({"tick": tick, "text": text})
                if len(sayings) > self.saying_history_cap:
                    del sayings[0 : len(sayings) - self.saying_history_cap]
                created += 1
            if created:
                try:
                    self.logger.info(f"[Sayings] Created {created} sayings at tick {tick}")
                except Exception:
                    pass
        except Exception:
            pass

    def _faction_data_changed(self, faction_name: str, faction: Faction) -> bool:
        """Check if faction data has changed since last save using actual state comparison"""
        current_state = faction.to_dict()

        # Get previous state
        previous_state = self._previous_faction_states.get(faction_name)

        if previous_state is None:
            # First time checking this faction, consider it changed and set baseline
            self._previous_faction_states[faction_name] = current_state.copy()
            return True

        # Compare key attributes that matter for persistence
        key_attributes = [
            "resources",
            "territory",
            "npc_ids",
            "relationships",
            "wars_fought",
            "memory",
        ]

        changed = False
        for attr in key_attributes:
            if current_state.get(attr) != previous_state.get(attr):
                changed = True
                break

        # Update previous state if changed
        if changed:
            self._previous_faction_states[faction_name] = current_state.copy()

        return changed

    def _log_faction_status(self):
        """Log faction status less frequently"""
        # ... existing logging but only called every 50 ticks ...
        pass  # Placeholder - implement as needed

    # ===== GLOBAL CLOCK METHODS =====

    def get_current_time(self) -> Dict[str, Any]:
        """Get the current time as a dictionary with all time components."""
        return {
            "total_minutes": self.total_minutes,
            "minute": self.current_minute,
            "hour": self.current_hour,
            "day": self.current_day,
            "season": self.current_season,
            "season_name": self.season_names[self.current_season],
            "year": self.current_year,
        }

    def get_current_time_string(self) -> str:
        """Get a formatted string representation of the current time."""
        return f"Year {self.current_year}, {self.season_names[self.current_season]} Day {self.current_day % self.DAYS_PER_SEASON}, {self.current_hour:02d}:{self.current_minute:02d}"

    def get_time_of_day(self) -> str:
        """Get the current time of day (Morning, Afternoon, Evening, Night)."""
        if 6 <= self.current_hour < 12:
            return "Morning"
        elif 12 <= self.current_hour < 18:
            return "Afternoon"
        elif 18 <= self.current_hour < 22:
            return "Evening"
        else:
            return "Night"

    def is_daytime(self) -> bool:
        """Check if it's currently daytime (6 AM to 6 PM)."""
        return 6 <= self.current_hour < 18

    def get_season(self) -> str:
        """Get the current season name."""
        return self.season_names[self.current_season]

    # ===== SEASON SYSTEM =====

    def distribute_resources(self):
        """Regenerate chunk resources using logistic growth dR = r * R * (1 - R/K) * season_mult.

        - Initializes missing capacity/regen the same as prior implementation.
        - Mineral resources treated as non-renewable (linear small regen) unless below 10% capacity.
        - Tracks total regenerated for utilization metrics.
        - Seasonal multipliers modulate effective growth rate.
        """
        season_multipliers = {
            "Spring": {"plant": 2.0, "animal": 1.5, "mineral": 1.0, "fish": 1.7},
            "Summer": {"plant": 2.5, "animal": 2.0, "mineral": 1.0, "fish": 2.0},
            "Autumn": {"plant": 1.7, "animal": 1.7, "mineral": 1.0, "fish": 1.5},
            "Winter": {"plant": 0.7, "animal": 1.0, "mineral": 1.0, "fish": 1.0},
        }
        current_season = self.get_season()
        multipliers = season_multipliers[current_season]

        # Apply population wave effects to resource regeneration
        resource_wave_mult = self.calculate_resource_wave_multiplier()

        # Base intrinsic growth rates per resource type - VERY CONSERVATIVE for balanced economy
        base_r = {
            "plant": 0.02,
            "animal": 0.015,
            "fish": 0.018,
        }  # Much more conservative rates
        # Minerals: slightly faster linear replenishment
        mineral_linear_regen = 0.012
        for chunk_coords, chunk in self.active_chunks.items():
            if not chunk.resource_capacity or not chunk.resource_regen:
                base = self._get_base_resources_for_terrain(chunk.terrain)
                # Apply wave effects to capacity and regeneration - EXTREMELY CONSERVATIVE
                CAP_FACTOR = 5.0 * resource_wave_mult  # Reduced from 10.0
                REGEN_FACTOR = 0.05 * resource_wave_mult  # Reduced from 0.3
                for rtype, amt in base.items():
                    chunk.resource_capacity.setdefault(rtype, max(amt * CAP_FACTOR, amt * 2.0))
                    chunk.resource_regen.setdefault(rtype, amt * REGEN_FACTOR)
                    chunk.resources.setdefault(
                        rtype, chunk.resource_capacity[rtype]
                    )  # start at 100%
        # --- FOOD FLOOR: maintain minimal food reserves for starting populations ---
        food_types = ["food", "plant", "animal", "fish"]
        total_food = sum(
            sum(chunk.resources.get(food_type, 0) for food_type in food_types)
            for chunk in self.active_chunks.values()
        )
        if total_food < 20:  # Much lower threshold - reduced from 200
            for chunk in self.active_chunks.values():
                for food_type in food_types:
                    if chunk.resources.get(food_type, 0) < 1:  # Minimal boost - reduced from 5
                        chunk.resources[food_type] = chunk.resources.get(food_type, 0) + 1

        # Resource regeneration for all chunks
        for chunk_coords, chunk in self.active_chunks.items():
            for rtype, cap in chunk.resource_capacity.items():
                if cap <= 0:
                    continue
                current = chunk.resources.get(rtype, 0.0)
                if rtype == "mineral":
                    # Non-renewable style: only trickle or slight recovery if heavily depleted
                    if current < cap * 0.1:
                        add = cap * mineral_linear_regen  # small discovery boost
                    else:
                        add = cap * mineral_linear_regen * 0.25
                else:
                    r_intrinsic = base_r.get(rtype, 0.03)
                    season_mult = multipliers.get(rtype, 1.0)
                    # Apply wave effects to growth rate
                    growth_rate = r_intrinsic * season_mult * resource_wave_mult
                    # Logistic increment
                    add = growth_rate * current * (1 - (current / cap))
                    # Bootstrap if near zero (recolonization)
                    if current < cap * 0.02:
                        add = max(add, cap * 0.02 * season_mult * resource_wave_mult)
                if add <= 0:
                    continue
                new_val = min(cap, current + add)
                chunk.resources[rtype] = new_val
                if rtype in self._utilization_accum:
                    self._utilization_accum[rtype]["regen"] += new_val - current
            if self._tick_count % 250 == 0:
                self.logger.debug(
                    f"Regen(Logistic) chunk {chunk_coords} ({chunk.terrain.name}) stocks={ {k: round(v,1) for k,v in chunk.resources.items()} }"
                )
        self._update_resource_utilization()

    # === Instrumentation helper updates ===
    def record_resource_consumption(self, rtype: str, amount: float):
        """Called by factions when consuming a resource to update utilization accumulators."""
        try:
            if rtype in self._utilization_accum:
                self._utilization_accum[rtype]["consumed"] += max(0.0, amount)
        except Exception:
            pass

    def set_fertility_factor(self, value: float):
        """Setter used by forthcoming reproduction controller to publish fertility factor (clamped 0..2)."""
        try:
            self._fertility_factor = max(0.0, min(2.0, float(value)))
        except Exception:
            self._fertility_factor = 0.0

    def set_capacity_estimate(self, value: float):
        try:
            self._global_capacity_estimate = max(0.0, float(value))
        except Exception:
            self._global_capacity_estimate = 0.0

    def _update_resource_utilization(self):
        """Compute rolling utilization ratios from accumulators and smooth over window."""
        try:
            ratios = {}
            for rtype, acc in self._utilization_accum.items():
                regen = acc["regen"]
                consumed = acc["consumed"]
                ratio = (consumed / regen) if regen > 0 else 0.0
                ratios[rtype] = round(ratio, 4)
            # Append history & smooth
            self._utilization_history.append(ratios)
            if len(self._utilization_history) > self._utilization_smooth_window:
                self._utilization_history.pop(0)
            # Compute smoothed values
            window = self._utilization_history[-self._utilization_smooth_window :]
            smoothed = {}
            for rtype in self._resource_utilization.keys():
                vals = [entry.get(rtype, 0.0) for entry in window]
                smoothed[rtype] = round(sum(vals) / len(vals), 4) if vals else 0.0
            self._resource_utilization = smoothed
            # Reset per-tick regen accumulators (keep consumption until after faction processing resets it explicitly)
            for rtype in self._utilization_accum:
                self._utilization_accum[rtype]["regen"] = 0.0
                # Note: do NOT clear consumption here; consumption recorded after regen will persist until next update cycle
                self._utilization_accum[rtype]["consumed"] = 0.0
        except Exception:
            pass

    def _get_base_resources_for_terrain(self, terrain_type: TerrainType) -> Dict[str, float]:
        """Get base resource generation rates for a given terrain type."""
        # Define resource generation per terrain type
        terrain_resources = {
            TerrainType.PLAINS: {"plant": 2.0, "animal": 1.5},
            TerrainType.FOREST: {"plant": 3.0, "animal": 2.0, "mineral": 0.5},
            TerrainType.MOUNTAINS: {"mineral": 3.0, "animal": 0.5},
            TerrainType.DESERT: {"mineral": 1.0, "animal": 0.3},
            TerrainType.WATER: {"fish": 4.0},
            TerrainType.SWAMP: {"plant": 1.5, "animal": 1.0, "fish": 1.0},
            TerrainType.TUNDRA: {"animal": 0.8, "mineral": 0.3},
            TerrainType.JUNGLE: {"plant": 4.0, "animal": 2.5},
            TerrainType.HILLS: {"mineral": 2.0, "plant": 1.0, "animal": 1.0},
            TerrainType.VALLEY: {"plant": 2.5, "animal": 1.8},
            TerrainType.CANYON: {"mineral": 2.5},
            TerrainType.COASTAL: {"fish": 3.0, "plant": 1.0},
            TerrainType.ISLAND: {"fish": 2.5, "plant": 1.5},
            TerrainType.VOLCANIC: {"mineral": 4.0},
            TerrainType.SAVANNA: {"animal": 2.0, "plant": 1.0},
            TerrainType.TAIGA: {"plant": 1.5, "animal": 1.2, "mineral": 0.8},
            TerrainType.STEPPE: {"animal": 1.8, "plant": 0.8},
            TerrainType.BADLANDS: {"mineral": 1.5},
            TerrainType.GLACIER: {"mineral": 0.2},
            TerrainType.OASIS: {"plant": 3.0, "animal": 1.0},
        }

        return terrain_resources.get(terrain_type, {})

    def get_faction_npcs(self, faction_name: str) -> List[NPC]:
        """Get all NPC objects belonging to a specific faction."""
        faction_npcs = []
        for chunk in self.active_chunks.values():
            for npc in chunk.npcs:
                if npc.faction_id == faction_name:
                    faction_npcs.append(npc)
        return faction_npcs

    def shutdown(self):
        """Shutdown the world engine, saving all data and cleaning up."""
        self.logger.info("Shutting down WorldEngine...")

        # Emit final diagnostics snapshot before saving
        try:
            snap = self.diagnostics_snapshot()
            self.logger.info(
                f"Final Diagnostics: tick={snap['tick']} total={snap['total_npcs']} actionable={snap['actionable_npcs']} idle={snap['idle_npcs']} idle%={snap['idle_pct']:.1f} no_action_streak={snap['no_action_streak']} idle_fallback_ticks={snap['idle_fallback_ticks']}"
            )
        except Exception:
            pass

        # Save all factions
        self._save_factions()

        # Save all active chunks
        for chunk in self.active_chunks.values():
            self._save_chunk(chunk)

        self.logger.info("WorldEngine shutdown complete.")
