def test_world_season_and_weather():
    from world.engine import WorldEngine
    from world import WeatherManager
    world = WorldEngine(seed=55)
    wm = WeatherManager(world)
    for _ in range(24*4):
        world.world_tick()
        wm.update_weather(world.current_hour)
    assert hasattr(world, 'current_season')
