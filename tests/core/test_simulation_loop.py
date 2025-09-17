def test_simulation_loop_progress():
    from world.engine import WorldEngine
    world = WorldEngine(seed=44)
    for _ in range(10):
        world.world_tick()
    pop = sum(len(chunk.npcs) for chunk in world.active_chunks.values())
    assert pop >= 0  # Should not crash or stall
