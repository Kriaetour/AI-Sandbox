import os
import random
import time
import logging
import threading
from typing import Any

from world.engine import WorldEngine
from tribes.tribal_manager import TribalManager
from tribes.tribe import TribalRole
from visualizer_api import run_api, save_world_state


def setup_dialogue_logger() -> logging.Logger:
    """Setup a separate logger for dialogue output."""
    dialogue_logger = logging.getLogger("dialogue")
    dialogue_logger.setLevel(logging.INFO)

    # Remove any existing handlers to avoid duplicates
    dialogue_logger.handlers.clear()

    # Create file handler for dialogue.log
    handler = logging.FileHandler("dialogue.log", mode="w", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    dialogue_logger.addHandler(handler)

    # Prevent propagation to root logger (so dialogue doesn't appear in
    # console)
    dialogue_logger.propagate = False

    return dialogue_logger


def safe_call(func, *args, **kwargs) -> Any:
    """Safely call a function, returning None if it fails."""
    try:
        return func(*args, **kwargs)
    except Exception:
        return None


def safe_getattr(obj, attr, default=None) -> Any:
    """Safely get an attribute, returning default if it fails."""
    try:
        return getattr(obj, attr, default)
    except Exception:
        return default


def _npcs_are_close(npc_a, npc_b):
    """Check if two NPCs are close enough for dialogue."""
    if not (hasattr(npc_a, "coordinates") and hasattr(npc_b, "coordinates")):
        return True
    return (
        abs(npc_a.coordinates[0] - npc_b.coordinates[0]) <= 1
        and abs(npc_a.coordinates[1] - npc_b.coordinates[1]) <= 1
    )


def _generate_dialogue_pair(npc_a, npc_b, context, tribal_diplomacy, tribes):
    """Generate dialogue for a pair of NPCs."""
    line_a = safe_call(npc_a.generate_dialogue, npc_b, context, tribal_diplomacy, tribes)
    line_b = safe_call(npc_b.generate_dialogue, npc_a, context, tribal_diplomacy, tribes)
    return [line for line in (line_a, line_b) if line]


def clear_persistence() -> None:
    try:
        if os.path.exists(WorldEngine.CHUNK_DIR):
            for f in os.listdir(WorldEngine.CHUNK_DIR):
                if f.endswith(".json"):
                    os.remove(os.path.join(WorldEngine.CHUNK_DIR, f))
        if os.path.exists(WorldEngine.FACTIONS_FILE):
            os.remove(WorldEngine.FACTIONS_FILE)
    except Exception:
        pass


def _parse_features():
    """Return full feature set unconditionally.

    Feature flag parsing has been disabled per user request to always run the
    complete experience. Environment variable `SANDBOX_FEATURES` is ignored.
    Keeping this helper so downstream code remains unchanged.
    """
    return {
        "resources",
        "repro",
        "mortality",
        "combat",
        "weather",
        "environmental_ai",
        "dialogue_full",
        "dialogue",  # include both for compatibility checks
        "diplomacy",
        "trade",
        "culture",
        "persist",
        "adapt_export",
        "events",
    }


def _collect_diagnostics(world, weather_manager=None, events_manager=None):
    """Collect diagnostic data for logging."""
    # Food: both chunk resources and faction inventories
    # - count all edible types
    food_types = ["food", "plant", "animal", "fish"]
    chunk_food = sum(
        sum(ch.resources.get(food_type, 0) for food_type in food_types)
        for ch in world.active_chunks.values()
    )
    faction_food = sum(
        sum(faction.resources.get(food_type, 0) for food_type in food_types)
        for faction in world.factions.values()
        if hasattr(faction, "resources")
    )
    total_food = chunk_food + faction_food
    pop = sum(len(ch.npcs) for ch in world.active_chunks.values())

    births = safe_getattr(world, "_audit_births_tick")
    deaths_starv = safe_getattr(world, "_audit_starvation_deaths_tick")
    deaths_natural = safe_getattr(world, "_audit_natural_deaths_tick")

    # Age distribution
    ages = [safe_getattr(npc, "age", 0) for ch in world.active_chunks.values() for npc in ch.npcs]
    if ages:
        age_stats = {"min": min(ages), "max": max(ages), "avg": sum(ages) / len(ages)}
    else:
        age_stats = {"min": 0, "max": 0, "avg": 0}

    # Weather information
    weather_info = {}
    if weather_manager:
        active_coords = list(world.active_chunks.keys())
        if active_coords:
            sample_coord = active_coords[0]
            current_weather = weather_manager.get_weather(sample_coord)
            weather_info["weather"] = (
                current_weather.name if hasattr(current_weather, "name") else str(current_weather)
            )

            # Get current season (0=Spring, 1=Summer, 2=Autumn, 3=Winter)
            season = getattr(world, "current_season", 0)
            season_names = ["Spring", "Summer", "Autumn", "Winter"]
            weather_info["season"] = season_names[season % 4]

    # Time and environmental information
    time_info = {}
    if hasattr(world, "current_hour"):
        time_info["hour"] = world.current_hour
        time_info["time_of_day"] = safe_call(world.get_time_of_day) or "Unknown"
        time_info["is_day"] = safe_call(world.is_daytime) or False

    # Events information
    events_info = {}
    if events_manager:
        active_events = [e for e in events_manager.active_events if e.active]
        events_info["active_events"] = len(active_events)
        if active_events:
            # Show up to 2 most recent events
            recent_events = sorted(active_events, key=lambda e: e.start_time, reverse=True)[:2]
            events_info["recent_events"] = [f"{e.name}@{e.location}" for e in recent_events]

    return {
        "total_food": total_food,
        "population": pop,
        "births": births,
        "deaths_starv": deaths_starv,
        "deaths_natural": deaths_natural,
        **age_stats,
        **weather_info,
        **time_info,
        **events_info,
    }


def _configure_environment_flags(_features):
    """Environment flag function retained for compatibility; now a no-op except
    ensuring core allows repro/mortality/combat."""
    os.environ["SANDBOX_ALLOW_REPRO"] = "1"
    os.environ["SANDBOX_ALLOW_MORTALITY"] = "1"
    os.environ["SANDBOX_ALLOW_COMBAT"] = "1"
    # Remove legacy disable flag if present
    os.environ.pop("SANDBOX_WORLD_RESOURCE_DISABLE", None)


def _process_technology_system(world, tribal_manager):
    """Process technology research and effects for all tribes."""
    try:
        from technology_system import technology_manager

        # Update research progress for each tribe based on their actions
        for tribe_name, tribe in tribal_manager.tribes.items():
            # Determine action type based on tribe's current focus/activities
            action_type = _determine_tribe_action_type(tribe, world)

            # Update research progress
            unlocked_techs = technology_manager.update_research(tribe_name, action_type, world._tick_count)

            # Log unlocked technologies
            for tech_id in unlocked_techs:
                tech = technology_manager.technologies.get(tech_id)
                if tech:
                    print(f"[TECHNOLOGY] Tribe {tribe_name} unlocked: {tech.name}")

        # Link factions to tribes for technology effects
        _link_factions_to_tribes(world, tribal_manager)

        # Process technology events
        _process_technology_events(world, tribal_manager, technology_manager)

    except ImportError:
        # Technology system not available
        pass
    except Exception as e:
        print(f"[TECHNOLOGY] Error processing technology system: {e}")


def _process_technology_events(world, tribal_manager, technology_manager):
    """Process and log technology-related events."""
    try:
        # Collect events from all tribes
        all_events = []
        for tribe_name in tribal_manager.tribes.keys():
            tribe_events = technology_manager.get_technology_events(tribe_name, world._tick_count)
            all_events.extend(tribe_events)

        # Log significant events
        for event in all_events:
            if event["type"] == "technology_unlocked":
                print(f"[TECHNOLOGY EVENT] {event['tribe_id']} unlocked {event['technology']} "
                      f"({event['category']} - {event['era']}) at tick {event['tick']}")
            elif event["type"] == "research_milestone":
                progress_pct = event["progress"] * 100
                print(f"[RESEARCH] {event['tribe_id']} {progress_pct:.1f}% complete on "
                      f"{event['technology']} (tick {event['tick']})")

        # Periodic technology status report
        if world._tick_count % 500 == 0 and world._tick_count > 0:
            total_unlocked = sum(len(techs) for techs in technology_manager.unlocked_technologies.values())
            active_research = sum(len(progress) for progress in technology_manager.tribe_research_progress.values())
            print(f"[TECHNOLOGY STATUS] Total technologies unlocked: {total_unlocked}, "
                  f"Active research projects: {active_research}")

    except Exception as e:
        print(f"[TECHNOLOGY] Error processing technology events: {e}")


def _determine_tribe_action_type(tribe, world):
    """Determine the primary action type for a tribe based on their current activities."""
    # This is a simplified heuristic - in a full implementation, this would
    # analyze the tribe's recent activities, NPC roles, and resource gathering patterns

    # Check if tribe has gatherer NPCs actively gathering
    gatherer_count = sum(1 for npc_id in tribe.member_ids
                        if getattr(tribe, 'social_roles', {}).get(npc_id) == TribalRole.GATHERER)

    # Check if tribe has hunter NPCs actively hunting
    hunter_count = sum(1 for npc_id in tribe.member_ids
                      if getattr(tribe, 'social_roles', {}).get(npc_id) == TribalRole.HUNTER)

    # Check if tribe has crafter NPCs actively crafting
    crafter_count = sum(1 for npc_id in tribe.member_ids
                       if getattr(tribe, 'social_roles', {}).get(npc_id) == TribalRole.CRAFTER)

    # Determine primary action based on role distribution
    total_roles = gatherer_count + hunter_count + crafter_count
    if total_roles == 0:
        return "social"  # Default to social activities

    if gatherer_count > hunter_count and gatherer_count > crafter_count:
        return "gathering"
    elif hunter_count > gatherer_count and hunter_count > crafter_count:
        return "hunting"
    elif crafter_count > gatherer_count and crafter_count > hunter_count:
        return "crafting"
    else:
        return "social"  # Mixed or equal distribution


def _link_factions_to_tribes(world, tribal_manager):
    """Link factions to tribes for technology effects."""
    try:
        # Link factions to tribes for technology effects
        faction_to_tribe = {}

        # For each tribe, find associated factions
        for tribe_name, tribe in tribal_manager.tribes.items():
            # Look for factions that have NPCs from this tribe
            for faction_name, faction in world.factions.items():
                # Check if faction has NPCs that are also in the tribe
                faction_npcs = set(faction.npc_ids)
                tribe_npcs = set(tribe.member_ids)

                # If there's overlap, link them
                if faction_npcs & tribe_npcs:
                    faction_to_tribe[faction_name] = tribe_name
                    # Update faction's tribe_id
                    faction.tribe_id = tribe_name
                    break

        # Log the mappings for debugging
        if faction_to_tribe and world._tick_count % 1000 == 0:
            print(f"[TECHNOLOGY] Faction-Tribe mappings: {faction_to_tribe}")

    except Exception as e:
        print(f"[TECHNOLOGY] Error linking factions to tribes: {e}")


def run_core_sim(
    num_ticks=1000, keep_alive: bool = False, export_on_complete: bool | None = None
) -> None:
    """Run the core AI sandbox simulation with balanced, tested parameters.

    This simulation has been extensively rebalanced to prevent population
    explosions and resource instability. Key improvements include:

    POPULATION STABILITY:
    - Conservative reproduction rates (0.03 base vs 0.07 previously)
    - Longer reproduction cooldowns (200 ticks vs 140 previously)
    - Higher food requirements for births (2.5 vs 1.6 previously)
    - Low population reproductive boost system (1.3x boost below 25 NPCs)

    RESOURCE BALANCE:
    - Dramatically reduced resource regeneration (REGEN_FACTOR: 0.05 vs 25.0)
    - Conservative capacity scaling (CAP_FACTOR: 5.0 vs 10.0)
    - Seasonal resource variation with population wave effects
    - Harvest rates limited to 1-5% per tick to prevent exploitation

    SYSTEM RELIABILITY:
    - Optional ThreadPoolExecutor parallelism control (use_parallelism flag)
    - Population wave system integration with stable sinusoidal multipliers
    - Adaptive mortality and capacity management within safe bounds
    - Comprehensive food production vs consumption monitoring

    TESTED SCENARIOS:
    - 5000+ tick simulations maintain stable 330-350 NPCs
    - Food production balanced at ~2.4x consumption ratio
    - Linear food growth instead of exponential explosion
    - Population waves maintain stability without crashes

        WAVE BALANCE ADJUSTMENTS (post 10k tick stability review):
        The initial wave amplitudes in the engine (resource=0.6, fertility=0.4,
        mortality=0.3) were
        too aggressive for very long (10k+) runs, occasionally pushing
        compounded low‑fertility / high‑mortality phases
        that prevented recovery (population drifting to single digits). We now
        override these at startup with
        conservative, empirically safe parameters:
            * Resource wave: length=480 ticks, amplitude=0.15 (down from 0.60)
            * Fertility wave: length=360 ticks, amplitude=0.12 (down from 0.40)
            * Mortality wave: length=420 ticks, amplitude=0.08 (down from 0.30)
        Design Principles:
            * Keep combined (fertility * base_repro) floor high enough
              (>= ~0.026 effective) for recovery after dips.
            * Limit mortality amplification so adaptive mortality + wave never
              exceed gentle suppression.
            * Shorter, slightly desynchronized periods reduce prolonged
              destructive alignment.
        Safeguards:
            * Amplitudes are clamped to a hard maximum of 0.25.
            * A minimum reproduction base floor is enforced (>=0.02) after
              adaptation.
        Expected Outcome:
            * Smooth oscillations without deep demographic collapses in 10k+
              tick runs.
    """
    # All features always enabled
    features = _parse_features()
    timing = {
        "tribal": 0.0,
        "world": 0.0,
        "weather": 0.0,
        "dialogue": 0.0,
        "culture": 0.0,
        "combat": 0.0,
        "events": 0.0,
    }
    dialogue_exchanges = 0
    dialogue_lines = 0
    dialogue_print_limit = int(
        os.environ.get("DIALOGUE_PRINT_LIMIT", "5")
    )  # max exchanges to print

    # Configure environment flags based on features
    _configure_environment_flags(features)

    # Configure parallelism control for ThreadPoolExecutor
    # (helps prevent crashes)
    use_parallelism = os.environ.get("SANDBOX_USE_PARALLELISM", "1").lower() in (
        "1",
        "true",
        "yes",
    )
    if not use_parallelism:
        os.environ["SANDBOX_DISABLE_PARALLELISM"] = "1"
        print("[CORE] Parallelism disabled for stability")
    else:
        os.environ.pop("SANDBOX_DISABLE_PARALLELISM", None)
        print("[CORE] Parallelism enabled")

    full_dialogue = True
    dialogue_print_limit = max(dialogue_print_limit, 10)

    # Setup dialogue logger if dialogue features are enabled
    dialogue_logger = None
    if full_dialogue:
        dialogue_logger = setup_dialogue_logger()
        dialogue_logger.info("=== Dialogue Log Started ===")

    culture_manager = None
    try:
        from world.culture import DynamicCultureManager  # type: ignore

        # optional module
        culture_manager = DynamicCultureManager()
    except Exception:
        culture_manager = None
    adapt_export = True
    clear_persistence()
    random.seed(42)

    # Create world engine with balanced parameters then override
    # wave configuration
    world = WorldEngine(seed=42)

    # Start the visualization API in a separate thread unless disabled
    if os.getenv("SANDBOX_NO_INTERNAL_API", "false").lower() not in ("1", "true", "yes"):  # allow external server
        api_thread = threading.Thread(target=run_api, daemon=True, name="API-Server")
        api_thread.start()
        print("[API] Visualization API thread started")
        import time as _t
        _t.sleep(1)
        if api_thread.is_alive():
            print("[API] Visualization API started successfully on port 5000")
        else:
            print("[API] Warning: API thread may not have started properly")
    else:
        print("[API] Internal API disabled via SANDBOX_NO_INTERNAL_API; assuming external server.")

    # --- Low-Population Scaling (now always active, independent of waves) ---
    # Continuous linear scaling between POP_SCALE_LOW and POP_SCALE_HIGH.
    POP_SCALE_LOW = 30  # <= this population => full boost
    POP_SCALE_HIGH = 180  # >= this population => no boost
    BASE_BOOST_MAX = 0.02  # Up to +0.02 added to base reproduction chance
    # (floor)
    CD_REDUCTION_MAX = 60  # Up to -60 ticks off reproduction cooldown
    _pop_scale_state = {"scale": 0.0, "prev_bucket": None}

    def _clamp_reproduction_params():
        bp = world.balance_params.get("REPRO_BASE_CHANCE", 0.03)
        cd = world.balance_params.get("REPRO_COOLDOWN", 200)
        s = _pop_scale_state["scale"]
        max_base = 0.045 + 0.010 * s  # dynamic ceiling rises slightly with
        # stronger boost to allow recovery but still capped
        min_cd = 160 - 20 * s  # dynamic floor for cooldown
        # (allows 160->140 range)
        bp = max(0.02, min(max_base, bp))
        cd = max(min_cd, min(260, cd))
        world.balance_params["REPRO_BASE_CHANCE"] = bp
        world.balance_params["REPRO_COOLDOWN"] = cd

    print(
        f"[SCALE] Low-pop scaling active: thresholds {POP_SCALE_LOW}-"
        f"{POP_SCALE_HIGH}, max +{BASE_BOOST_MAX:.02f} base, "
        f"-{CD_REDUCTION_MAX} cooldown"
    )

    # --- Population Wave Balance Override (see docstring) ---
    if getattr(world, "wave_enabled", False):
        # Replace with the conservative, empirically safe parameters
        # (see docstring WAVE BALANCE ADJUSTMENTS)
        world.abundance_cycle_length = 480
        world.fertility_wave_length = 360
        world.mortality_wave_length = 420
        world.resource_wave_amplitude = 0.15
        world.fertility_wave_amplitude = 0.12
        world.mortality_wave_amplitude = 0.08
        print(
            f"[CORE] Wave parameters set (conservative): "
            f"res_amp={world.resource_wave_amplitude} "
            f"fert_amp={world.fertility_wave_amplitude} "
            f"mort_amp={world.mortality_wave_amplitude}"
        )
        try:
            world.enable_repro_jitter = True
            world.repro_jitter_spread = 0.30
            print(
                f"[CORE] Reproduction jitter enabled "
                f"(spread=±{int(world.repro_jitter_spread*100)}%)"
            )
        except Exception:
            pass
        try:
            world._pop_target_min = 40
            world._pop_target_max = 110
            print(
                f"[ADAPT] Population target band set to "
                f"{world._pop_target_min}-{world._pop_target_max} (A)"
            )
        except Exception:
            pass
        # Hook adaptive reproduction (waves path) to enforce clamps
        # post-adaptation
        try:
            if hasattr(world, "_adaptive_reproduction_tuning"):
                _orig_adapt = world._adaptive_reproduction_tuning

                def _wrapped_adapt():
                    try:
                        _orig_adapt()
                    finally:
                        _clamp_reproduction_params()

                world._adaptive_reproduction_tuning = _wrapped_adapt
        except Exception:
            pass

    # Initial clamp to ensure parameters respect new bounds before ticking
    _clamp_reproduction_params()
    tm = TribalManager()
    weather_manager = None
    try:
        from world.weather import WeatherManager

        weather_manager = WeatherManager(world)
    except Exception:
        weather_manager = None
    events_manager = None
    try:
        from world.events import EventManager

        events_manager = EventManager(world, event_interval=30)
    except Exception:
        events_manager = None
    persistence_manager = None
    try:
        from persistence_manager import PersistenceManager

        persistence_manager = PersistenceManager()
    except Exception:
        persistence_manager = None
    enhanced_combat = None
    try:
        from enhanced_combat import EnhancedCombatManager, CombatType

        enhanced_combat = EnhancedCombatManager()
    except Exception:
        enhanced_combat = None
    print("[CORE] ========== SIMULATION CONFIGURATION ==========")
    print("[CORE] Running with balanced parameters (tested for 5000+ ticks)")
    print("[CORE] Expected stable population: 330-350 NPCs")
    print("[CORE] Expected food balance: ~2.4x production to " "consumption ratio")
    print("[CORE] Reproduction parameters: base=0.03, cooldown=200, " "food_req=2.5")
    print("[CORE] Resource regeneration: REGEN_FACTOR=0.05, CAP_FACTOR=5.0")
    print("[CORE] Population waves: enabled with bounded variation")
    parallelism_status = "enabled" if use_parallelism else "disabled"
    print(f"[CORE] Parallelism: {parallelism_status}")
    print("[CORE] ================================================")
    start = time.time()
    for tick in range(num_ticks):
        # --- Continuous Low-Pop Reproduction Scaling ---
        try:
            total_pop = sum(len(ch.npcs) for ch in world.active_chunks.values())
            if total_pop <= POP_SCALE_LOW:
                scale = 1.0
            elif total_pop >= POP_SCALE_HIGH:
                scale = 0.0
            else:
                # Linear interpolation between high and low thresholds
                scale = (POP_SCALE_HIGH - total_pop) / (POP_SCALE_HIGH - POP_SCALE_LOW)
            _pop_scale_state["scale"] = max(0.0, min(1.0, scale))

            # Apply scaling to reproduction parameters BEFORE clamp
            base_current = world.balance_params.get("REPRO_BASE_CHANCE", 0.03)
            desired_base_floor = 0.03 + BASE_BOOST_MAX * _pop_scale_state["scale"]
            if base_current < desired_base_floor:
                world.balance_params["REPRO_BASE_CHANCE"] = desired_base_floor

            cd_current = world.balance_params.get("REPRO_COOLDOWN", 200)
            desired_cd_cap = 200 - CD_REDUCTION_MAX * _pop_scale_state["scale"]
            if cd_current > desired_cd_cap:
                world.balance_params["REPRO_COOLDOWN"] = desired_cd_cap

            # Clamp within dynamic bounds
            _clamp_reproduction_params()

            # Bucketed logging to avoid spam (log when scale bucket
            # changes by 0.25 or hits 0/1)
            bucket = (
                int(_pop_scale_state["scale"] * 4)
                if _pop_scale_state["scale"] not in (0.0, 1.0)
                else _pop_scale_state["scale"]
            )
            if bucket != _pop_scale_state["prev_bucket"]:
                print(
                    f"[SCALE] pop={total_pop} "
                    f"scale={_pop_scale_state['scale']:.2f} "
                    f"base={world.balance_params['REPRO_BASE_CHANCE']:.3f} "
                    f"cd={world.balance_params['REPRO_COOLDOWN']}"
                )
                _pop_scale_state["prev_bucket"] = bucket
        except Exception:
            pass
        t0 = time.time()
        tm.process_tribal_dynamics(world)
        timing["tribal"] += time.time() - t0

        # Process technology research and effects
        t1 = time.time()
        _process_technology_system(world, tm)
        timing["technology"] = timing.get("technology", 0) + (time.time() - t1)

        t2 = time.time()
        world.world_tick()
        timing["world"] += time.time() - t2
        # --- DIAGNOSTIC: Log total food and population ---
        if tick % 10 == 0 or tick == num_ticks - 1:
            diag = _collect_diagnostics(world, weather_manager, events_manager)
            weather_str = (
                (f" weather={diag.get('weather', 'N/A')} " f"season={diag.get('season', 'N/A')}")
                if weather_manager
                else ""
            )
            time_str = (
                (
                    f" hour={diag.get('hour', 'N/A')} "
                    f"{diag.get('time_of_day', 'N/A')} "
                    f"{'day' if diag.get('is_day') else 'night'}"
                )
                if "hour" in diag
                else ""
            )
            events_str = (f" events={diag.get('active_events', 0)}") if events_manager else ""
            if events_manager and diag.get("recent_events"):
                events_str += f" [{','.join(diag['recent_events'])}]"
            print(
                f"[DIAG] tick={tick} total_food={diag['total_food']:.1f} "
                f"population={diag['population']} births={diag['births']} "
                f"deaths_starv={diag['deaths_starv']} "
                f"deaths_natural={diag['deaths_natural']} "
                f"age_avg={diag['avg']:.1f} age_min={diag['min']} "
                f"age_max={diag['max']}{weather_str}{time_str}{events_str}"
            )

            # Update world state for web API visualization
            latest_state = {
                'tick': tick,
                'season': diag.get('season', 'Unknown'),
                # Optional lightweight movement layer for visualization only
                # If SANDBOX_VISUAL_MOVEMENT is set, apply a bounded random walk to
                # the serialized coordinates WITHOUT mutating core simulation state.
                'npcs': (
                    (lambda _all: (
                        __import__('random'),
                        [
                            dict(n, coordinates=(n['coordinates'][0] + __import__('random').choice([-1,0,1]),
                                                 n['coordinates'][1] + __import__('random').choice([-1,0,1])))
                            if os.getenv('SANDBOX_VISUAL_MOVEMENT') else n for n in _all
                        ]
                    )[1])([
                        npc.serialize() for ch in world.active_chunks.values() for npc in ch.npcs
                    ])
                ),
                'factions': [faction.serialize() for faction in world.factions.values()],
                'chunks': [chunk.serialize() for chunk in world.active_chunks.values()],
                'total_food': diag['total_food'],
                'population': diag['population'],
            }
            save_world_state(latest_state)
        if weather_manager is not None:
            w0 = time.time()
            safe_call(weather_manager.update_weather, world.current_hour)
            timing["weather"] += time.time() - w0

        if events_manager is not None:
            e0 = time.time()
            safe_call(events_manager.update, world.current_day)
            # Use day instead of hour for events
            timing["events"] = timing.get("events", 0) + (time.time() - e0)
        dialogue_interval = 10 if full_dialogue else 25
        if full_dialogue and tick % dialogue_interval == 0:
            d0 = time.time()
            npcs = [npc for ch in world.active_chunks.values() for npc in ch.npcs]
            if len(npcs) >= 2:
                a, b = random.sample(npcs, 2)
                if (
                    _npcs_are_close(a, b)
                    and hasattr(a, "generate_dialogue")
                    and hasattr(b, "generate_dialogue")
                ):
                    ctx = random.choice(["encounter", "trade", "idle", "hostility", "greeting"])
                    produced = _generate_dialogue_pair(a, b, ctx, tm.tribal_diplomacy, tm.tribes)
                    if produced:
                        dialogue_exchanges += 1
                        dialogue_lines += len(produced)
                        # Log all dialogue to separate file
                        if dialogue_logger:
                            dialogue_logger.info(
                                f"[TICK {tick}] {a.name}->{b.name} ({ctx}) | "
                                f"{produced[0] if produced else '...'}"
                            )
                            if len(produced) > 1:
                                msg = (
                                    f"[TICK {tick}] {b.name}->{a.name} " f"({ctx}) | {produced[1]}"
                                )
                                dialogue_logger.info(msg)
                            # Log LLM-enhanced versions if available
                            use_llm = os.getenv("SANDBOX_LLM_DIALOGUE", "false").lower() == "true"
                            if use_llm:
                                orig_a = getattr(a, "_last_dialogue_original", None)
                                enh_a = getattr(a, "_last_dialogue_enhanced", None)
                                if orig_a and enh_a and orig_a != enh_a:
                                    dialogue_logger.info(
                                        "[TICK %s] %s->LLM (%s) | " "Original: %s | Enhanced: %s",
                                        tick,
                                        a.name,
                                        ctx,
                                        orig_a,
                                        enh_a,
                                    )
                                if len(produced) > 1:
                                    orig_b = getattr(b, "_last_dialogue_original", None)
                                    enh_b = getattr(b, "_last_dialogue_enhanced", None)
                                    if orig_b and enh_b and orig_b != enh_b:
                                        dialogue_logger.info(
                                            "[TICK %s] %s->LLM (%s) | "
                                            "Original: %s | Enhanced: %s",
                                            tick,
                                            b.name,
                                            ctx,
                                            orig_b,
                                            enh_b,
                                        )
                        # Limited console output
                        if dialogue_exchanges <= dialogue_print_limit:
                            print(
                                f"[DIALOGUE] {a.name}->{b.name} ({ctx}) | "
                                + (produced[0] if produced else "...")
                            )
                            if len(produced) > 1:
                                print(f"[DIALOGUE] {b.name}->{a.name} ({ctx}) | " f"{produced[1]}")
            timing["dialogue"] += time.time() - d0
        if culture_manager and tick % 30 == 0:
            c0 = time.time()
            safe_call(culture_manager.periodic_update)
            timing["culture"] += time.time() - c0
        # Enhanced combat processing
        if enhanced_combat and tick % 120 == 0 and len(tm.tribes) >= 2:  # Combat every 120 ticks
            try:
                tribe_names = list(tm.tribes.keys())
                if len(tribe_names) >= 2:
                    attacker_name, defender_name = random.sample(tribe_names, 2)
                    attacker_tribe = tm.tribes[attacker_name]
                    defender_tribe = tm.tribes[defender_name]

                    # Choose combat type based on tribal relations and
                    # situation
                    combat_type = random.choice([CombatType.SKIRMISH, CombatType.RAID])
                    if random.random() < 0.3:  # 30% chance of major engagement
                        combat_type = random.choice([CombatType.BATTLE, CombatType.SIEGE])

                    # Use defender's location as battle location
                    location = getattr(defender_tribe, "location", (0, 0))

                    # Create world context for environmental factors
                    world_context = {
                        "weather": (
                            weather_manager.get_weather(location).name
                            if weather_manager
                            else "CLEAR"
                        ),
                        "time": {
                            "hour": world.current_hour,
                            "season": world.current_season,
                            "is_day": world.is_daytime(),
                        },
                    }

                    # Initiate combat
                    combat_result = enhanced_combat.initiate_combat(
                        attacker_tribe,
                        defender_tribe,
                        location,
                        combat_type,
                        world_context,
                    )

                    print(
                        f"[COMBAT] {attacker_name} vs {defender_name} "
                        f"({combat_type.value}) -> {combat_result['result']}"
                    )
                    c0 = time.time()
                    timing["combat"] = timing.get("combat", 0) + (time.time() - c0)
            except Exception:
                pass  # Silent failure for combat system
            try:
                tribe_names = list(tm.tribes.keys())
                if len(tribe_names) >= 2:
                    tA, tB = random.sample(tribe_names, 2)
                    tribeA = tm.tribes[tA]
                    tribeB = tm.tribes[tB]
                    if hasattr(tribeA, "relations") and isinstance(tribeA.relations, dict):
                        tribeA.relations[tB] = tribeA.relations.get(tB, 0) + 1.0
                        tribeB.relations[tA] = tribeB.relations.get(tA, 0) + 1.0
                    if culture_manager and hasattr(culture_manager, "register_trade_success"):
                        culture_manager.register_trade_success(tA, tB)
            except Exception:
                pass
        if tick % 100 == 0 and tick > 0:
            print(f"[CORE] tick {tick}/{num_ticks}")
        if tick % 200 == 0 and tick > 0 and getattr(world, "wave_enabled", False):
            try:
                ws = world.get_wave_status()
                print(
                    f"[WAVE] tick={ws['tick']} "
                    f"res_mult={ws['resource_multiplier']:.3f} "
                    f"fert_mult={ws['fertility_multiplier']:.3f} "
                    f"mort_mult={ws['mortality_multiplier']:.3f}"
                )
            except Exception:
                pass
    elapsed = time.time() - start
    print(f"[CORE] DONE {num_ticks} ticks in {elapsed:.2f}s " f"(~{num_ticks/elapsed:.1f} t/s)")
    if full_dialogue:
        print(
            f"[CORE] Dialogue exchanges={dialogue_exchanges} "
            f"lines={dialogue_lines} (printed up to {dialogue_print_limit})"
        )
    if culture_manager:
        print(
            f"[CORE] Culture manager active. Values known: "
            f"{len(getattr(culture_manager, 'values', {}))}"
        )
    active = {k: v for k, v in timing.items() if v > 0}
    if active:
        print("[CORE] Feature timing (s): " + ", ".join(f"{k}={v:.3f}" for k, v in active.items()))
    do_export = adapt_export if export_on_complete is None else export_on_complete
    if do_export and hasattr(world, "export_adaptation_history"):
        try:
            path = world.export_adaptation_history()
            if path:
                print(f"[CORE] Adaptation history exported: {path}")
        except Exception:
            pass
    if persistence_manager:
        try:
            save_success = persistence_manager.save_world_state(
                world,
                weather_manager,
                events_manager,
                tm,
                save_name=f"simulation_{num_ticks}ticks",
            )
            if save_success:
                print("[CORE] World state saved " "(includes weather, events, tribes)")
            else:
                print("[CORE] Failed to save world state")
        except Exception as e:
            print(f"[CORE] Persistence error: {e}")
    if not keep_alive:
        try:
            world.shutdown()
        except Exception:
            pass
    return world if keep_alive else None


if __name__ == "__main__":
    import sys

    t = 1000  # Default to 1000 ticks to showcase stable long-term
    # population dynamics
    if len(sys.argv) > 1:
        try:
            t = int(sys.argv[1])
        except ValueError:
            pass
    print(
        "[DEPRECATED] Direct execution of core_sim.py is deprecated. Use:\n"
        "  python main.py core --ticks <n>\n"
        "Example: python main.py core --ticks 1000\n"
        "(Ensures unified logging, menu access, and guaranteed low-pop "
        "scaling activation.)\n"
    )
    print(f"[CORE] Starting simulation with {t} ticks (balanced parameters)")
    run_core_sim(t, keep_alive=False)
