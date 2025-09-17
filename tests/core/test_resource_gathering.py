def test_faction_resource_gathering():
    from factions.faction import Faction
    class DummyChunk:
        def __init__(self):
            self.resources = {}
    class DummyWorld:
        def __init__(self):
            self.current_season = 'Spring'
            self.balance_params = {}
        def get_chunk(self, x, y):
            return DummyChunk()
    faction = Faction(name='TestFaction', territory=[(0,0)])
    faction.resources['food'] = 10
    world = DummyWorld()
    faction.gather_resources(world)
    assert 'food' in faction.resources
