def test_chunk_activation():
    from world.engine import WorldEngine
    world = WorldEngine(seed=77)
    x, y = 5, 5
    world.activate_chunk(x, y)
    chunk = world.get_chunk(x, y)
    assert chunk is not None
