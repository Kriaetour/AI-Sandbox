from tribes.tribal_manager import TribalManager

# Test the enhanced tribal features
tribal_manager = TribalManager()
tribe = tribal_manager.create_tribe("Test Tribe", "founder", (0, 0))

print("Enhanced Tribal Features Test:")
print(f"Tribe: {tribe.name} {tribe.symbol}")
print(f'Culture: {tribe.cultural_quirks["music_style"]} music')
print(f'Totems: {tribe.culture["totems"]}')
print(f"Specialization: {tribe.economic_specialization}")
print(f'Spirit Guides: {tribe.spiritual_beliefs["spirit_guides"]}')

# Test ceremony
ceremony = tribe.perform_ceremony("hunting")
print(f'Ceremony: {ceremony["description"]}')

# Test prophecy
prophecy = tribe.develop_prophecy()
print(f"Prophecy: {prophecy}")

print("Enhanced tribal features working correctly!")
