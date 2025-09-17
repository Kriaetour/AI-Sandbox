import logging
from world.engine import WorldEngine


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    # Configure small threshold for quick test
    world = WorldEngine(
        auto_seed=True,
        auto_seed_threshold=5,
        min_population=3,
        zero_pop_warning_interval=3,
    )
    for i in range(12):
        world.world_tick()
    snap = world.diagnostics_snapshot()
    print("Final snapshot:", snap)


if __name__ == "__main__":
    main()
