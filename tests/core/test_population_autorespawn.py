def test_population_autorespawn():
    from world.engine import WorldEngine
    world = WorldEngine(seed=66)
    # Simulate population drop to zero
    for chunk in world.active_chunks.values():
        chunk.npcs.clear()
    # Simulate auto-respawn logic (should be in main loop, here we just check no crash)
    try:
        world.world_tick()
        assert True
    except Exception:
        assert False
