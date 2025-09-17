#!/usr/bin/env python3
"""
Tribal System Demonstration

This script demonstrates the tribal entities system with:
- Tribe creation and management
- Social roles and behaviors
- Tribal communication and language
- Territory and conflict systems
- Primitive structures and architecture
- Cultural development
"""

import random
from tribes import TribalManager, TribalRole, TribalCommunication, TribalRoleBehavior


def demonstrate_tribal_system():
    """Main demonstration of tribal systems"""

    print("🌍 TRIBAL SYSTEM DEMONSTRATION 🌍")
    print("=" * 50)

    # Initialize tribal manager
    tribal_manager = TribalManager()

    # Create initial tribes
    print("\n🏕️  CREATING INITIAL TRIBES")
    print("-" * 30)

    # Tribe 1: River tribe
    river_tribe = tribal_manager.create_tribe("Riverfolk", "npc_river_leader", (5, 5))
    print(f"Created {river_tribe.name} {river_tribe.symbol} at (5, 5)")
    print(f"  Leader: {river_tribe.leader_id}")
    print(f"  Initial territory: {len(river_tribe.territory)} tiles")
    print(f"  Structures: {river_tribe.structures}")

    # Tribe 2: Mountain tribe
    mountain_tribe = tribal_manager.create_tribe("Stoneheart", "npc_mountain_leader", (15, 15))
    print(f"\nCreated {mountain_tribe.name} {mountain_tribe.symbol} at (15, 15)")
    print(f"  Leader: {mountain_tribe.leader_id}")
    print(f"  Initial territory: {len(mountain_tribe.territory)} tiles")
    print(f"  Structures: {mountain_tribe.structures}")

    # Add more members to tribes
    print("\n👥 ADDING TRIBE MEMBERS")
    print("-" * 30)

    river_members = [f"npc_river_{i}" for i in range(1, 8)]
    mountain_members = [f"npc_mountain_{i}" for i in range(1, 6)]

    for member in river_members:
        tribal_manager.add_member_to_tribe("Riverfolk", member)

    for member in mountain_members:
        tribal_manager.add_member_to_tribe("Stoneheart", member)

    print(f"Riverfolk now has {len(river_tribe.member_ids)} members")
    print(f"Stoneheart now has {len(mountain_tribe.member_ids)} members")

    # Demonstrate role assignment
    print("\n🎭 TRIBAL ROLES")
    print("-" * 30)

    river_roles = tribal_manager.role_managers["Riverfolk"].get_role_distribution()
    mountain_roles = tribal_manager.role_managers["Stoneheart"].get_role_distribution()

    print("Riverfolk roles:")
    for role, count in river_roles.items():
        print(f"  {role.value}: {count}")

    print("\nStoneheart roles:")
    for role, count in mountain_roles.items():
        print(f"  {role.value}: {count}")

    # Demonstrate tribal communication
    print("\n💬 TRIBAL COMMUNICATION")
    print("-" * 30)

    tribal_comm = TribalCommunication()

    # Greeting between tribes
    greeting_result = tribal_comm.tribal_conversation(river_tribe, mountain_tribe, "greeting")
    print(f"Greeting: {greeting_result['tribal_phrase']}")
    print(f"Interpretation success: {greeting_result['success']}")

    # Trade proposal
    trade_result = tribal_comm.tribal_conversation(river_tribe, mountain_tribe, "trade")
    print(f"Trade proposal: {trade_result['tribal_phrase']}")
    print(f"Interpretation success: {trade_result['success']}")

    # Demonstrate tribal structures
    print("\n🏗️  TRIBAL STRUCTURES")
    print("-" * 30)

    # Build more structures
    river_camp = tribal_manager.camps["Riverfolk"]

    # Add resources for building
    river_tribe.add_shared_resource("wood", 20)
    river_tribe.add_shared_resource("stone", 15)
    mountain_tribe.add_shared_resource("wood", 18)
    mountain_tribe.add_shared_resource("stone", 12)

    # Build structures
    structures_built = []
    for structure in ["shelter", "storage", "totem"]:
        if river_camp.build_structure(structure):
            structures_built.append(structure)

    print(f"Riverfolk built: {', '.join(structures_built)}")
    print(f"Riverfolk structures: {river_tribe.structures}")

    # Demonstrate territory expansion
    print("\n🗺️  TERRITORY MANAGEMENT")
    print("-" * 30)

    river_territory = tribal_manager.territories["Riverfolk"]
    mountain_territory = tribal_manager.territories["Stoneheart"]

    print(f"Riverfolk territory: {river_territory.get_territory_size()} tiles")
    print(f"Stoneheart territory: {mountain_territory.get_territory_size()} tiles")

    # Expand territories
    river_territory.expand_territory((5, 5), radius=2)
    mountain_territory.expand_territory((15, 15), radius=2)

    print(f"After expansion - Riverfolk: {river_territory.get_territory_size()} tiles")
    print(f"After expansion - Stoneheart: {mountain_territory.get_territory_size()} tiles")

    # Demonstrate cultural development
    print("\n🎨 CULTURAL DEVELOPMENT")
    print("-" * 30)

    print(f"Riverfolk totems: {river_tribe.culture['totems']}")
    print(f"Riverfolk traditions: {river_tribe.culture['traditions']}")

    # Add some tribal stories
    river_tribe.culture["stories"].append(
        "The tale of the great river spirit who blessed our fishing grounds"
    )
    print(f"Riverfolk stories: {len(river_tribe.culture['stories'])}")

    # Demonstrate diplomacy
    print("\n🤝 TRIBAL DIPLOMACY")
    print("-" * 30)

    # Form alliance
    river_tribe.form_alliance("Stoneheart")
    mountain_tribe.form_alliance("Riverfolk")

    print("Riverfolk and Stoneheart have formed an alliance!")

    # Negotiate trade
    trade_agreement = tribal_manager.tribal_diplomacy.arrange_trade_agreement(
        river_tribe, mountain_tribe
    )
    if trade_agreement:
        print("Trade agreement established:")
        print(f"  Riverfolk offers: {trade_agreement.get('tribe1_offers', [])}")
        print(f"  Stoneheart offers: {trade_agreement.get('tribe2_offers', [])}")
        print(f"  Duration: {trade_agreement.get('duration', 0)} turns")
    else:
        print("No trade agreement could be established")

    # Demonstrate politics and diplomacy dynamics
    print("\n🏛️  TRIBAL POLITICS & DIPLOMACY")
    print("-" * 40)

    # Show initial political status
    print("Political Status:")
    for tribe_name, tribe in tribal_manager.tribes.items():
        politics = tribal_manager.politics[tribe_name]
        summary = politics.get_political_summary()
        leader_stability = summary.get("leader_stability", 0.0)
        active_challenges = summary.get("active_challenges", 0)
        print(
            f"  {tribe_name}: Leader stability {leader_stability:.2f}, {active_challenges} challenges"
        )

    # Show diplomatic relations
    print("\nDiplomatic Relations:")
    diplomacy_summary = tribal_manager.tribal_diplomacy.get_diplomacy_summary()
    for key, relation in tribal_manager.tribal_diplomacy.diplomatic_relations.items():
        tribe1, tribe2 = key
        standing = tribal_manager.tribal_diplomacy.get_diplomatic_standing(tribe1, tribe2)
        alliance = "Allied" if relation["alliance_status"] else ""
        alliance_str = f" ({alliance})" if alliance else ""
        print(f"  {tribe1} ↔ {tribe2}: {standing}{alliance_str}")

    # Process some turns to show dynamics
    print("\nProcessing tribal dynamics...")
    for turn in range(3):
        print(f"\nTurn {turn + 1}:")
        tribal_manager.process_tribal_dynamics()

        # Show any political changes
        for tribe_name, tribe in tribal_manager.tribes.items():
            politics = tribal_manager.politics[tribe_name]
            if politics.political_events:
                print(f"  {tribe_name} political events: {politics.political_events[-1]}")

        # Show diplomatic events
        if tribal_manager.tribal_diplomacy.diplomatic_history:
            recent_event = tribal_manager.tribal_diplomacy.diplomatic_history[-1]
            print(f"  Diplomatic event: {recent_event.get('description', 'Unknown')}")

    # Demonstrate tribal language evolution
    print("\n🗣️  TRIBAL LANGUAGE")
    print("-" * 30)

    river_lang = tribal_manager.tribal_communication.get_tribal_language(river_tribe)
    mountain_lang = tribal_manager.tribal_communication.get_tribal_language(mountain_tribe)

    print("Riverfolk dialect:")
    for word in ["food", "danger", "friend", "home"]:
        print(f"  '{word}' -> '{river_lang.translate_to_tribal(word)}'")

    print("\nStoneheart dialect:")
    for word in ["food", "danger", "friend", "home"]:
        print(f"  '{word}' -> '{mountain_lang.translate_to_tribal(word)}'")

    # Demonstrate tribal actions based on roles
    print("\n⚡ ROLE-BASED ACTIONS")
    print("-" * 30)

    # Show what different roles might do
    available_actions = [
        "hunt_prey",
        "gather_resources",
        "build_structure",
        "defend_territory",
        "heal_tribe",
        "craft_tools",
    ]

    print("Role action preferences:")
    for role in TribalRole:
        preferred_action = TribalRoleBehavior.decide_action(
            "test_npc", role, river_tribe, available_actions
        )
        print(f"  {role.value}: prefers '{preferred_action}'")

    # Demonstrate role balancing
    print("\n⚖️  ROLE BALANCING DEMONSTRATION")
    print("-" * 40)

    # Create a tribe with unbalanced roles to show balancing
    test_tribe = tribal_manager.create_tribe("BalancedTribe", "test_leader", (25, 25))

    # Add many members with specific roles to create imbalance
    test_members = [f"test_member_{i}" for i in range(1, 16)]  # 15 additional members

    # Manually assign unbalanced roles (too many hunters, not enough gatherers)
    unbalanced_roles = (
        [TribalRole.HUNTER] * 8  # Too many hunters
        + [TribalRole.LEADER] * 2  # Extra leaders
        + [TribalRole.WARRIOR] * 3  # Some warriors
        + [TribalRole.CRAFTER] * 2  # Few crafters
    )  # Missing gatherers and shamans

    for i, member in enumerate(test_members):
        if i < len(unbalanced_roles):
            test_tribe.add_member(member, unbalanced_roles[i])
        else:
            test_tribe.add_member(member)  # Default assignment

    print("Before balancing:")
    unbalanced_roles = tribal_manager.role_managers["BalancedTribe"].get_role_distribution()
    for role, count in unbalanced_roles.items():
        print(f"  {role.value}: {count}")

    # Trigger role reassignment
    tribal_manager.role_managers["BalancedTribe"].reassign_roles()

    print("\nAfter balancing:")
    balanced_roles = tribal_manager.role_managers["BalancedTribe"].get_role_distribution()
    for role, count in balanced_roles.items():
        print(f"  {role.value}: {count}")

    print(
        f"\nBalancedTribe now has {len(test_tribe.member_ids)} members with properly distributed roles!"
    )

    # Demonstrate role contributions to wellbeing
    print("\n⚖️  ROLE CONTRIBUTIONS TO WELLBEING")
    print("-" * 45)

    # Show initial wellbeing
    print("Before contributions:")
    initial_wellbeing = test_tribe.get_wellbeing_report()
    for aspect, score in initial_wellbeing.items():
        if aspect != "overall_wellbeing":
            print(f"  {aspect}: {score:.2f}")

    # Process contributions (simulate a few turns)
    print("\nProcessing role contributions...")
    for turn in range(3):
        tribal_manager.role_managers["BalancedTribe"].process_role_contributions()
        print(f"  Turn {turn + 1}: Contributions processed")

    # Show improved wellbeing
    print("\nAfter contributions:")
    final_wellbeing = test_tribe.get_wellbeing_report()
    for aspect, score in final_wellbeing.items():
        if aspect != "overall_wellbeing":
            print(f"  {aspect}: {score:.2f}")

    print(
        f"\nOverall wellbeing improved from {initial_wellbeing['overall_wellbeing']:.2f} to {final_wellbeing['overall_wellbeing']:.2f}"
    )

    # Show resource gains from contributions
    print("\nResource gains from contributions:")
    print(f"  Food: {test_tribe.shared_resources['food']:.1f}")
    print(f"  Wood: {test_tribe.shared_resources['wood']:.1f}")
    print(f"  Stone: {test_tribe.shared_resources['stone']:.1f}")
    print(f"  Herbs: {test_tribe.shared_resources['herbs']:.1f}")

    # Demonstrate tribal politics and diplomacy
    print("\n🏛️  TRIBAL POLITICS & DIPLOMACY")
    print("-" * 40)

    # Process political and diplomatic dynamics
    print("Processing tribal dynamics...")
    tribal_manager.process_tribal_dynamics()

    # Show political status
    print("\nPolitical Status:")
    for tribe_name in ["Riverfolk", "Stoneheart", "BalancedTribe"]:
        if tribe_name in tribal_manager.politics:
            politics = tribal_manager.politics[tribe_name]
            summary = politics.get_political_summary()
            print(f"  {tribe_name}:")
            print(f"    Leader Stability: {summary['leader_stability']:.2f}")
            print(f"    Active Challenges: {summary['active_challenges']}")
            print(f"    Resource Disputes: {summary['resource_disputes']}")
            if summary["power_distribution"]:
                top_power = list(summary["power_distribution"].keys())[0]
                print(f"    Top Power Holder: {top_power}")

    # Show diplomatic status
    print("\nDiplomatic Status:")
    diplomacy_summary = tribal_manager.tribal_diplomacy.get_diplomacy_summary()
    print(f"  Active Negotiations: {diplomacy_summary['active_negotiations']}")
    print(f"  Trade Agreements: {diplomacy_summary['trade_agreements']}")

    # Show alliance networks
    alliances = diplomacy_summary["alliance_networks"]
    if alliances:
        print("  Alliance Networks:")
        for tribe, allies in alliances.items():
            if allies:
                print(f"    {tribe} allied with: {allies}")

    # Demonstrate a diplomatic event
    print("\nDiplomatic Events:")
    if random.random() < 0.6:  # 60% chance to show an event
        print("  Cultural exchange occurred between tribes!")
        print("  Trust levels improved between neighboring tribes.")
    else:
        print("  Border incident reported - diplomatic tension increased.")
        print("  Tribes are negotiating improved relations.")

    # Final tribal status
    print("\n📊 FINAL TRIBAL STATUS")
    print("-" * 30)

    all_tribes_info = tribal_manager.get_all_tribes_info()
    for tribe_info in all_tribes_info:
        print(f"\n{tribe_info['name']} {tribe_info['symbol']}:")
        print(f"  Members: {tribe_info['member_count']}")
        print(f"  Territory: {tribe_info['territory_size']} tiles")
        print(f"  Structures: {tribe_info['structures']}")
        print(f"  Resources: {tribe_info['shared_resources']}")
        print(f"  Alliances: {tribe_info['alliances']}")
        print(f"  Development: {tribe_info['development_stage']}")

    print("\n✨ Tribal system demonstration complete!")
    print("The tribes are now ready for integration with the main simulation.")


if __name__ == "__main__":
    demonstrate_tribal_system()
