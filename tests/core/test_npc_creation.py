def test_npc_creation_and_traits():
    from npcs.npc import NPC
    npc = NPC(name='TestNPC', coordinates=(0,0), faction_id='TestFaction')
    npc.traits.append('brave')
    assert 'brave' in npc.traits
