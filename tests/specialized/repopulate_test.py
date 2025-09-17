import logging
from world.engine import WorldEngine
from factions.faction import Faction


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    # Create world with auto seed threshold small
    world = WorldEngine(
        auto_seed=True,
        auto_seed_threshold=5,
        min_population=4,
        zero_pop_warning_interval=3,
    )
    # Add existing factions WITHOUT NPCS to trigger repopulate path (not SeedFaction)
    world.factions["Alpha"] = Faction(name="Alpha", territory=[(2, 2)])
    world.factions["Beta"] = Faction(name="Beta", territory=[(5, 5)])

    for i in range(12):
        world.world_tick()

    snap = world.diagnostics_snapshot()
    print("Final snapshot:", snap)
    assert snap["repopulated_existing"] is True, "Repopulation path did not trigger"
    assert not snap["auto_seeded"], "Auto-seed should not have been used when factions exist"
    assert snap["total_npcs"] >= 2, "Expected at least one NPC per faction"
    print("Repopulation test passed.")


if __name__ == "__main__":
    main()
