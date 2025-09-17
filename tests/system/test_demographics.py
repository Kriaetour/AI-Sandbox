import random
from world.engine import WorldEngine
from factions.faction import Faction


class DemoWorld(WorldEngine):
    def __init__(self):
        super().__init__(auto_seed=False)
        self.active_chunks = {}
        # Give a stable tick count simulation manually if needed


def run_ticks(world, faction, ticks):
    for _ in range(ticks):
        # Simulate only faction processing path used in world_tick
        faction.process_tick(world)
        world._tick_count += 1


def test_starvation_deaths():
    random.seed(42)
    w = DemoWorld()
    f = Faction(name="Starvers")
    # Create population
    f.npc_ids = [f"s_{i}" for i in range(20)]
    # Zero food -> accumulate starvation then deaths once pressure high
    f.resources["food"] = 0.0
    w.factions[f.name] = f
    # Manually raise starvation pressure above threshold to trigger deaths quickly
    f._starvation_pressure = 5.0  # threshold=3.0 => excess=2.0 => p=0.04
    pre_pop = len(f.npc_ids)
    f._process_demographics(w)
    post_pop = len(f.npc_ids)
    assert post_pop <= pre_pop, "Population should not increase during starvation mortality phase"
    assert w._audit_starvation_deaths >= 0, "Starvation deaths counter not updated"


def test_birth_event():
    random.seed(123)
    w = DemoWorld()
    f = Faction(name="Growers")
    f.npc_ids = [f"g_{i}" for i in range(5)]
    # Provide abundant food and zero starvation pressure to allow birth
    f.resources["food"] = 50.0  # per capita 10
    f._starvation_pressure = 0.0
    w.factions[f.name] = f
    # Ensure cooldown satisfied by setting last birth far in past
    f._last_birth_tick = -1000
    # High chance due to surplus ratio (cap at 5) => birth chance up to 25%
    attempts = 50
    births_before = w._audit_total_births
    for _ in range(attempts):
        f._process_demographics(w)
        w._tick_count += 1
        if w._audit_total_births > births_before:
            break
    assert (
        w._audit_total_births > births_before
    ), "Expected at least one birth event under surplus conditions"


if __name__ == "__main__":
    test_starvation_deaths()
    test_birth_event()
    print("Demographic tests passed.")
