#!/usr/bin/env python3
"""
Demo script for testing the enhanced persistence system.
Shows save/load functionality for complete world state including weather, events, and environmental data.
"""

from persistence_manager import PersistenceManager


def demo_persistence():
    """Demonstrate the persistence system capabilities."""
    print("=== PERSISTENCE SYSTEM DEMO ===")

    pm = PersistenceManager()

    # List existing saves
    saves = pm.list_saves()
    print(f"\nExisting saves: {saves}")

    if saves:
        # Show details of the most recent save
        latest_save = saves[-1]
        print(f"\nLoading save: {latest_save}")

        save_data = pm.load_world_state(latest_save)
        if save_data:
            metadata = save_data.get("metadata", {})
            world_data = save_data.get("world", {})
            weather_data = save_data.get("weather", {})
            events_data = save_data.get("events", {})
            tribes_data = save_data.get("tribes", {})

            print(f"  Timestamp: {metadata.get('timestamp', 'Unknown')}")
            print(f"  Version: {metadata.get('version', 'Unknown')}")

            # World state details
            if world_data:
                print("\nWorld State:")
                print(f"  Day: {world_data.get('current_day', 0)}")
                print(f"  Hour: {world_data.get('current_hour', 0)}")
                print(f"  Season: {world_data.get('current_season', 0)}")
                print(f"  Active chunks: {len(world_data.get('active_chunks', {}))}")
                print(f"  Factions: {len(world_data.get('factions', {}))}")

                # NPC count
                total_npcs = 0
                for chunk_data in world_data.get("active_chunks", {}).values():
                    total_npcs += len(chunk_data.get("npcs", []))
                print(f"  Total NPCs: {total_npcs}")

            # Weather state details
            if weather_data:
                print("\nWeather State:")
                current_weather = weather_data.get("current_weather", {})
                print(f"  Weather locations: {len(current_weather)}")
                if current_weather:
                    sample_weather = list(current_weather.values())[0]
                    print(f"  Sample weather: {sample_weather}")
                print(f"  Update interval: {weather_data.get('update_interval', 'Unknown')}")

            # Events state details
            if events_data:
                print("\nEvents State:")
                active_events = events_data.get("active_events", [])
                print(f"  Active events: {len(active_events)}")
                for event in active_events[:3]:  # Show first 3 events
                    print(
                        f"    {event.get('name', 'Unknown')} at {event.get('location', 'Unknown')}"
                    )
                print(f"  Event interval: {events_data.get('event_interval', 'Unknown')}")

            # Tribal state details
            if tribes_data:
                print("\nTribal State:")
                tribes = tribes_data.get("tribes", {})
                print(f"  Tribes: {len(tribes)}")
                for tribe_name, tribe_data in list(tribes.items())[:3]:  # Show first 3 tribes
                    members = len(tribe_data.get("members", {}))
                    location = tribe_data.get("location", (0, 0))
                    print(f"    {tribe_name}: {members} members at {location}")
        else:
            print("Failed to load save data")
    else:
        print("No saves found. Run a simulation with persistence enabled first.")


if __name__ == "__main__":
    demo_persistence()
