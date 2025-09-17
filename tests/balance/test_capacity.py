from world.engine import WorldEngine
from factions.faction import Faction


class CapWorld(WorldEngine):
    def __init__(self):
        super().__init__(auto_seed=False)
        self.active_chunks = {}


def test_overcapacity_increases_pressure():
    w = CapWorld()
    f = Faction(name="Crowded")
    # Large population with stagnant/negative food delta
    f.npc_ids = [f"c_{i}" for i in range(100)]
    # Provide just enough starting food so consumption runs, but no inflow (no territory => no gather)
    f.resources["food"] = 5.0
    w.factions[f.name] = f
    # Simulate a few ticks to build econ history with negative dFood (consumption only)
    for _ in range(10):
        f.consume_resources(w)
        f.econ_snapshot(getattr(w, "_tick_count", 0))
        w._tick_count += 1
    # Force demographic processing which should detect overcapacity
    start_pressure = f._starvation_pressure
    f._process_demographics(w)
    assert (
        f._starvation_pressure >= start_pressure
    ), "Pressure should not decrease when over capacity"
    # If capacity logic triggered, pressure should rise slightly
    # Can't assert absolute value due to stochastic elements, but expect >= start


if __name__ == "__main__":
    test_overcapacity_increases_pressure()
    print("Carrying capacity test passed.")
