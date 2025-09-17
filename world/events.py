import random
import logging


# === Event Blueprint System ===
class Event:
    """Base class for all world events."""

    def __init__(self, name, location, start_time, duration, area_of_effect=None, effects=None):
        self.name = name
        self.location = location  # (x, y) or region id
        self.start_time = start_time
        self.duration = duration
        self.area_of_effect = area_of_effect or [location]
        self.effects = effects or []  # List of effect dicts or callables
        self.active = True

    def is_active(self, current_time):
        return self.active and (current_time < self.start_time + self.duration)

    def end(self):
        self.active = False

    def apply_effects(self, world):
        """Apply this event's effects to the world or its inhabitants."""
        for effect in self.effects:
            if callable(effect):
                effect(world, self)
            # else: could be a dict for data-driven effects


# --- Specific Event Types ---
class WildfireEvent(Event):
    def __init__(self, location, start_time, duration=15):
        super().__init__(
            name="Wildfire",
            location=location,
            start_time=start_time,
            duration=duration,
            area_of_effect=[location],
            effects=[self.wildfire_effect],
        )

    def wildfire_effect(self, world, event):
        chunk = world.chunks.get(event.location)
        if chunk:
            chunk.resources["wood"] = chunk.resources.get("wood", 0) * 0.25
            chunk.impassable = True
            # Mark NPCs to flee (could be expanded)
            for npc in getattr(chunk, "npcs", []):
                npc.needs["safety"] = 0


class FamineEvent(Event):
    def __init__(self, location, start_time, duration=60):
        super().__init__(
            name="Famine",
            location=location,
            start_time=start_time,
            duration=duration,
            area_of_effect=[location],
            effects=[self.famine_effect],
        )

    def famine_effect(self, world, event):
        chunk = world.chunks.get(event.location)
        if chunk:
            chunk.resources["food"] = chunk.resources.get("food", 0) * 0.5
            # Mark for increased migration (could be expanded)
            for npc in getattr(chunk, "npcs", []):
                npc.needs["migration"] = npc.needs.get("migration", 0) + 0.5


class BountifulHarvestEvent(Event):
    def __init__(self, location, start_time, duration=90):
        super().__init__(
            name="Bountiful Harvest",
            location=location,
            start_time=start_time,
            duration=duration,
            area_of_effect=[location],
            effects=[self.harvest_effect],
        )

    def harvest_effect(self, world, event):
        chunk = world.chunks.get(event.location)
        if chunk and getattr(chunk, "terrain", None) and chunk.terrain.name == "PLAINS":
            chunk.resources["food"] = chunk.resources.get("food", 0) * 2.0


class PlagueEvent(Event):
    def __init__(self, location, start_time, duration=40):
        super().__init__(
            name="The Wasting Sickness",
            location=location,
            start_time=start_time,
            duration=duration,
            area_of_effect=[location],
            effects=[self.plague_effect],
        )

    def plague_effect(self, world, event):
        chunk = world.chunks.get(event.location)
        if chunk:
            for npc in getattr(chunk, "npcs", []):
                npc.needs["death_chance"] = npc.needs.get("death_chance", 0) + 0.1
                npc.needs["work_efficiency"] = npc.needs.get("work_efficiency", 1.0) * 0.75


class EventManager:
    """
    Central controller for world events. Decides when, where, and what events occur.
    """

    def __init__(self, world, event_interval=90):
        self.world = world
        self.event_interval = event_interval  # e.g., check every 90 days (once per season)
        self.logger = logging.getLogger("EventManager")
        self.active_events = []  # List of WorldEvent
        self.last_event_check = 0

    def update(self, current_time):
        """
        Check if new events should be triggered and update existing events.
        """
        from world.weather import WeatherType

        # End expired events
        for event in self.active_events:
            if not event.is_active(current_time):
                event.end()
                self.logger.info(f"Event ended: {event.name} at {event.location}")
        self.active_events = [e for e in self.active_events if e.active]

        # Only check for new events at the specified interval
        if current_time - self.last_event_check < self.event_interval:
            return
        self.last_event_check = current_time

        for chunk in self.world.chunks.values():
            # --- Environmental Triggers ---
            weather = getattr(chunk, "weather", None)
            # Track prolonged weather in chunk
            if not hasattr(chunk, "_weather_counter"):
                chunk._weather_counter = {}
            if weather:
                chunk._weather_counter[weather] = chunk._weather_counter.get(weather, 0) + 1
                # Reset counters for other weather types
                for w in list(chunk._weather_counter.keys()):
                    if w != weather:
                        chunk._weather_counter[w] = 0
            # Prolonged drought/heatwave: increase famine/wildfire chance
            famine_chance = 0.05
            wildfire_chance = 0.05
            if (
                weather == WeatherType.DROUGHT
                and chunk._weather_counter.get(WeatherType.DROUGHT, 0) >= 10
            ):
                famine_chance = 0.5
                wildfire_chance = 0.2
            if (
                weather == WeatherType.HEATWAVE
                and chunk._weather_counter.get(WeatherType.HEATWAVE, 0) >= 10
            ):
                wildfire_chance = 0.3
            # Prolonged storms: increase flood chance (if you add a FloodEvent)
            if (
                weather == WeatherType.STORM
                and chunk._weather_counter.get(WeatherType.STORM, 0) >= 7
            ):
                pass  # flood_chance = 0.3

            # --- Game State Triggers ---
            # High population: increase plague chance
            npc_count = len(getattr(chunk, "npcs", []))
            plague_chance = 0.05
            if npc_count >= 15:
                plague_chance = 0.3
            # Resource depletion: increase migration/famine chance
            food = chunk.resources.get("food", 100)
            if food < 10:
                famine_chance = max(famine_chance, 0.3)

            # --- Event Spawning ---
            # Famine
            if random.random() < famine_chance:
                event = FamineEvent(chunk.coordinates, current_time)
                self.active_events.append(event)
                self.logger.info(
                    f"[TRIGGER] Famine at {chunk.coordinates} (chance: {famine_chance})"
                )
                event.apply_effects(self.world)
            # Wildfire
            if random.random() < wildfire_chance:
                event = WildfireEvent(chunk.coordinates, current_time)
                self.active_events.append(event)
                self.logger.info(
                    f"[TRIGGER] Wildfire at {chunk.coordinates} (chance: {wildfire_chance})"
                )
                event.apply_effects(self.world)
            # Plague
            if random.random() < plague_chance:
                event = PlagueEvent(chunk.coordinates, current_time)
                self.active_events.append(event)
                self.logger.info(
                    f"[TRIGGER] Plague at {chunk.coordinates} (chance: {plague_chance})"
                )
                event.apply_effects(self.world)
            # Bountiful Harvest (example: if food is high)
            if food > 200 and random.random() < 0.1:
                event = BountifulHarvestEvent(chunk.coordinates, current_time)
                self.active_events.append(event)
                self.logger.info(f"[TRIGGER] Bountiful Harvest at {chunk.coordinates}")
                event.apply_effects(self.world)

    def get_events_for_location(self, location):
        """
        Return all active events affecting a given location.
        """
        return [e for e in self.active_events if e.location == location and e.active]
