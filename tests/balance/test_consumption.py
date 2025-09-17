import math
from world.engine import WorldEngine
from factions.faction import Faction


class DummyWorld(WorldEngine):
    """Lightweight subclass overriding heavy systems for targeted tests."""

    def __init__(self):
        super().__init__(auto_seed=False)
        # Disable resource distribution side-effects by clearing active chunks
        self.active_chunks = {}


def test_basic_consumption_decrease():
    w = DummyWorld()
    f = Faction(name="Testers")
    # Give a territory so gather_resources won't early return; but skip chunk activation
    f.territory = []  # empty to avoid harvesting; we only test consumption
    # Add population
    f.npc_ids = [f"npc_{i}" for i in range(10)]  # pop=10
    # Provide food
    f.resources["food"] = 10.0
    w.factions[f.name] = f

    initial_food = f.resources["food"]
    # One tick worth of consumption: per NPC per day =1; per tick=1/1440
    per_tick_need = len(f.npc_ids) * (1.0 / (w.MINUTES_PER_HOUR * w.HOURS_PER_DAY))
    f.consume_resources(w)
    expected = initial_food - per_tick_need
    assert math.isclose(
        f.resources["food"], expected, rel_tol=1e-6
    ), f"Food did not decrease correctly: {f.resources['food']} vs {expected}"
    assert (
        getattr(f, "_starvation_pressure", 0.0) == 0.0
    ), "Starvation pressure should not increase when food sufficient"


def test_starvation_accumulates():
    w = DummyWorld()
    f = Faction(name="Hungry")
    f.npc_ids = [f"npc_{i}" for i in range(5)]  # pop=5
    f.resources["food"] = 0.0  # trigger deficit
    w.factions[f.name] = f

    per_tick_need = len(f.npc_ids) * (1.0 / (w.MINUTES_PER_HOUR * w.HOURS_PER_DAY))
    f.consume_resources(w)
    # All food consumed (already 0), starvation increases by per_tick_need
    assert math.isclose(
        getattr(f, "_starvation_pressure", 0.0), per_tick_need, rel_tol=1e-6
    ), "Starvation pressure did not accumulate deficit"


def test_starvation_decay():
    w = DummyWorld()
    f = Faction(name="Recovering")
    f.npc_ids = [f"npc_{i}" for i in range(3)]
    w.factions[f.name] = f
    # Manually set starvation pressure
    f._starvation_pressure = 5.0
    f.resources["food"] = 10.0
    f.consume_resources(w)
    # Should have decayed by 0.1
    assert math.isclose(
        f._starvation_pressure, 4.9, rel_tol=1e-6
    ), f"Starvation pressure did not decay: {f._starvation_pressure}"


def test_diagnostics_starvation_aggregation():
    w = DummyWorld()
    # Create two factions with different starvation
    f1 = Faction(name="A")
    f1.npc_ids = ["a1"]
    f1._starvation_pressure = 2.0
    f2 = Faction(name="B")
    f2.npc_ids = ["b1"]
    f2._starvation_pressure = 4.0
    w.factions[f1.name] = f1
    w.factions[f2.name] = f2
    snap = w.diagnostics_snapshot()
    starv = snap["starvation"]
    assert (
        starv["total"] == 6.0
        and starv["max"] == 4.0
        and math.isclose(starv["avg"], 3.0, rel_tol=1e-6)
    ), f"Starvation aggregation incorrect: {starv}"


if __name__ == "__main__":
    test_basic_consumption_decrease()
    test_starvation_accumulates()
    test_starvation_decay()
    test_diagnostics_starvation_aggregation()
    print("Consumption tests passed.")
