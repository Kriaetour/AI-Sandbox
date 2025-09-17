def test_persistence_manager():
    from persistence_manager import PersistenceManager
    from world.engine import WorldEngine
    pm = PersistenceManager()
    # Save and load a real world object
    world = WorldEngine(seed=123)
    pm.save_world_state(world)
    loaded = pm.load_world_state()
    assert isinstance(loaded, dict)
    # Check for expected keys in the saved world state
    assert 'metadata' in loaded or 'world' in loaded or 'active_chunks' in loaded
