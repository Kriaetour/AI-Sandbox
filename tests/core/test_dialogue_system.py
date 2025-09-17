def test_dialogue_generation():
    from npcs.npc import NPC
    npc1 = NPC(name='A', coordinates=(0,0), faction_id='F1')
    npc2 = NPC(name='B', coordinates=(1,0), faction_id='F2')
    out = npc1.generate_dialogue(npc2, 'encounter', tribal_diplomacy={}, tribe_lookup=None)
    assert isinstance(out, str)
    assert len(out) > 0
