def test_faction_and_tribe_creation():
    from world.engine import WorldEngine
    from tribes.tribal_manager import TribalManager
    world = WorldEngine(seed=43)
    tribal_manager = TribalManager()
    tribe = tribal_manager.create_tribe('TestTribe', 'founder_test', (0,0))
    assert tribe is not None
    # Create a Faction for the tribe and add to world.factions
    from factions.faction import Faction
    world.factions['TestTribe'] = Faction(name='TestTribe', territory=[(0,0)])
    assert 'TestTribe' in world.factions
