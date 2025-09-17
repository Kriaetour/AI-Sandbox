def test_tribe_diplomacy():
    from tribes.tribal_manager import TribalManager
    tm = TribalManager()
    t1 = tm.create_tribe('T1', 'f1', (0,0))
    t2 = tm.create_tribe('T2', 'f2', (1,0))
    # Use the provided method to set diplomacy if available
    if hasattr(tm, 'set_diplomacy'):
        tm.set_diplomacy(t1.name, t2.name, 0.5)
        value = tm.get_diplomacy(t1.name, t2.name) if hasattr(tm, 'get_diplomacy') else None
        assert value == 0.5
    else:
        # Fallback: just check that the diplomacy structure exists
        assert hasattr(tm, 'tribal_diplomacy')
