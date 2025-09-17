import json
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime


class PersistenceManager:
    """
    Enhanced persistence system for complete world state including weather, events, and environmental data.
    """

    def __init__(self, base_path: str = "persistence"):
        self.base_path = base_path
        self.logger = logging.getLogger("PersistenceManager")

        # Create directories if they don't exist
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(os.path.join(self.base_path, "chunks"), exist_ok=True)
        os.makedirs(os.path.join(self.base_path, "weather"), exist_ok=True)
        os.makedirs(os.path.join(self.base_path, "events"), exist_ok=True)

    def save_world_state(
        self,
        world,
        weather_manager=None,
        events_manager=None,
        tribal_manager=None,
        save_name: str = "default",
    ) -> bool:
        """
        Save complete world state including all enhanced features and Markov chains.
        """
        try:
            timestamp = datetime.now().isoformat()
            save_data = {
                "metadata": {
                    "save_name": save_name,
                    "timestamp": timestamp,
                    "version": "1.0",
                },
                "world": self._serialize_world(world),
                "weather": (self._serialize_weather(weather_manager) if weather_manager else None),
                "events": (self._serialize_events(events_manager) if events_manager else None),
                "tribes": (self._serialize_tribes(tribal_manager) if tribal_manager else None),
                "markov": self._serialize_markov_chains(),
            }

            save_file = os.path.join(self.base_path, f"world_state_{save_name}.json")
            with open(save_file, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, default=str)

            self.logger.info(f"World state saved to {save_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save world state: {e}")
            return False

    def load_world_state(self, save_name: str = "default") -> Optional[Dict[str, Any]]:
        """
        Load complete world state including Markov chains.
        """
        try:
            save_file = os.path.join(self.base_path, f"world_state_{save_name}.json")
            if not os.path.exists(save_file):
                self.logger.warning(f"Save file not found: {save_file}")
                return None

            with open(save_file, "r", encoding="utf-8") as f:
                save_data = json.load(f)

            # Restore Markov chains if present
            if "markov" in save_data:
                self._deserialize_markov_chains(save_data["markov"])

            self.logger.info(f"World state loaded from {save_file}")
            return save_data

        except Exception as e:
            self.logger.error(f"Failed to load world state: {e}")
            return None

    def _serialize_world(self, world) -> Dict[str, Any]:
        """Serialize world engine state."""
        chunks_data = {}
        for coord, chunk in world.active_chunks.items():
            chunks_data[f"{coord[0]}_{coord[1]}"] = {
                "coordinates": coord,
                "terrain": (
                    chunk.terrain.name if hasattr(chunk.terrain, "name") else str(chunk.terrain)
                ),
                "resources": dict(chunk.resources),
                "npcs": [self._serialize_npc(npc) for npc in chunk.npcs],
                "weather": getattr(chunk, "weather", None),
            }

        return {
            "current_hour": world.current_hour,
            "current_day": world.current_day,
            "current_season": world.current_season,
            "total_minutes": world.total_minutes,
            "active_chunks": chunks_data,
            "factions": {
                name: self._serialize_faction(faction) for name, faction in world.factions.items()
            },
        }

    def _serialize_npc(self, npc) -> Dict[str, Any]:
        """Serialize NPC state."""
        return {
            "name": npc.name,
            "age": npc.age,
            "coordinates": npc.coordinates,
            "faction_id": npc.faction_id,
            "food": getattr(npc, "food", 100),
            "needs": getattr(npc, "needs", {}),
            "attributes": getattr(npc, "attributes", {}),
            "relationships": getattr(npc, "relationships", {}),
        }

    def _serialize_faction(self, faction) -> Dict[str, Any]:
        """Serialize faction state."""
        return {
            "name": faction.name,
            "territory": faction.territory,
            "members": list(faction.members) if hasattr(faction, "members") else [],
            "resources": getattr(faction, "resources", {}),
            "memory": getattr(faction, "memory", {}),
        }

    def _serialize_weather(self, weather_manager) -> Dict[str, Any]:
        """Serialize weather manager state."""
        if not weather_manager:
            return None

        return {
            "current_weather": {
                str(coord): weather.name if hasattr(weather, "name") else str(weather)
                for coord, weather in weather_manager.current_weather.items()
            },
            "last_update_time": weather_manager.last_update_time,
            "update_interval": weather_manager.update_interval,
        }

    def _serialize_events(self, events_manager) -> Dict[str, Any]:
        """Serialize events manager state."""
        if not events_manager:
            return None

        active_events = []
        for event in events_manager.active_events:
            if event.active:
                active_events.append(
                    {
                        "name": event.name,
                        "location": event.location,
                        "start_time": event.start_time,
                        "duration": event.duration,
                        "area_of_effect": event.area_of_effect,
                    }
                )

        return {
            "active_events": active_events,
            "last_event_check": events_manager.last_event_check,
            "event_interval": events_manager.event_interval,
        }

    def _serialize_tribes(self, tribal_manager) -> Dict[str, Any]:
        """Serialize tribal manager state."""
        if not tribal_manager:
            return None

        tribes_data = {}
        for name, tribe in tribal_manager.tribes.items():
            tribes_data[name] = {
                "name": name,
                "location": getattr(tribe, "location", (0, 0)),
                "members": getattr(tribe, "members", {}),
                "shared_resources": getattr(tribe, "shared_resources", {}),
                "priorities": getattr(tribe, "priorities", {}),
                "relations": getattr(tribe, "relations", {}),
            }

        return {
            "tribes": tribes_data,
            "diplomatic_relations": getattr(tribal_manager, "diplomatic_relations", {}),
        }

    def list_saves(self) -> list:
        """List all available save files."""
        saves = []
        for filename in os.listdir(self.base_path):
            if filename.startswith("world_state_") and filename.endswith(".json"):
                save_name = filename[12:-5]  # Remove "world_state_" and ".json"
                saves.append(save_name)
        return saves

    def delete_save(self, save_name: str) -> bool:
        """Delete a save file."""
        try:
            save_file = os.path.join(self.base_path, f"world_state_{save_name}.json")
            if os.path.exists(save_file):
                os.remove(save_file)
                self.logger.info(f"Deleted save: {save_name}")
                return True
            else:
                self.logger.warning(f"Save file not found: {save_name}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to delete save {save_name}: {e}")
            return False

    def _serialize_markov_chains(self) -> Dict[str, Any]:
        """Serialize Markov chain states for persistence."""
        try:
            from markov_behavior import global_tribal_markov

            # markov_dialogue no longer exposes MARKOV_MODELS; we snapshot strict models if built
            try:
                import markov_dialogue as md
            except Exception:
                md = None

            def serialize_chain_model(chain):
                return {
                    state: dict(actions) for state, actions in getattr(chain, "model", {}).items()
                }

            data = {
                "behavioral": {
                    "diplomatic": serialize_chain_model(global_tribal_markov.diplomatic_chain),
                    "resource": serialize_chain_model(global_tribal_markov.resource_chain),
                    "conflict": serialize_chain_model(global_tribal_markov.conflict_chain),
                    "cultural": serialize_chain_model(global_tribal_markov.cultural_chain),
                },
                "dialogue": {},
            }

            # Attempt to snapshot strict hostile/neutral internal models
            if md is not None:
                try:
                    hostile, neutral = md._build_strict_models()
                    data["dialogue"]["hostile_raw"] = (
                        hostile.to_state() if hasattr(hostile, "to_state") else {}
                    )
                    data["dialogue"]["neutral_raw"] = (
                        neutral.to_state() if hasattr(neutral, "to_state") else {}
                    )
                except Exception as e:
                    self.logger.warning(f"Dialogue strict model snapshot failed: {e}")
            return data
        except Exception as e:
            self.logger.error(f"Failed to serialize Markov chains: {e}")
            return {}

    def _deserialize_markov_chains(self, markov_data: Dict[str, Any]):
        """Restore Markov chain states from saved data."""
        try:
            from markov_behavior import global_tribal_markov
            from collections import defaultdict
            import markov_dialogue as md

            # Helper to restore defaultdict structure
            def restore_chain_model(chain, saved_model):
                chain.model = defaultdict(lambda: defaultdict(int))
                for state, actions in saved_model.items():
                    for action, count in actions.items():
                        chain.model[state][action] = count

            # Restore behavioral chains
            if "behavioral" in markov_data:
                behavioral = markov_data["behavioral"]
                if "diplomatic" in behavioral:
                    restore_chain_model(
                        global_tribal_markov.diplomatic_chain, behavioral["diplomatic"]
                    )
                if "resource" in behavioral:
                    restore_chain_model(global_tribal_markov.resource_chain, behavioral["resource"])
                if "conflict" in behavioral:
                    restore_chain_model(global_tribal_markov.conflict_chain, behavioral["conflict"])
                if "cultural" in behavioral:
                    restore_chain_model(global_tribal_markov.cultural_chain, behavioral["cultural"])

            # Restore dialogue strict models if present
            if "dialogue" in markov_data and md is not None:
                dlg = markov_data["dialogue"]
                try:
                    hostile_state = dlg.get("hostile_raw")
                    neutral_state = dlg.get("neutral_raw")
                    if hostile_state and neutral_state:
                        # rebuild via from_state for consistency
                        md._STRICT_HOSTILE_MODEL = md.NGramMarkov.from_state(hostile_state)
                        md._STRICT_NEUTRAL_MODEL = md.NGramMarkov.from_state(neutral_state)
                        md._save_strict()
                except Exception as e:
                    self.logger.warning(f"Failed to restore dialogue strict models: {e}")

            self.logger.info("Markov chains restored from saved state")

        except Exception as e:
            self.logger.error(f"Failed to restore Markov chains: {e}")

    def learn_from_interaction(
        self, interaction_type: str, context: str, action: str, outcome_success: float
    ):
        """Record interaction outcomes for Markov learning."""
        try:
            from markov_behavior import global_tribal_markov

            # Learn from the outcome
            global_tribal_markov.learn_from_outcome(
                interaction_type, context, action, outcome_success
            )

            # Log the learning event
            self.logger.debug(
                f"Markov learning: {interaction_type} context='{context}' action='{action}' success={outcome_success}"
            )

        except Exception as e:
            self.logger.error(f"Failed to record Markov learning: {e}")
