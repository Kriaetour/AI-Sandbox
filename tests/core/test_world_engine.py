def test_world_tick_runs():
    from world.engine import WorldEngine
    world = WorldEngine(seed=42)
    world.world_tick()
    assert hasattr(world, 'active_chunks')
    assert isinstance(world.active_chunks, dict)
