import re
import logging
import math
from dataclasses import dataclass, field, asdict
from typing import Tuple, Dict, Any, Optional, List
import random
from world.weather import WeatherType
from gemini_narrative import generate_agent_dialogue


def is_logically_sound_statement(text):
    """Basic logical soundness check for dialogue lines."""
    if not text or not isinstance(text, str):
        return False
    # Heuristic: must be at least 4 words
    if len(text.split()) < 4:
        return False
    # Heuristic: must contain a verb (very basic check)
    verbs = ["is", "are", "was", "were", "be", "have", "has", "do", "does", "did", "can", "will", "shall", "may", "must", "go", "see", "make", "know", "think", "say", "want", "need", "like", "love", "hate", "find", "get", "give", "tell", "work", "call", "try", "ask", "feel", "leave", "put", "keep", "let", "begin", "seem", "help", "talk", "turn", "start", "show", "hear", "play", "run", "move", "live", "believe", "bring", "write", "sit", "stand", "lose", "pay", "meet", "include", "continue", "set", "learn", "change", "lead", "understand", "watch", "follow", "stop", "create", "speak", "read", "allow", "add", "spend", "grow", "open", "walk", "win", "offer", "remember", "love", "consider", "appear", "buy", "wait", "serve", "die", "send", "expect", "build", "stay", "fall", "cut", "reach", "kill", "remain"]
    if not any(f" {v} " in f" {text.lower()} " for v in verbs):
        return False
    # Heuristic: avoid excessive repetition
    words = text.lower().split()
    if len(set(words)) < len(words) // 2:
        return False
    # Heuristic: must end with punctuation
    if not text.strip().endswith(('.', '!', '?')):
        return False
    return True

def improve_punctuation(text):
    """Add punctuation to dialogue: ensures ending punctuation and basic comma/period insertion."""
    if not text or not isinstance(text, str):
        return text
    # Capitalize first letter
    text = text[0].upper() + text[1:] if text else text
    # Add period if missing at end
    if not text.strip().endswith(('.', '!', '?')):
        text = text.rstrip() + '.'
    # Add commas before all conjunctions (and, but, or, so, yet) if not already present
    text = re.sub(r'\b(and|but|or|so|yet)\b', r', \1', text)
    # Add comma after introductory phrases (first 2-3 words followed by another word)
    text = re.sub(r'^(\w+\s+\w+\s+)(\w+)', r'\1, \2', text)
    # Join short sentences with conjunctions and commas (post-processing)
    # e.g., "I have food. You have water." -> "I have food, and you have water."
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) > 1:
        # Only join if both are short
        joined = []
        i = 0
        while i < len(sentences):
            s = sentences[i]
            if i < len(sentences) - 1 and len(s.split()) <= 7 and len(sentences[i+1].split()) <= 7:
                # Join with a random conjunction
                conj = random.choice([", and ", ", but ", ", or "])
                joined.append(s.rstrip('.!?') + conj + sentences[i+1][0].lower() + sentences[i+1][1:])
                i += 2
            else:
                joined.append(s)
                i += 1
        text = ' '.join(joined)
    # Ensure questions end with a question mark
    # Simple heuristic: if line starts with a question word or ends with a question word, force '?'
    question_words = [
        'who', 'what', 'when', 'where', 'why', 'how', 'is', 'are', 'do', 'does', 'did', 'can', 'could', 'will', 'would', 'should', 'shall', 'may', 'might', 'am', 'was', 'were', 'have', 'has', 'had'
    ]
    # Split into sentences for processing
    sentences = re.split(r'(?<=[.!?])\s+', text)
    new_sentences = []
    for s in sentences:
        s_strip = s.strip()
        if not s_strip:
            continue
        words = s_strip.split()
        first_word = words[0].lower() if words else ''
        # If the sentence starts with a question word, always end with '?'
        if first_word in question_words:
            s_strip = re.sub(r'[.!?]+$', '', s_strip)
            # Insert a comma after the first clause if sentence is long or has multiple verbs
            # Heuristic: insert comma after first verb if more than 6 words
            if len(words) > 6:
                # Find first verb position
                verbs = ["is", "are", "was", "were", "be", "have", "has", "do", "does", "did", "can", "will", "shall", "may", "must", "go", "see", "make", "know", "think", "say", "want", "need", "like", "love", "hate", "find", "get", "give", "tell", "work", "call", "try", "ask", "feel", "leave", "put", "keep", "let", "begin", "seem", "help", "talk", "turn", "start", "show", "hear", "play", "run", "move", "live", "believe", "bring", "write", "sit", "stand", "lose", "pay", "meet", "include", "continue", "set", "learn", "change", "lead", "understand", "watch", "follow", "stop", "create", "speak", "read", "allow", "add", "spend", "grow", "open", "walk", "win", "offer", "remember", "love", "consider", "appear", "buy", "wait", "serve", "die", "send", "expect", "build", "stay", "fall", "cut", "reach", "kill", "remain"]
                verb_idx = next((i for i, w in enumerate(words) if w.lower() in verbs), None)
                if verb_idx is not None and verb_idx < len(words) - 1:
                    # Insert comma after the first verb phrase
                    before = ' '.join(words[:verb_idx+2])
                    after = ' '.join(words[verb_idx+2:])
                    s_strip = before + (', ' + after if after else '')
            s_strip += '?'
        new_sentences.append(s_strip)
    text = ' '.join(new_sentences)
    # Remove double spaces
    text = re.sub(r'\s{2,}', ' ', text)
    return text

@dataclass
class NPC:
    """Represents a single NPC in the world."""
    name: str
    coordinates: Tuple[int, int]
    faction_id: Optional[str] = None
    health: int = 100
    age: int = 0
    skills: Dict[str, int] = field(
        default_factory=lambda: {"combat": 10, "crafting": 5, "social": 8}
    )
    needs: Dict[str, float] = field(
        default_factory=lambda: {"food": 100.0, "safety": 100.0, "rest": 100.0}
    )
    relationships: Dict[str, float] = field(default_factory=dict)
    traits: List[str] = field(default_factory=lambda: [])  # Corrected: No extra parentheses
    
    # Individual NPC Ambition System
    ambition: Optional[Dict[str, Any]] = field(default_factory=lambda: {
        "type": None,  # "leadership", "resource_hoarding", "exploration", "social_status", "alliance_building"
        "target": None,  # Specific target (NPC name, resource type, location, etc.)
        "progress": 0.0,  # Progress towards ambition (0.0 to 1.0)
        "start_tick": None,  # When ambition was adopted
        "allies": [],  # List of NPC names who are allies in pursuing this ambition
        "rivals": [],  # List of NPC names who are rivals/obstacles
        "resources_accumulated": {},  # Resources hoarded for ambition
        "influence_level": 0.0,  # Current influence within tribe (0.0 to 1.0)
    })
    
    MAX_AGE: int = 350  # Dramatically increased for much longer lifespans
    # Periodic need forcing parameters (drive action generation during stagnation)
    NEED_FORCE_INTERVAL: int = 50  # Every N world minutes apply extra decay
    NEED_FORCE_FOOD_DECAY_RANGE: Tuple[int, int] = (5, 12)
    NEED_FORCE_REST_DECAY_RANGE: Tuple[int, int] = (2, 5)
    NEED_FORCE_SAFETY_DECAY: int = 0  # Keep at 0 unless wanting migration pressure

    # Enhanced pathfinding and resource tracking
    known_resources: Dict[str, List[Tuple[Tuple[int, int], float, int]]] = field(
        default_factory=dict
    )  # resource_type -> [(coords, amount, last_seen_tick)]
    current_path: List[Tuple[int, int]] = field(default_factory=list)  # Current navigation path
    path_target: Optional[Tuple[int, int]] = None  # Final destination of current path
    resource_search_radius: int = 8  # How far to search for resources
    resource_memory_decay: int = 100  # Ticks before forgetting old resource locations

    def __post_init__(self):
        """Initialize the NPC after dataclass creation."""
        self.logger = logging.getLogger(f"NPC.{self.name}")
        self.cultural_imprint: Dict[str, Any] = {}

        # Initialize pathfinding engine - will be set during first world interaction
        self._pathfinding_engine = None
        self._world_engine = None

    def inherit_culture(self, tribe):
        """Inherit a snapshot of tribe culture at creation time (non-mutating)."""
        try:
            if hasattr(tribe, "snapshot_culture"):
                snap = tribe.snapshot_culture()
                self.cultural_imprint = snap
                self.logger.debug(
                    f"{self.name} inherited culture snapshot (values={len(snap.get('values',{}).get('principles',{}))}, rituals={len(snap.get('rituals_customs',{}).get('rituals',[]))})"
                )
        except Exception:
            pass

    def generate_ambition(self, world_context, faction_memory):
        """Generate or update an individual ambition for this NPC."""
        # Only generate ambition if NPC is mature enough (age > 50) and doesn't have one
        if self.age < 50 or self.ambition.get("type") is not None:
            return

        # Chance to develop ambition based on personality traits and circumstances
        ambition_chance = 0.1  # Base 10% chance per update
        
        # Modify chance based on traits
        if "ambitious" in self.traits:
            ambition_chance *= 2.0
        if "content" in self.traits:
            ambition_chance *= 0.3
        if "leader" in self.traits:
            ambition_chance *= 1.5
            
        # Modify chance based on current situation
        current_chunk = world_context.get("current_chunk")
        if current_chunk and len(current_chunk.npcs) > 5:
            ambition_chance *= 1.3  # More competition in larger groups
            
        if random.random() < ambition_chance:
            self._select_ambition_type(world_context, faction_memory)

    def _select_ambition_type(self, world_context, faction_memory):
        """Select an appropriate ambition type based on NPC traits and situation."""
        ambition_types = {
            "leadership": 0.2,
            "resource_hoarding": 0.25,
            "exploration": 0.15,
            "social_status": 0.2,
            "alliance_building": 0.2
        }
        
        # Modify weights based on traits
        if "leader" in self.traits:
            ambition_types["leadership"] *= 2.0
        if "crafting" in self.traits or self.skills.get("crafting", 0) > 15:
            ambition_types["resource_hoarding"] *= 1.5
        if "explorer" in self.traits or self.skills.get("social", 0) > 15:
            ambition_types["exploration"] *= 1.8
        if "diplomat" in self.traits or self.skills.get("social", 0) > 12:
            ambition_types["alliance_building"] *= 1.5
            
        # Select ambition type
        total_weight = sum(ambition_types.values())
        rand_val = random.random() * total_weight
        
        cumulative = 0
        for ambition_type, weight in ambition_types.items():
            cumulative += weight
            if rand_val <= cumulative:
                self.ambition["type"] = ambition_type
                self.ambition["start_tick"] = world_context.get("time", {}).get("total_minutes", 0)
                self._set_ambition_target(ambition_type, world_context, faction_memory)
                self.logger.info(f"NPC {self.name} developed ambition: {ambition_type} -> {self.ambition['target']}")
                break

    def _set_ambition_target(self, ambition_type, world_context, faction_memory):
        """Set a specific target for the ambition."""
        current_chunk = world_context.get("current_chunk")
        
        if ambition_type == "leadership":
            # Target could be current leader or just "become leader"
            if current_chunk and current_chunk.npcs:
                potential_leaders = [npc for npc in current_chunk.npcs if npc != self and npc.ambition.get("influence_level", 0) > 0.3]
                if potential_leaders:
                    self.ambition["target"] = random.choice(potential_leaders).name
                else:
                    self.ambition["target"] = "tribal_leader"
            else:
                self.ambition["target"] = "tribal_leader"
                
        elif ambition_type == "resource_hoarding":
            # Target a specific resource type
            resource_types = ["food", "ore", "wood", "precious_stones"]
            self.ambition["target"] = random.choice(resource_types)
            
        elif ambition_type == "exploration":
            # Target a distant location
            if current_chunk:
                # Find a distant chunk (simplified - in real implementation would use world knowledge)
                target_x = current_chunk.coordinates[0] + random.randint(-20, 20)
                target_y = current_chunk.coordinates[1] + random.randint(-20, 20)
                self.ambition["target"] = (target_x, target_y)
            else:
                self.ambition["target"] = "distant_lands"
                
        elif ambition_type == "social_status":
            # Target a specific social role or status level
            social_targets = ["elder", "shaman", "warrior_chief", "master_crafter"]
            self.ambition["target"] = random.choice(social_targets)
            
        elif ambition_type == "alliance_building":
            # Target building alliances with other NPCs
            if current_chunk and len(current_chunk.npcs) > 2:
                potential_allies = [npc for npc in current_chunk.npcs if npc != self]
                if potential_allies:
                    self.ambition["target"] = random.choice(potential_allies).name
                else:
                    self.ambition["target"] = "multiple_allies"
            else:
                self.ambition["target"] = "multiple_allies"

    def _pursue_ambition(self, world_context, faction_memory):
        """Pursue the NPC's current ambition."""
        ambition_type = self.ambition.get("type")
        target = self.ambition.get("target")
        
        if ambition_type == "leadership":
            return self._pursue_leadership_ambition(world_context, target)
        elif ambition_type == "resource_hoarding":
            return self._pursue_resource_hoarding_ambition(world_context, target)
        elif ambition_type == "exploration":
            return self._pursue_exploration_ambition(world_context, target)
        elif ambition_type == "social_status":
            return self._pursue_social_status_ambition(world_context, target)
        elif ambition_type == "alliance_building":
            return self._pursue_alliance_building_ambition(world_context, target)
            
        return None

    def _pursue_leadership_ambition(self, world_context, target):
        """Pursue leadership ambition by challenging rivals or gaining influence."""
        current_chunk = world_context.get("current_chunk")
        if not current_chunk:
            return None
            
        # If targeting a specific NPC, try to challenge or undermine them
        if isinstance(target, str) and target != "tribal_leader":
            target_npc = None
            for npc in current_chunk.npcs:
                if npc.name == target:
                    target_npc = npc
                    break
            
            if target_npc:
                # Challenge the target if they're nearby and conditions are right
                if random.random() < 0.1:  # 10% chance to attempt challenge
                    self.logger.info(f"NPC {self.name} challenging {target} for leadership!")
                    return {
                        "action": "challenge_leader",
                        "target": target,
                        "reason": "leadership_ambition"
                    }
        
        # Otherwise, work on building influence through social actions
        if random.random() < 0.3:  # 30% chance for influence-building action
            return {
                "action": "build_influence",
                "reason": "leadership_ambition"
            }
            
        return None

    def _pursue_resource_hoarding_ambition(self, world_context, target_resource):
        """Pursue resource hoarding by collecting and storing the target resource."""
        current_chunk = world_context.get("current_chunk")
        nearby_chunks = world_context.get("nearby_chunks", [])
        
        # Check if target resource is available in current chunk
        if current_chunk and current_chunk.resources.get(target_resource, 0) > 0:
            amount = min(10, current_chunk.resources[target_resource])
            self.logger.debug(f"NPC {self.name} hoarding {amount} {target_resource}")
            return {
                "action": "collect",
                "resource": target_resource,
                "amount": amount,
                "reason": "resource_hoarding"
            }
        
        # Look for target resource in nearby chunks
        for chunk in nearby_chunks:
            if chunk.resources.get(target_resource, 0) > 0:
                self.logger.debug(f"NPC {self.name} moving to hoard {target_resource} at {chunk.coordinates}")
                return {
                    "action": "move",
                    "new_coords": chunk.coordinates,
                    "reason": "resource_hoarding"
                }
        
        # If resource not found nearby, explore for it
        if nearby_chunks and random.random() < 0.2:
            target_chunk = random.choice(nearby_chunks)
            return {
                "action": "move", 
                "new_coords": target_chunk.coordinates,
                "reason": "resource_search"
            }
            
        return None

    def _pursue_exploration_ambition(self, world_context, target_location):
        """Pursue exploration ambition by moving toward target location."""
        current_chunk = world_context.get("current_chunk")
        if not current_chunk:
            return None
            
        # If target is coordinates, move toward them
        if isinstance(target_location, tuple) and len(target_location) == 2:
            target_x, target_y = target_location
            current_x, current_y = current_chunk.coordinates
            
            # Calculate direction to target
            dx = target_x - current_x
            dy = target_y - current_y
            
            # Move in the direction of the target
            if abs(dx) > abs(dy):
                new_x = current_x + (1 if dx > 0 else -1)
                new_y = current_y
            else:
                new_x = current_x
                new_y = current_y + (1 if dy > 0 else -1)
                
            # Check if target location reached
            if abs(dx) <= 1 and abs(dy) <= 1:
                self.logger.info(f"NPC {self.name} reached exploration target!")
                self.ambition["progress"] = min(1.0, self.ambition.get("progress", 0) + 0.1)
                return {
                    "action": "explore",
                    "reason": "exploration_complete"
                }
            
            return {
                "action": "move",
                "new_coords": (new_x, new_y),
                "reason": "exploration_ambition"
            }
        
        return None

    def _pursue_social_status_ambition(self, world_context, target_status):
        """Pursue social status ambition by performing status-enhancing actions."""
        # Different actions based on target status
        if target_status == "elder":
            # Elders gain status through wisdom and experience - focus on social interaction
            if random.random() < 0.4:
                return {
                    "action": "social_interaction",
                    "reason": "elder_status"
                }
        elif target_status == "shaman":
            # Shamans gain status through spiritual activities
            if random.random() < 0.3:
                return {
                    "action": "spiritual_ritual",
                    "reason": "shaman_status"
                }
        elif target_status == "warrior_chief":
            # Warrior chiefs gain status through combat and leadership
            if random.random() < 0.2:
                return {
                    "action": "demonstrate_strength",
                    "reason": "warrior_status"
                }
        elif target_status == "master_crafter":
            # Master crafters gain status through skilled work
            if random.random() < 0.3:
                return {
                    "action": "craft_item",
                    "reason": "crafter_status"
                }
                
        return None

    def _pursue_alliance_building_ambition(self, world_context, target):
        """Pursue alliance building by forming relationships with target NPCs."""
        current_chunk = world_context.get("current_chunk")
        if not current_chunk:
            return None
            
        # If targeting a specific NPC, try to interact with them
        if isinstance(target, str) and target != "multiple_allies":
            target_npc = None
            for npc in current_chunk.npcs:
                if npc.name == target:
                    target_npc = npc
                    break
            
            if target_npc and random.random() < 0.4:
                return {
                    "action": "form_alliance",
                    "target": target,
                    "reason": "alliance_building"
                }
        
        # Otherwise, engage in general social interaction to build multiple alliances
        if len(current_chunk.npcs) > 1 and random.random() < 0.3:
            return {
                "action": "social_interaction",
                "reason": "alliance_building"
            }
            
        return None

    def handle_ambition_conflicts(self, world_context):
        """Handle conflicts and interactions between ambitious NPCs in the same area."""
        current_chunk = world_context.get("current_chunk")
        if not current_chunk or len(current_chunk.npcs) < 2:
            return
            
        ambitious_npcs = [npc for npc in current_chunk.npcs if npc.ambition.get("type") is not None]
        if len(ambitious_npcs) < 2:
            return
            
        # Check for ambition conflicts between NPCs
        for i, npc1 in enumerate(ambitious_npcs):
            for npc2 in ambitious_npcs[i+1:]:
                self._resolve_ambition_conflict(npc1, npc2, world_context)

    def _resolve_ambition_conflict(self, npc1, npc2, world_context):
        """Resolve conflicts between two ambitious NPCs."""
        conflict_type = self._determine_conflict_type(npc1, npc2)
        
        if conflict_type == "rivalry":
            # Reduce relationship and potentially create hostility
            self._handle_rivalry(npc1, npc2)
        elif conflict_type == "alliance":
            # Improve relationship and create alliance
            self._handle_alliance(npc1, npc2)
        elif conflict_type == "competition":
            # Neutral competition that might lead to either rivalry or alliance
            self._handle_competition(npc1, npc2)

    def _determine_conflict_type(self, npc1, npc2):
        """Determine the type of conflict between two ambitious NPCs."""
        ambition1 = npc1.ambition.get("type")
        ambition2 = npc2.ambition.get("type")
        target1 = npc1.ambition.get("target")
        target2 = npc2.ambition.get("target")
        
        # Same ambition type often leads to rivalry
        if ambition1 == ambition2:
            # Especially if they have the same target
            if target1 == target2:
                return "rivalry"
            else:
                return "competition"
        
        # Leadership ambitions often conflict
        if ambition1 == "leadership" or ambition2 == "leadership":
            return "rivalry"
            
        # Resource hoarding vs leadership can conflict
        if ((ambition1 == "resource_hoarding" and ambition2 == "leadership") or
            (ambition1 == "leadership" and ambition2 == "resource_hoarding")):
            return "competition"
            
        # Alliance building ambitions can lead to alliances
        if ambition1 == "alliance_building" or ambition2 == "alliance_building":
            return "alliance"
            
        # Social status ambitions might compete or ally
        if ambition1 == "social_status" and ambition2 == "social_status":
            return "competition"
            
        return "neutral"

    def _handle_rivalry(self, npc1, npc2):
        """Handle rivalry between two NPCs."""
        # Reduce relationship scores
        npc1.relationships[npc2.name] = npc1.relationships.get(npc2.name, 0) - 5
        npc2.relationships[npc1.name] = npc2.relationships.get(npc1.name, 0) - 5
        
        # Add to rivals list if not already there
        if npc2.name not in npc1.ambition.get("rivals", []):
            npc1.ambition.setdefault("rivals", []).append(npc2.name)
        if npc1.name not in npc2.ambition.get("rivals", []):
            npc2.ambition.setdefault("rivals", []).append(npc1.name)
            
        # Chance for betrayal or sabotage
        if random.random() < 0.05:  # 5% chance
            betrayer = random.choice([npc1, npc2])
            target = npc2 if betrayer == npc1 else npc1
            betrayer.logger.info(f"NPC {betrayer.name} betrays {target.name} due to rivalry!")
            
            # Severe relationship damage
            betrayer.relationships[target.name] = -50
            target.relationships[betrayer.name] = -50

    def _handle_alliance(self, npc1, npc2):
        """Handle alliance formation between two NPCs."""
        # Improve relationship scores
        npc1.relationships[npc2.name] = min(100, npc1.relationships.get(npc2.name, 0) + 10)
        npc2.relationships[npc1.name] = min(100, npc2.relationships.get(npc1.name, 0) + 10)
        
        # Add to allies list if not already there
        if npc2.name not in npc1.ambition.get("allies", []):
            npc1.ambition.setdefault("allies", []).append(npc2.name)
        if npc1.name not in npc2.ambition.get("allies", []):
            npc2.ambition.setdefault("allies", []).append(npc1.name)
            
        # Chance for cooperative action
        if random.random() < 0.1:  # 10% chance
            npc1.logger.info(f"NPC {npc1.name} and {npc2.name} form alliance!")
            
            # Boost influence for both
            npc1.ambition["influence_level"] = min(1.0, npc1.ambition.get("influence_level", 0) + 0.05)
            npc2.ambition["influence_level"] = min(1.0, npc2.ambition.get("influence_level", 0) + 0.05)

    def _handle_competition(self, npc1, npc2):
        """Handle competitive relationship between two NPCs."""
        # Slight relationship reduction but not as severe as rivalry
        npc1.relationships[npc2.name] = npc1.relationships.get(npc2.name, 0) - 2
        npc2.relationships[npc1.name] = npc2.relationships.get(npc1.name, 0) - 2
        
        # Competition can lead to either alliance or rivalry over time
        if random.random() < 0.3:  # 30% chance to evolve
            if random.random() < 0.5:
                self._handle_alliance(npc1, npc2)
            else:
                self._handle_rivalry(npc1, npc2)

    def update_ambition_progress(self, world_context):
        """Update ambition progress based on actions and circumstances."""
        if not self.ambition.get("type"):
            return
            
        ambition_type = self.ambition["type"]
        progress = self.ambition.get("progress", 0)
        
        # Base progress increase
        progress_increment = 0.01  # Small base progress
        
        # Progress based on influence level
        influence_boost = self.ambition.get("influence_level", 0) * 0.02
        progress_increment += influence_boost
        
        # Ambition-specific progress
        if ambition_type == "leadership":
            # Leadership progress based on influence and allies
            allies_count = len(self.ambition.get("allies", []))
            progress_increment += allies_count * 0.005
        elif ambition_type == "resource_hoarding":
            # Resource hoarding progress based on accumulated resources
            total_resources = sum(self.ambition.get("resources_accumulated", {}).values())
            progress_increment += total_resources * 0.001
        elif ambition_type == "social_status":
            # Social status progress based on skills and influence
            skill_boost = (self.skills.get("social", 0) + self.skills.get("combat", 0)) / 200.0
            progress_increment += skill_boost
        elif ambition_type == "alliance_building":
            # Alliance building progress based on number of allies
            allies_count = len(self.ambition.get("allies", []))
            progress_increment += allies_count * 0.01
            
        # Update progress
        self.ambition["progress"] = min(1.0, progress + progress_increment)
        
        # Check for ambition completion
        if self.ambition["progress"] >= 1.0:
            self._complete_ambition(world_context)

    def _complete_ambition(self, world_context):
        """Handle ambition completion."""
        ambition_type = self.ambition["type"]
        self.logger.info(f"NPC {self.name} completed ambition: {ambition_type}!")
        
        # Grant benefits based on ambition type
        if ambition_type == "leadership":
            self.ambition["influence_level"] = 1.0
            # Add leadership trait
            if "leader" not in self.traits:
                self.traits.append("leader")
        elif ambition_type == "resource_hoarding":
            # Boost resource-related skills
            self.skills["crafting"] = min(100, self.skills.get("crafting", 0) + 20)
        elif ambition_type == "social_status":
            # Boost social skills
            self.skills["social"] = min(100, self.skills.get("social", 0) + 15)
        elif ambition_type == "alliance_building":
            # Boost influence
            self.ambition["influence_level"] = min(1.0, self.ambition.get("influence_level", 0) + 0.3)
            
        # Chance to develop new ambition
        if random.random() < 0.7:  # 70% chance for new ambition
            self.ambition = {
                "type": None,
                "target": None,
                "progress": 0.0,
                "start_tick": world_context.get("time", {}).get("total_minutes", 0),
                "allies": self.ambition.get("allies", []),
                "rivals": self.ambition.get("rivals", []),
                "resources_accumulated": self.ambition.get("resources_accumulated", {}),
                "influence_level": self.ambition.get("influence_level", 0),
            }

    def to_dict(self):
        """Convert NPC to dictionary for serialization."""
        data = asdict(self)
        # Remove non-serializable pathfinding engine references
        data.pop("_pathfinding_engine", None)
        data.pop("_world_engine", None)
        return data

    def serialize(self) -> Dict[str, Any]:
        """Convert NPC to lightweight dictionary for web API visualization."""
        return {
            "id": id(self),  # Use object ID for unique identification
            "name": self.name,
            "coordinates": self.coordinates,
            "faction_id": self.faction_id,
            "health": self.health,
            "age": self.age,
            "ambition_type": self.ambition.get("type"),
            "ambition_progress": self.ambition.get("progress", 0.0),
            "traits": self.traits,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NPC":
        """Create NPC from dictionary, handling backward compatibility."""
        # Handle backward compatibility for new fields
        if "known_resources" not in data:
            data["known_resources"] = {}
        if "current_path" not in data:
            data["current_path"] = []
        if "path_target" not in data:
            data["path_target"] = None
        if "resource_search_radius" not in data:
            data["resource_search_radius"] = 8
        if "resource_memory_decay" not in data:
            data["resource_memory_decay"] = 100
        if "ambition" not in data:
            data["ambition"] = {
                "type": None,
                "target": None,
                "progress": 0.0,
                "start_tick": None,
                "allies": [],
                "rivals": [],
                "resources_accumulated": {},
                "influence_level": 0.0,
            }

        return cls(**data)

    def _calculate_mortality_probability(self, world_context):
        """Calculate the probability of death based on age and health."""
        # Simple mortality: certain death at MAX_AGE, gradual increase before that
        if self.age >= self.MAX_AGE:
            return 1.0  # Certain death at max age
        # Health-based death
        if self.health <= 0:
            return 1.0  # Certain death at zero health
        # Age-based mortality curve (starts late, very gradual increase)
        # Now starts at 250, over 20 year span, max 2% chance near max age
        age_factor = max(0, self.age - 250) / 20.0
        base_mortality = age_factor * 0.02  # Max 2% chance near max age
        # Health modifier (also reduced)
        if self.health < 30:  # Only below 30 health
            health_factor = (30 - self.health) / 30.0  # 0 to 1
            base_mortality += health_factor * 0.02  # Up to 2% additional
        # Apply population wave multiplier for mortality
        try:
            if hasattr(world_context, "calculate_mortality_wave_multiplier") and getattr(
                world_context, "wave_enabled", False
            ):
                mortality_wave_mult = world_context.calculate_mortality_wave_multiplier()
                base_mortality *= mortality_wave_mult
        except Exception:
            pass
        return min(base_mortality, 0.05)  # Cap at 5% per tick (reduced from 15%)

    def _check_mortality(self, world_context):
        """Check if NPC should die due to age or health."""
        # Mortality is now enabled by default
        # if not os.environ.get('SANDBOX_ALLOW_MORTALITY'):
        #     return False

        # Check for certain death conditions
        if self.age >= self.MAX_AGE:
            self.logger.info(f"NPC {self.name} died of old age at {self.age}")
            return True

        if self.health <= 0:
            self.logger.info(f"NPC {self.name} died due to poor health")
            return True

        # Check probabilistic death
        p_death = self._calculate_mortality_probability(world_context)
        if random.random() < p_death:
            self.logger.info(f"NPC {self.name} died (prob={p_death:.3f}, age={self.age})")
            return True

        return False

    def update(self, world_context, faction_memory):
        """Update NPC state and decide on an action to take."""
        # ===== DEBUG: Log NPC state =====
        if self.age % 10 == 0:  # Only log every 10 ticks to reduce logging
            self.logger.debug(
                f"NPC {self.name} update - Health: {self.health}, Age: {self.age}, Needs: {self.needs}"
            )
            self.logger.debug(
                f"NPC {self.name} - Coordinates: {self.coordinates}, Faction: {self.faction_id}"
            )

        # Age the NPC
        self.age += 1

        # Generate ambition if appropriate
        self.generate_ambition(world_context, faction_memory)

        # Handle ambition conflicts with other NPCs
        self.handle_ambition_conflicts(world_context)

        # Update ambition progress
        self.update_ambition_progress(world_context)

        # Check mortality (simplified)
        if self._check_mortality(world_context):
            return {
                "action": "die",
                "reason": "old age" if self.age > self.MAX_AGE else "poor health",
            }

        # Starvation failsafe: if only 1 NPC remains, prevent starvation death and refill food
        world = world_context.get("world") if isinstance(world_context, dict) else None
        if world:
            total_npcs = sum(len(ch.npcs) for ch in getattr(world, "active_chunks", {}).values())
            if total_npcs == 1:
                # Refill food in current chunk
                current_chunk = world_context.get("current_chunk")
                if current_chunk:
                    current_chunk.resources["food"] = max(
                        current_chunk.resources.get("food", 0), 10
                    )
                # Prevent death by starvation
                if self.needs.get("food", 100) < 5:
                    self.needs["food"] = 20

        # ===== DEBUG: Log needs after update =====
        if self.age % 10 == 0:
            self.logger.debug(f"NPC {self.name} needs after update: {self.needs}")

        # Get current chunk
        current_chunk = world_context.get("current_chunk")
        if not current_chunk:
            self.logger.debug(f"NPC {self.name} has no current chunk")
            return None

        # ===== DEBUG: Log chunk info =====
        if self.age % 10 == 0:
            self.logger.debug(
                f"NPC {self.name} current chunk: {current_chunk.coordinates}, NPCs: {len(current_chunk.npcs)}"
            )

        # Decide on action based on needs and context
        action = self._decide_action(world_context, faction_memory)

        # ===== DEBUG: Log decided action =====
        if self.age % 10 == 0:
            self.logger.debug(f"NPC {self.name} decided action: {action}")

        return action

    def _decide_action(self, world_context, faction_memory):
        """Decide what action the NPC should take based on needs and context."""
        # ===== DEBUG: Log decision process =====
        if self.age % 10 == 0:
            self.logger.debug(f"NPC {self.name} deciding action - Needs: {self.needs}")

        # ===== SEASONAL AND TIME AWARENESS =====
        time_info = world_context.get("time", {})
        current_hour = time_info.get("hour", 12)  # Default to noon if no time info
        current_season = time_info.get("season", 0)  # 0=Spring, 1=Summer, 2=Autumn, 3=Winter
        season_name = time_info.get("season_name", "Spring")

        # Define seasonal characteristics for decision making
        is_winter = current_season == 3  # Harsh survival conditions
        is_autumn = current_season == 2  # Preparation for winter
        is_spring = current_season == 0  # Growth and expansion
        is_summer = current_season == 1  # Abundant resources

        # Define time periods
        is_night = current_hour >= 22 or current_hour <= 5  # 10 PM to 5 AM
        is_dawn = 6 <= current_hour <= 8  # 6 AM to 8 AM
        is_dusk = 18 <= current_hour <= 21  # 6 PM to 9 PM
        is_day = 9 <= current_hour <= 17  # 9 AM to 5 PM

        # ===== PREDATOR SWITCHING CHECK =====
        # Check if this NPC should switch to predator faction
        predator_switch = self._check_predator_switch(world_context, faction_memory)
        if predator_switch:
            return predator_switch

        # ===== PREDATOR BEHAVIOR =====
        # If this NPC is a predator, use different decision logic
        if self.faction_id == "Predator":
            return self._decide_predator_action(world_context, faction_memory)

        # ===== WEATHER & EVENT-AWARE BEHAVIOR =====
        current_chunk = world_context.get("current_chunk")
        current_weather = (
            getattr(current_chunk, "weather", WeatherType.CLEAR)
            if current_chunk
            else WeatherType.CLEAR
        )

        # Event awareness: check for active events in this chunk
        event_manager = world_context.get("event_manager")
        active_events = []
        if event_manager and current_chunk:
            active_events = event_manager.get_events_for_location(current_chunk.coordinates)

        # Flee if wildfire or flood event is active
        for event in active_events:
            if event.name in ["Wildfire", "Flood"]:
                self.logger.debug(
                    f"NPC {self.name} fleeing {event.name} at {current_chunk.coordinates}"
                )
                # Try to move to a safe adjacent chunk
                nearby_chunks = world_context.get("nearby_chunks", [])
                safe_chunks = [c for c in nearby_chunks if not getattr(c, "impassable", False)]
                if safe_chunks:
                    target = random.choice(safe_chunks)
                    return {
                        "action": "move",
                        "new_coords": target.coordinates,
                        "reason": f"flee_{event.name.lower()}",
                    }
                else:
                    return self._seek_safety_action(world_context)

        # Famine: prioritize food
        for event in active_events:
            if event.name == "Famine":
                self.logger.debug(
                    f"NPC {self.name} in Famine at {current_chunk.coordinates}: food priority increased!"
                )
                if self.needs.get("food", 100) < 90:
                    food_action = self._seek_food_action(world_context, season_modifier=0.3)
                    if food_action:
                        return food_action
                # Conserve food (rest if not hungry)
                if self.needs.get("food", 100) > 80:
                    return {"action": "rest", "reason": "famine_conservation"}

        # Plague: consider migration or avoid social contact
        for event in active_events:
            if event.name == "The Wasting Sickness":
                self.logger.debug(
                    f"NPC {self.name} in Plague at {current_chunk.coordinates}: migration/avoidance!"
                )
                # 50% chance to try to migrate
                if random.random() < 0.5:
                    nearby_chunks = world_context.get("nearby_chunks", [])
                    safe_chunks = [c for c in nearby_chunks if not getattr(c, "impassable", False)]
                    if safe_chunks:
                        target = random.choice(safe_chunks)
                        return {
                            "action": "move",
                            "new_coords": target.coordinates,
                            "reason": "flee_plague",
                        }

        # If severe weather, override priorities
        if current_weather in [WeatherType.BLIZZARD, WeatherType.STORM]:
            # Throttle repetitive per-NPC shelter logs: only log once per cooldown window per weather type
            if not hasattr(self, "_last_shelter_log"):  # {weather_type: tick}
                self._last_shelter_log = {}
            global_tick = world_context.get("time", {}).get("total_minutes", 0)
            last_tick = self._last_shelter_log.get(current_weather.name, -9999)
            shelter_log_cooldown = 120  # minutes between logs per NPC per weather type
            if global_tick - last_tick >= shelter_log_cooldown:
                self.logger.debug(
                    f"NPC {self.name} seeking shelter due to {current_weather.name} (cooldown {shelter_log_cooldown}m)"
                )
                self._last_shelter_log[current_weather.name] = global_tick
            # Aggregate world-level counter if engine reference given (attach via world_context['world'])
            world_ref = world_context.get("world")
            try:
                if world_ref is not None:
                    if not hasattr(world_ref, "_shelter_events_tick"):
                        world_ref._shelter_events_tick = 0
                    world_ref._shelter_events_tick += 1
            except Exception:
                pass
            # Only seek safety during storms if current safety is actually low
            if self.needs.get("safety", 100) < 80:  # Higher threshold for storms
                return self._seek_safety_action(world_context)
        if current_weather in [WeatherType.HEATWAVE, WeatherType.DROUGHT]:
            # If thirst is modeled, prioritize water; otherwise, seek shade/safety
            if self.needs.get("thirst", 100) < 60:
                return {"action": "seek_water", "reason": current_weather.name.lower()}
            # Only seek safety during extreme heat if safety is actually compromised
            if self.needs.get("safety", 100) < 70:  # Moderate threshold for heat
                return self._seek_safety_action(world_context)
        if current_weather == WeatherType.SNOW:
            # Move cautiously, avoid long travel
            if self.needs.get("safety", 100) < 60:
                return self._seek_safety_action(world_context)

        # ===== SEASONAL SURVIVAL PRIORITIES =====
        # Winter: Focus heavily on survival, conserve energy, avoid risky behavior
        if is_winter:
            self.logger.debug(f"NPC {self.name} applying winter survival priorities")
            # In winter, safety and food are critical - lower thresholds for action
            if self.needs.get("food", 100) < 70:  # Winter food urgency higher
                food_action = self._seek_food_action(
                    world_context, season_modifier=0.5
                )  # Harder to find food
                if food_action:
                    return food_action
            if self.needs.get("safety", 100) < 60:  # Winter safety more critical
                return self._seek_safety_action(world_context)
            # Prefer staying put in winter - less exploration
            if self.needs.get("rest", 100) < 40:
                return {"action": "rest", "reason": "winter_conservation"}

        # Autumn: Prepare for winter, gather and store resources
        elif is_autumn:
            self.logger.debug(f"NPC {self.name} applying autumn preparation priorities")
            # Autumn focus on resource gathering before winter
            if self.needs.get("food", 100) < 80:  # Gather more food in autumn
                food_action = self._seek_food_action(
                    world_context, season_modifier=1.2
                )  # Autumn harvest bonus
                if food_action:
                    return food_action

        # Spring: Expansion, exploration, renewal
        elif is_spring:
            self.logger.debug(f"NPC {self.name} applying spring expansion priorities")
            # Spring encourages exploration and social activities
            if (
                self.needs.get("food", 100) > 40
                and self.needs.get("safety", 100) > 40
                and self.needs.get("rest", 100) > 30
            ):
                # Good conditions for spring exploration
                spring_exploration = self._spring_exploration_action(world_context)
                if spring_exploration:
                    return spring_exploration

        # Summer: Peak activity, resource abundance
        elif is_summer:
            self.logger.debug(f"NPC {self.name} applying summer abundance priorities")
            # Summer allows for more social interaction and territory expansion
            if (
                self.needs.get("food", 100) > 30  # Food is more abundant in summer
                and self.needs.get("safety", 100) > 30
            ):
                social_action = self._seek_social_action(world_context)
                if social_action:
                    return social_action

        # ===== TIME-BASED BEHAVIOR WITH SEASONAL MODIFIERS =====
        # Time-based behavioral priorities adjusted for season
        if is_night:
            # Night behavior: prioritize rest and safety, reduce activity
            self.logger.debug(
                f"NPC {self.name} applying night behavior (hour {current_hour}, {season_name})"
            )

            # Winter nights are more dangerous - higher safety threshold
            safety_threshold = 80 if is_winter else 70
            if self.needs.get("safety", 100) < safety_threshold:
                return self._seek_safety_action(world_context)

            # Rest is highly prioritized at night, especially in winter
            rest_threshold = 70 if is_winter else 60
            if self.needs.get("rest", 100) < rest_threshold:
                self.logger.debug(
                    f"NPC {self.name} resting during {season_name} night (rest: {self.needs.get('rest', 100)})"
                )
                return {"action": "rest", "reason": f"{season_name.lower()}_night_rest"}

            # Only move for critical needs during night - more critical in winter
            food_threshold = 25 if is_winter else 15
            if self.needs.get("food", 100) < food_threshold:
                food_action = self._seek_food_action(
                    world_context, season_modifier=0.7 if is_winter else 1.0
                )
                if food_action:
                    return food_action

            # Default night action is rest
            self.logger.debug(f"NPC {self.name} resting during {season_name} night")
            return {"action": "rest", "reason": f"{season_name.lower()}_night_time"}

        elif is_dawn:
            # Dawn behavior: begin daily activities, patrol territory
            self.logger.debug(
                f"NPC {self.name} applying dawn behavior (hour {current_hour}, {season_name})"
            )

            # Seasonal dawn activities
            rest_threshold = 70 if is_winter else 60
            food_threshold = 60 if is_winter else 50
            safety_threshold = 60 if is_winter else 50

            if (
                self.needs.get("rest", 100) > rest_threshold
                and self.needs.get("food", 100) > food_threshold
                and self.needs.get("safety", 100) > safety_threshold
            ):
                # Good conditions for morning activities - adjusted by season
                if is_spring or is_summer:
                    # Spring/summer: active patrol and exploration
                    return self._patrol_action(world_context)
                else:
                    # Autumn/winter: cautious resource check
                    return self._cautious_resource_check(world_context)

        elif is_day:
            # Day behavior: prioritize resource gathering and exploration
            self.logger.debug(
                f"NPC {self.name} applying day behavior (hour {current_hour}, {season_name})"
            )

            # Seasonal rest requirements
            rest_threshold = 40 if is_winter else 30
            if self.needs.get("rest", 100) < rest_threshold:
                self.logger.debug(
                    f"NPC {self.name} too tired for {season_name} day activities (rest: {self.needs.get('rest', 100)})"
                )
                return {"action": "rest", "reason": f"{season_name.lower()}_exhausted"}

            # Enhanced seasonal resource gathering
            food_threshold = 70 if is_winter else (80 if is_autumn else 60)
            if self.needs.get("food", 100) < food_threshold:
                season_modifier = 0.6 if is_winter else (1.3 if is_summer else 1.0)
                food_action = self._seek_food_action(world_context, season_modifier=season_modifier)
                if food_action:
                    return food_action

        elif is_dusk:
            # Dusk behavior: return to safe areas, social activities
            self.logger.debug(
                f"NPC {self.name} applying dusk behavior (hour {current_hour}, {season_name})"
            )

            # Seasonal dusk behavior - winter requires earlier preparation
            rest_threshold = 50 if is_winter else 40
            if self.needs.get("rest", 100) > rest_threshold and not is_winter:
                # Social interaction reduced in winter
                social_action = self._seek_social_action(world_context)
                if social_action:
                    return social_action
            elif is_winter:
                # Winter dusk: prepare for harsh night
                return self._prepare_for_winter_night(world_context)

        # Get current chunk and nearby chunks
        current_chunk = world_context.get("current_chunk")
        nearby_chunks = world_context.get("nearby_chunks", [])

        # ===== DEBUG: Log nearby chunks =====
        if self.age % 10 == 0:
            self.logger.debug(
                f"NPC {self.name} nearby chunks: {[chunk.coordinates for chunk in nearby_chunks]}"
            )

        # Priority 1: Safety - if health is low, try to find safer location
        if self.needs.get("safety", 100) < 30:
            self.logger.debug(f"NPC {self.name} prioritizing safety")
            # Look for safer chunk
            for chunk in nearby_chunks:
                if self._is_chunk_safer(chunk, current_chunk):
                    self.logger.debug(f"NPC {self.name} moving to safer chunk {chunk.coordinates}")
                    return {"action": "move", "new_coords": chunk.coordinates}

        # ===== AMBITION-DRIVEN BEHAVIOR =====
        # If survival needs are met and NPC has an ambition, pursue it
        if (self.ambition.get("type") is not None and
            self.needs.get("food", 100) > 50 and
            self.needs.get("safety", 100) > 50 and
            self.needs.get("rest", 100) > 40):
            
            ambition_action = self._pursue_ambition(world_context, faction_memory)
            if ambition_action:
                self.logger.debug(f"NPC {self.name} pursuing ambition: {self.ambition['type']}")
                return ambition_action

        # Priority 2: Enhanced Resource Collection - use improved pathfinding and prioritization
        resource_action = self._seek_any_resource_action(
            world_context, self._get_faction_resource_priorities()
        )
        if resource_action:
            return resource_action

        # Legacy food seeking for compatibility (fallback)
        food_here = current_chunk.resources.get("food", 0)
        if food_here > 0:
            self.logger.debug(
                f"NPC {self.name} collecting food from current chunk (legacy fallback)"
            )
            return {
                "action": "collect",
                "resource": "food",
                "amount": min(25, food_here),
            }
        # Look for food-rich chunk in nearby areas
        for chunk in nearby_chunks:
            if chunk.resources.get("food", 0) > 0:
                self.logger.debug(
                    f"NPC {self.name} moving to food-rich chunk {chunk.coordinates} (legacy fallback)"
                )
                return {"action": "move", "new_coords": chunk.coordinates}
        # Fallback: wander to discover resources if stuck
        if nearby_chunks:
            target = random.choice(nearby_chunks)
            self.logger.debug(
                f"NPC {self.name} wandering to {target.coordinates} (resource discovery)"
            )
            return {
                "action": "move",
                "new_coords": target.coordinates,
                "reason": "resource_discovery",
            }

        # Priority 3: Social interaction - if not too urgent needs
        if current_chunk and (
            self.needs.get("food", 100) > 50
            and self.needs.get("safety", 100) > 50
            and len(current_chunk.npcs) > 1
        ):
            self.logger.debug(f"NPC {self.name} considering social interaction")
            # Find another NPC in the same chunk
            for npc in current_chunk.npcs:
                if npc != self and npc.faction_id == self.faction_id:
                    self.logger.debug(f"NPC {self.name} socializing with {npc.name}")
                    return {"action": "socialize", "target_npc_name": npc.name}

        # Priority 4: Exploration - move to nearby chunk if conditions are good
        if (
            self.needs.get("food", 100) > 60
            and self.needs.get("safety", 100) > 60
            and nearby_chunks
        ):
            self.logger.debug(f"NPC {self.name} exploring")
            target_chunk = random.choice(nearby_chunks)
            self.logger.debug(f"NPC {self.name} moving to explore {target_chunk.coordinates}")
            return {"action": "move", "new_coords": target_chunk.coordinates}

        # Diversity bypass: small chance to perform low-priority social/explore even if above conditions already failed
        if (
            nearby_chunks
            and current_chunk
            and self.needs.get("food", 100) > 45
            and self.needs.get("safety", 100) > 45
        ):
            if random.random() < 0.03:  # 3% chance per tick when stable
                # Prefer social if a partner exists; else exploration
                partner = None
                for npc in current_chunk.npcs:
                    if npc != self and npc.faction_id == self.faction_id:
                        partner = npc
                        break
                if partner:
                    self.logger.debug(
                        f"NPC {self.name} diversity bypass social with {partner.name}"
                    )
                    return {
                        "action": "socialize",
                        "target_npc_name": partner.name,
                        "reason": "diversity_bypass",
                    }
                else:
                    target_chunk = random.choice(nearby_chunks)
                    self.logger.debug(
                        f"NPC {self.name} diversity bypass exploring {target_chunk.coordinates}"
                    )
                    return {
                        "action": "move",
                        "new_coords": target_chunk.coordinates,
                        "reason": "diversity_bypass",
                    }

        # No action needed
        self.logger.debug(f"NPC {self.name} no action needed")
        return None

    def _seek_safety_action(self, world_context):
        """Find a safer location when safety is prioritized."""
        current_chunk = world_context.get("current_chunk")
        nearby_chunks = world_context.get("nearby_chunks", [])

        # Look for safer chunk
        for chunk in nearby_chunks:
            if self._is_chunk_safer(chunk, current_chunk):
                self.logger.debug(f"NPC {self.name} moving to safer chunk {chunk.coordinates}")
                return {"action": "move", "new_coords": chunk.coordinates}

        # If no safer chunk, try to stay put
        return {"action": "rest", "reason": "seeking_safety"}

    def _seek_food_action(self, world_context, season_modifier=1.0):
        """Find food when hungry, using enhanced pathfinding and resource detection."""
        current_chunk = world_context.get("current_chunk")
        nearby_chunks = world_context.get("nearby_chunks", [])

        # Initialize pathfinding engine if needed
        if self._pathfinding_engine is None:
            self._initialize_pathfinding(world_context)

        # Seasonal food availability modifier affects thresholds
        food_threshold = max(3, int(5 * season_modifier))
        food_rich_threshold = max(5, int(10 * season_modifier))

        # Try to collect food from current chunk
        current_food = current_chunk.resources.get("food", 0)
        if current_food > food_threshold:
            amount = min(10, current_food)
            # Apply seasonal efficiency
            actual_amount = max(1, int(amount * season_modifier))

            # Update resource memory
            self._update_resource_memory("food", self.coordinates, current_food, world_context)

            self.logger.debug(
                f"NPC {self.name} collecting {actual_amount} food from current chunk (seasonal modifier: {season_modifier})"
            )
            return {"action": "collect", "resource": "food", "amount": actual_amount}

        # If continuing on a path to a resource, keep following it
        if self.current_path and self.path_target:
            next_step = self.current_path[0]
            if next_step == self.coordinates:
                # We've reached this step, remove it and continue
                self.current_path.pop(0)
                if self.current_path:
                    next_step = self.current_path[0]
                else:
                    # Reached the target
                    self.path_target = None
                    # Try to collect at target location
                    target_chunk = self._get_chunk_at(self.coordinates, world_context)
                    if target_chunk and target_chunk.resources.get("food", 0) > 0:
                        return self._seek_food_action(world_context, season_modifier)

            if self.current_path:
                self.logger.debug(f"NPC {self.name} continuing on food path to {next_step}")
                return {
                    "action": "move",
                    "new_coords": next_step,
                    "reason": "following_food_path",
                }

        # Search for food using enhanced pathfinding
        best_food_location = self._find_best_resource_location(
            "food", world_context, season_modifier
        )

        if best_food_location:
            coords, amount, distance = best_food_location

            # If it's adjacent, move directly
            if distance <= 1.5:  # Adjacent or diagonal
                self.logger.debug(f"NPC {self.name} moving to adjacent food-rich chunk {coords}")
                return {"action": "move", "new_coords": coords}

            # Plan a path for distant resources
            if self._pathfinding_engine:
                path = self._pathfinding_engine.a_star_pathfind(
                    self.coordinates, coords, max_distance=self.resource_search_radius
                )

                if path and len(path) > 1:
                    self.current_path = path[1:]  # Exclude current position
                    self.path_target = coords
                    next_step = path[1]

                    self.logger.debug(
                        f"NPC {self.name} starting path to distant food at {coords} (distance: {distance:.1f})"
                    )
                    return {
                        "action": "move",
                        "new_coords": next_step,
                        "reason": "pathfind_to_food",
                    }

        # Fallback to old behavior: check immediate neighbors
        for chunk in nearby_chunks:
            if chunk.resources.get("food", 0) > food_rich_threshold:
                self.logger.debug(
                    f"NPC {self.name} moving to nearby food-rich chunk {chunk.coordinates} (fallback)"
                )
                return {"action": "move", "new_coords": chunk.coordinates}

        # Last resort: explore to find new resources
        if self._pathfinding_engine:
            exploration_target = self._find_exploration_target(world_context)
            if exploration_target:
                self.logger.debug(
                    f"NPC {self.name} exploring for food resources to {exploration_target}"
                )
                return {
                    "action": "move",
                    "new_coords": exploration_target,
                    "reason": "food_exploration",
                }

        return None

    def _seek_social_action(self, world_context):
        """Engage in social activities when conditions are good."""
        current_chunk = world_context.get("current_chunk")

        if (
            self.needs.get("food", 100) > 50
            and self.needs.get("safety", 100) > 50
            and len(current_chunk.npcs) > 1
        ):

            # Find another NPC in the same chunk
            for npc in current_chunk.npcs:
                if npc != self and npc.faction_id == self.faction_id:
                    # Share resource knowledge during social interaction
                    if (
                        hasattr(npc, "known_resources") and random.random() < 0.3
                    ):  # 30% chance to share
                        for resource_type in [
                            "food",
                            "wood",
                            "stone",
                        ]:  # Common resources
                            if resource_type in self.known_resources:
                                self._share_resource_knowledge(npc, resource_type)

                    self.logger.debug(f"NPC {self.name} socializing with {npc.name}")
                    return {"action": "socialize", "target_npc_name": npc.name}

        return None

    def _patrol_action(self, world_context):
        """Patrol territory during dawn hours."""
        nearby_chunks = world_context.get("nearby_chunks", [])

        if nearby_chunks:
            # Choose a nearby chunk to patrol
            target_chunk = random.choice(nearby_chunks)
            self.logger.debug(f"NPC {self.name} patrolling to {target_chunk.coordinates}")
            return {"action": "patrol", "new_coords": target_chunk.coordinates}

        return None

    def _update_needs(self, world_context):
        """Update NPC needs based on current state and time of day."""
        # ===== FOOD CONSUMPTION FROM FACTION INVENTORY =====
        # Before food decreases, try to eat from faction inventory
        if self.needs.get("food", 100) < 90 and self.faction_id:  # Only eat if somewhat hungry
            world_engine = world_context.get("world_engine")
            if world_engine and self.faction_id in world_engine.factions:
                faction = world_engine.factions[self.faction_id]
                if hasattr(faction, "resources"):
                    # Try to consume from available food resource types
                    food_types = [
                        "food",
                        "plant",
                        "animal",
                        "fish",
                    ]  # Order of preference
                    food_consumed = 0
                    target_consumption = 20  # Maximum to consume this tick

                    for food_type in food_types:
                        if food_consumed >= target_consumption:
                            break
                        if faction.resources.get(food_type, 0) > 0:
                            available = faction.resources[food_type]
                            to_consume = min(target_consumption - food_consumed, available)
                            faction.resources[food_type] -= to_consume
                            food_consumed += to_consume

                    if food_consumed > 0:
                        self.needs["food"] = min(100, self.needs.get("food", 100) + food_consumed)

                        if self.age % 20 == 0:  # Log occasionally
                            self.logger.debug(
                                f"NPC {self.name} consumed {food_consumed:.1f} food from faction. Personal food: {self.needs['food']:.1f}"
                            )

        # Food decreases over time
        self.needs["food"] = max(0, self.needs.get("food", 100) - 0.5)

        # Safety based on health
        self.needs["safety"] = min(100, self.health)

        # ===== TIME-BASED REST MECHANICS =====
        time_info = world_context.get("time", {})
        current_hour = time_info.get("hour", 12)

        # Rest decreases during active hours, increases during rest/night
        is_night = current_hour >= 22 or current_hour <= 5
        is_day = 9 <= current_hour <= 17

        if is_night:
            # Rest increases at night (if resting)
            self.needs["rest"] = min(100, self.needs.get("rest", 100) + 3)
        elif is_day:
            # Rest decreases more during active day hours
            self.needs["rest"] = max(0, self.needs.get("rest", 100) - 1.5)
        else:
            # Normal rest decrease during dawn/dusk
            self.needs["rest"] = max(0, self.needs.get("rest", 100) - 1)

        # ===== DEBUG: Log needs update =====
        if self.age % 10 == 0:
            self.logger.debug(f"NPC {self.name} needs updated: {self.needs} (hour: {current_hour})")

        # ===== PERIODIC FORCED DECAY TO PROMPT ACTION =====
        total_minutes = world_context.get("time", {}).get("total_minutes")
        if total_minutes and total_minutes % self.NEED_FORCE_INTERVAL == 0:
            extra_food = random.randint(*self.NEED_FORCE_FOOD_DECAY_RANGE)
            extra_rest = random.randint(*self.NEED_FORCE_REST_DECAY_RANGE)
            self.needs["food"] = max(0, self.needs.get("food", 100) - extra_food)
            self.needs["rest"] = max(0, self.needs.get("rest", 100) - extra_rest)
            if self.NEED_FORCE_SAFETY_DECAY:
                self.needs["safety"] = max(
                    0, self.needs.get("safety", 100) - self.NEED_FORCE_SAFETY_DECAY
                )
            self.logger.debug(
                f"NPC {self.name} periodic need decay applied (every {self.NEED_FORCE_INTERVAL}m): -food {extra_food}, -rest {extra_rest}; needs now {self.needs}"
            )

    def _is_chunk_safer(self, chunk, current_chunk):
        """Determine if a chunk is safer than the current one."""
        # Simple safety calculation based on number of predators vs prey
        current_predators = sum(
            1 for npc in current_chunk.npcs if getattr(npc, "is_predator", False)
        )
        current_prey = len(current_chunk.npcs) - current_predators

        chunk_predators = sum(1 for npc in chunk.npcs if getattr(npc, "is_predator", False))
        chunk_prey = len(chunk.npcs) - chunk_predators

        # Safer if fewer predators relative to prey
        current_ratio = current_predators / max(1, current_prey)
        chunk_ratio = chunk_predators / max(1, chunk_prey)

        # Throttle & suppress noisy spam when both ratios evaluate to zero repeatedly.
        if not hasattr(self, "_last_safety_log_tick"):
            self._last_safety_log_tick = -1
        # Try to get global tick if available
        global_tick = None
        try:
            global_tick = current_chunk.world._tick_count  # if chunk holds backref (may not exist)
        except Exception:
            pass
        should_log = True
        if current_ratio == 0.0 and chunk_ratio == 0.0:
            # Only log occasionally when both zero
            if global_tick is not None:
                should_log = global_tick % 300 == 0  # every 300 ticks max
            else:
                should_log = False
        else:
            # Non-zero change: allow more frequent logs but still throttle
            if (
                global_tick is not None
                and self._last_safety_log_tick >= 0
                and global_tick - self._last_safety_log_tick < 20
            ):
                should_log = False
        if should_log:
            self.logger.debug(
                f"NPC {self.name} safety check - Current ratio: {current_ratio:.2f}, Chunk ratio: {chunk_ratio:.2f}"
            )
            if global_tick is not None:
                self._last_safety_log_tick = global_tick

        return chunk_ratio < current_ratio

    def generate_dialogue(
        self,
        target_npc,
        context,
        tribal_diplomacy,
        tribe_lookup: Optional[Dict[str, Any]] = None,
    ):
        """Generate dialogue for social interactions using Markov chains, influenced by tribal diplomacy, relationships, traits, and culture."""
        # Robust import (handles running as script or package)
        try:
            from markov_dialogue import generate_markov_dialogue  # type: ignore
        except Exception:
            try:
                from ..markov_dialogue import generate_markov_dialogue  # type: ignore
            except Exception:
                # Last resort dynamic import
                import importlib
                import sys
                import os

                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if base_dir not in sys.path:
                    sys.path.append(base_dir)
                generate_markov_dialogue = importlib.import_module("markov_dialogue").generate_markov_dialogue  # type: ignore
        target_faction_id = target_npc.faction_id
        relationship = self.relationships.get(target_npc.name, 0)
        # Handle tribal_diplomacy safely
        try:
            diplomacy = tribal_diplomacy.get((self.faction_id, target_faction_id), 0)
        except AttributeError:
            diplomacy = 0
        # Adjust context based on tribal diplomacy
        if diplomacy > 0.5:
            adjusted_context = f"friendly_{context}"
        elif diplomacy < -0.5:
            adjusted_context = f"hostile_{context}"
        else:
            adjusted_context = f"neutral_{context}"
        # Further adjust based on personal relationship
        if relationship > 10:
            adjusted_context = f"close_{adjusted_context}"
        elif relationship < -5:
            adjusted_context = f"distant_{adjusted_context}"
        # Use trait if available
        trait = self.traits[0] if self.traits else None
        # Build tags for conditioning
        tags = []
        if "friendly_" in adjusted_context:
            tags.append("friend")
        if "hostile_" in adjusted_context:
            tags.append("hostile")
        if "close_" in adjusted_context:
            tags.append("close")
        if "distant_" in adjusted_context:
            tags.append("distant")
        if trait:
            tags.append(trait)
        # Use improved Markov-based dialogue generation with context + tags
        chosen = generate_markov_dialogue(
            context,
            trait=trait,
            seed=None,
            adjusted_context=adjusted_context,
            tags=tags,
        )
        # Store original Markov for potential logging
        original_markov = chosen
        # Improve punctuation before logical soundness check
        chosen = improve_punctuation(chosen)
        # Check logical soundness, regenerate if not sound (up to 2 tries)
        for _ in range(2):
            if is_logically_sound_statement(chosen):
                break
            # Try to regenerate and re-punctuate
            chosen = generate_markov_dialogue(
                context,
                trait=trait,
                seed=None,
                adjusted_context=adjusted_context,
                tags=tags,
            )
            chosen = improve_punctuation(chosen)
        # === CULTURAL / MYTH INJECTION ===
        try:
            if tribe_lookup and self.faction_id and random.random() < 0.12:
                tribe = tribe_lookup.get(self.faction_id)
                if tribe and hasattr(tribe, "cultural_ledger"):
                    myths = tribe.cultural_ledger.get("history_myths", {}).get("myths", [])
                    rituals = tribe.cultural_ledger.get("rituals_customs", {}).get("rituals", [])
                    snippet = None
                    if myths:
                        myth = random.choice(myths)
                        myth_name = myth.get("name") or myth.get("event", "ancient tale")
                        snippet = f"Have you heard the tale of {myth_name}?"
                    elif rituals:
                        ritual = random.choice(rituals)
                        ritual_name = (
                            ritual.get("name", "our sacred rite")
                            if isinstance(ritual, dict)
                            else str(ritual)
                        )
                        snippet = f"Soon we observe {ritual_name}."
                    if snippet:
                        if len(chosen) < 40:
                            chosen = (
                                f"{chosen} {snippet}"
                                if not chosen.endswith(".")
                                else f"{chosen} {snippet}"
                            )
                        else:
                            chosen = snippet
        except Exception:
            pass
        # === LEXICAL INJECTION (tribal language terms) ===
        try:
            if tribe_lookup and self.faction_id and random.random() < 0.18:
                tribe = tribe_lookup.get(self.faction_id)
                if tribe and hasattr(tribe, "cultural_ledger"):
                    lang = tribe.cultural_ledger.get("language", {})
                    lex = lang.get("lexicon", {})
                    if lex:
                        concept_pool = [
                            "food",
                            "trade",
                            "ally",
                            "spirit",
                            "water",
                            "danger",
                            "hunt",
                        ]
                        concepts = [c for c in concept_pool if c in lex]
                        if concepts:
                            concept = random.choice(concepts)
                            native = lex.get(concept)
                            lowered = chosen.lower()
                            replaced = False
                            if concept in lowered and random.random() < 0.5:

                                def _swap(text, needle, repl):
                                    return text.replace(needle, repl, 1)

                                idx = lowered.find(concept)
                                if idx >= 0 and chosen[idx : idx + 1].isupper():
                                    inj = native.capitalize()
                                else:
                                    inj = native
                                chosen = _swap(chosen, chosen[idx : idx + len(concept)], inj)
                                replaced = True
                            if not replaced:
                                gloss = concept if random.random() < 0.7 else ""
                                if gloss:
                                    chosen = f"{chosen} ({native}={gloss})"
                                else:
                                    chosen = f"{chosen} ({native})"
                            usage = lang.setdefault("usage", {})
                            usage[concept] = usage.get(concept, 0) + 1
        except Exception:
            pass
        # Optional LLM enhancement
        import os

        use_llm = os.getenv("SANDBOX_LLM_DIALOGUE", "false").lower() == "true"
        if use_llm:
            try:
                # Determine mood based on diplomacy and relationship
                mood = "neutral"
                if diplomacy > 0.5 or relationship > 10:
                    mood = "happy"
                elif diplomacy < -0.5 or relationship < -5:
                    mood = "angry"
                # Pass Markov output as a seed/context to the LLM
                enhanced = generate_agent_dialogue(
                    self.name,
                    f"{context} with {target_npc.name}\nSeed: {original_markov}",
                    mood
                )
                # Store both for logging
                self._last_dialogue_original = original_markov
                self._last_dialogue_enhanced = enhanced
                # Improve punctuation for LLM output
                enhanced = improve_punctuation(enhanced)
                # Check logical soundness, fallback to Markov if LLM fails
                if is_logically_sound_statement(enhanced):
                    chosen = enhanced
                else:
                    chosen = original_markov
            except ImportError:
                pass
        return chosen

    def _spring_exploration_action(self, world_context):
        """Special spring exploration behavior for expansion and renewal."""
        nearby_chunks = world_context.get("nearby_chunks", [])

        if nearby_chunks:
            # In spring, prefer chunks with growth potential
            for chunk in nearby_chunks:
                if chunk.resources.get("food", 0) > 5 or chunk.terrain.name in [
                    "GRASSLAND",
                    "FOREST",
                ]:
                    self.logger.debug(f"NPC {self.name} spring exploration to {chunk.coordinates}")
                    return {"action": "move", "new_coords": chunk.coordinates}

            # Fallback to random exploration
            target_chunk = random.choice(nearby_chunks)
            self.logger.debug(f"NPC {self.name} spring exploration to {target_chunk.coordinates}")
            return {"action": "move", "new_coords": target_chunk.coordinates}

        return None

    # ===== ENHANCED PATHFINDING AND RESOURCE DETECTION METHODS =====

    def _initialize_pathfinding(self, world_context):
        """Initialize the pathfinding engine with world reference."""
        try:
            from pathfinding import PathfindingEngine

            # Get world engine from context (may need to be passed differently)
            self._world_engine = world_context.get("world_engine")
            if self._world_engine:
                self._pathfinding_engine = PathfindingEngine(self._world_engine)
            else:
                self.logger.warning(
                    f"NPC {self.name} could not initialize pathfinding - no world engine in context"
                )
        except ImportError:
            self.logger.warning(f"NPC {self.name} could not import pathfinding module")

    def _get_chunk_at(self, coordinates, world_context):
        """Get chunk at given coordinates."""
        if self._world_engine:
            try:
                return self._world_engine.get_chunk(coordinates[0], coordinates[1])
            except Exception:
                return None
        return None

    def _update_resource_memory(
        self,
        resource_type: str,
        coordinates: Tuple[int, int],
        amount: float,
        world_context,
    ):
        """Update memory of resource locations."""
        current_tick = world_context.get("time", {}).get("total_minutes", 0)

        if resource_type not in self.known_resources:
            self.known_resources[resource_type] = []

        # Update existing entry or add new one
        resource_list = self.known_resources[resource_type]
        for i, (coords, old_amount, old_tick) in enumerate(resource_list):
            if coords == coordinates:
                resource_list[i] = (coordinates, amount, current_tick)
                return

        # Add new resource location
        resource_list.append((coordinates, amount, current_tick))

        # Clean up old memories
        self._cleanup_resource_memory(resource_type, current_tick)

    def _cleanup_resource_memory(self, resource_type: str, current_tick: int):
        """Remove old resource memories."""
        if resource_type not in self.known_resources:
            return

        # Remove memories older than decay threshold
        self.known_resources[resource_type] = [
            (coords, amount, tick)
            for coords, amount, tick in self.known_resources[resource_type]
            if current_tick - tick < self.resource_memory_decay
        ]

    def _find_best_resource_location(
        self, resource_type: str, world_context, season_modifier: float = 1.0
    ) -> Optional[Tuple[Tuple[int, int], float, float]]:
        """Find the best resource location considering memory and fresh search."""
        if not self._pathfinding_engine:
            return None

        current_tick = world_context.get("time", {}).get("total_minutes", 0)
        best_location = None
        best_score = 0

        # Check known resource locations first
        if resource_type in self.known_resources:
            for coords, remembered_amount, tick in self.known_resources[resource_type]:
                # Skip very old memories
                if current_tick - tick > self.resource_memory_decay // 2:
                    continue

                distance = self._pathfinding_engine.euclidean_distance(self.coordinates, coords)
                if distance <= self.resource_search_radius:
                    # Verify the resource is still there
                    chunk = self._get_chunk_at(coords, world_context)
                    if chunk:
                        actual_amount = chunk.resources.get(resource_type, 0)
                        if actual_amount > 0:
                            # Update memory with current amount
                            self._update_resource_memory(
                                resource_type, coords, actual_amount, world_context
                            )

                            from pathfinding import calculate_resource_priority_score

                            score = calculate_resource_priority_score(
                                self,
                                resource_type,
                                actual_amount,
                                distance,
                                season_modifier,
                            )

                            if score > best_score:
                                best_score = score
                                best_location = (coords, actual_amount, distance)

        # Search for new resources in the area
        new_resources = self._pathfinding_engine.find_all_resources_in_radius(
            self.coordinates, resource_type, self.resource_search_radius, min_amount=1.0
        )

        for coords, amount in new_resources:
            distance = self._pathfinding_engine.euclidean_distance(self.coordinates, coords)

            # Update memory
            self._update_resource_memory(resource_type, coords, amount, world_context)

            from pathfinding import calculate_resource_priority_score

            score = calculate_resource_priority_score(
                self, resource_type, amount, distance, season_modifier
            )

            if score > best_score:
                best_score = score
                best_location = (coords, amount, distance)

        return best_location

    def _find_exploration_target(self, world_context) -> Optional[Tuple[int, int]]:
        """Find a good location to explore for resources."""
        if not self._pathfinding_engine:
            return None

        # Look for unexplored areas within a reasonable range
        exploration_radius = self.resource_search_radius // 2

        for _ in range(5):  # Try a few random directions
            angle = random.uniform(0, 2 * 3.14159)
            distance = random.uniform(3, exploration_radius)

            dx = int(distance * math.cos(angle))
            dy = int(distance * math.sin(angle))

            target = (self.coordinates[0] + dx, self.coordinates[1] + dy)

            # Check if this is a valid exploration target
            if self._pathfinding_engine.is_passable(target):
                return target

        return None

    def _share_resource_knowledge(self, other_npc, resource_type: str):
        """Share knowledge of resource locations with another NPC."""
        if resource_type not in self.known_resources:
            return

        # Share our knowledge with the other NPC
        if resource_type not in other_npc.known_resources:
            other_npc.known_resources[resource_type] = []

        for coords, amount, tick in self.known_resources[resource_type]:
            # Check if other NPC already knows this location
            already_known = any(
                known_coords == coords
                for known_coords, _, _ in other_npc.known_resources[resource_type]
            )

            if not already_known:
                # Add with slightly reduced confidence (shared knowledge)
                other_npc.known_resources[resource_type].append((coords, amount * 0.8, tick))

    def _seek_any_resource_action(self, world_context, priority_resources: List[str] = None):
        """Generic resource seeking with intelligent prioritization and coordination."""
        if priority_resources is None:
            priority_resources = ["food", "wood", "stone", "water"]

        if not self._pathfinding_engine:
            self._initialize_pathfinding(world_context)

        current_chunk = world_context.get("current_chunk")
        season_modifier = self._get_seasonal_modifier(world_context)

        best_action = None
        best_priority = 0

        for resource_type in priority_resources:
            # Check current chunk first
            current_amount = current_chunk.resources.get(resource_type, 0)
            if current_amount > 0:
                from pathfinding import calculate_resource_priority_score

                priority = calculate_resource_priority_score(
                    self, resource_type, current_amount, 0, season_modifier
                )

                if priority > best_priority:
                    best_priority = priority
                    collect_amount = (
                        min(10, current_amount)
                        if resource_type == "food"
                        else min(5, current_amount)
                    )
                    best_action = {
                        "action": "collect",
                        "resource": resource_type,
                        "amount": collect_amount,
                    }

            # Look for distant resources with coordination
            best_location = self._find_best_resource_location(
                resource_type, world_context, season_modifier
            )

            # Check if too many faction members are targeting the same resource
            if best_location and self._coordinate_with_faction_members(
                world_context, resource_type
            ):
                # Find alternative target
                alternative = self._find_alternative_resource_target(world_context, resource_type)
                if alternative:
                    best_location = alternative

            if best_location:
                coords, amount, distance = best_location

                from pathfinding import calculate_resource_priority_score

                priority = calculate_resource_priority_score(
                    self, resource_type, amount, distance, season_modifier
                )

                if priority > best_priority:
                    best_priority = priority
                    if distance <= 1.5:  # Adjacent
                        best_action = {
                            "action": "move",
                            "new_coords": coords,
                            "resource_target": resource_type,
                        }
                    else:
                        # Plan path for distant resource
                        if self._pathfinding_engine:
                            path = self._pathfinding_engine.a_star_pathfind(
                                self.coordinates,
                                coords,
                                max_distance=self.resource_search_radius,
                            )
                            if path and len(path) > 1:
                                self.current_path = path[1:]
                                self.path_target = coords
                                best_action = {
                                    "action": "move",
                                    "new_coords": path[1],
                                    "resource_target": resource_type,
                                }

        return best_action

    def _get_seasonal_modifier(self, world_context) -> float:
        """Get seasonal modifier for resource availability."""
        season = world_context.get("time", {}).get("season", 1)
        season_modifiers = {
            0: 0.7,  # Winter - resources scarce
            1: 1.3,  # Spring - resources growing
            2: 1.5,  # Summer - resources abundant
            3: 1.2,  # Autumn - harvest time
        }
        return season_modifiers.get(season, 1.0)

    def _get_faction_resource_priorities(self) -> List[str]:
        """Get resource priorities based on faction needs."""
        # TODO: This could be enhanced to read from faction-level resource tracking
        base_priorities = ["food", "wood", "stone", "water"]

        # Adjust based on needs
        if self.needs.get("food", 100) < 70:
            # Prioritize food when hungry
            base_priorities = ["food"] + [r for r in base_priorities if r != "food"]

        return base_priorities

    def _coordinate_with_faction_members(self, world_context, resource_type: str) -> bool:
        """Check if other faction members are already targeting the same resource."""
        if not hasattr(self, "path_target") or not self.path_target:
            return False

        current_chunk = world_context.get("current_chunk")
        nearby_chunks = world_context.get("nearby_chunks", [])

        # Check NPCs in current and nearby chunks
        all_nearby_npcs = []
        if current_chunk:
            all_nearby_npcs.extend(current_chunk.npcs)
        for chunk in nearby_chunks:
            all_nearby_npcs.extend(chunk.npcs)

        # Count faction members targeting same location
        targeting_same = 0
        for npc in all_nearby_npcs:
            if (
                npc != self
                and npc.faction_id == self.faction_id
                and hasattr(npc, "path_target")
                and npc.path_target == self.path_target
            ):
                targeting_same += 1

        # If too many are targeting the same resource, consider alternatives
        return targeting_same >= 2  # Limit to 2 NPCs per resource location

    def _find_alternative_resource_target(self, world_context, resource_type: str):
        """Find an alternative resource target to avoid overcrowding."""
        if not self._pathfinding_engine:
            return None

        # Get all available resources of this type
        all_resources = self._pathfinding_engine.find_all_resources_in_radius(
            self.coordinates, resource_type, self.resource_search_radius, min_amount=1.0
        )

        # Filter out resources that are being targeted by too many NPCs
        current_chunk = world_context.get("current_chunk")
        nearby_chunks = world_context.get("nearby_chunks", [])
        all_nearby_npcs = []
        if current_chunk:
            all_nearby_npcs.extend(current_chunk.npcs)
        for chunk in nearby_chunks:
            all_nearby_npcs.extend(chunk.npcs)

        # Count targets for each resource location
        target_counts = {}
        for npc in all_nearby_npcs:
            if (
                npc != self
                and npc.faction_id == self.faction_id
                and hasattr(npc, "path_target")
                and npc.path_target
            ):
                target_counts[npc.path_target] = target_counts.get(npc.path_target, 0) + 1

        # Find best uncrowded resource
        season_modifier = self._get_seasonal_modifier(world_context)
        best_location = None
        best_score = 0

        for coords, amount in all_resources:
            # Skip if too crowded
            if target_counts.get(coords, 0) >= 2:
                continue

            distance = self._pathfinding_engine.euclidean_distance(self.coordinates, coords)
            from pathfinding import calculate_resource_priority_score

            score = calculate_resource_priority_score(
                self, resource_type, amount, distance, season_modifier
            )

            if score > best_score:
                best_score = score
                best_location = (coords, amount, distance)

        return best_location

    def _cautious_resource_check(self, world_context):
        """Cautious resource assessment for autumn/winter dawn."""
        current_chunk = world_context.get("current_chunk")

        # Check current resources before moving
        if current_chunk.resources.get("food", 0) > 3:
            amount = min(5, current_chunk.resources["food"])  # Conservative gathering
            self.logger.debug(f"NPC {self.name} cautious resource gathering: {amount} food")
            return {"action": "collect", "resource": "food", "amount": amount}

        # Stay put if no immediate resources - don't waste energy
        return {"action": "rest", "reason": "conserving_energy"}

    def _prepare_for_winter_night(self, world_context):
        """Prepare for harsh winter night conditions."""
        current_chunk = world_context.get("current_chunk")
        nearby_chunks = world_context.get("nearby_chunks", [])

        # Priority 1: Ensure safety
        if self.needs.get("safety", 100) < 60:
            # Look for safer area
            for chunk in nearby_chunks:
                if self._is_chunk_safer(chunk, current_chunk):
                    self.logger.debug(
                        f"NPC {self.name} seeking winter night safety at {chunk.coordinates}"
                    )
                    return {"action": "move", "new_coords": chunk.coordinates}

        # Priority 2: Last chance food gathering
        if self.needs.get("food", 100) < 50 and current_chunk.resources.get("food", 0) > 2:
            amount = min(3, current_chunk.resources["food"])  # Small amount - conserve energy
            self.logger.debug(f"NPC {self.name} final winter food gathering: {amount}")
            return {"action": "collect", "resource": "food", "amount": amount}

        # Priority 3: Rest early to prepare for harsh night
        self.logger.debug(f"NPC {self.name} preparing for winter night")
        return {"action": "rest", "reason": "winter_night_preparation"}

    # === Seasonal Helper Methods (added to satisfy seasonal tests) ===
    def _get_seasonal_gathering_efficiency(self, season: int) -> float:
        """Return a multiplicative efficiency modifier for gathering based on season.

        Pattern:
        - Spring (0): 1.1 (growth surge)
        - Summer (1): 1.25 (peak abundance)
        - Autumn (2): 1.0 (normal, storing focus)
        - Winter (3): 0.6 (scarcity)
        Unknown season falls back to 1.0.
        """
        mapping = {0: 1.1, 1: 1.25, 2: 1.0, 3: 0.6}
        return mapping.get(season, 1.0)

    def _get_seasonal_resource_availability(self, resource: str, season: int) -> float:
        """Return an availability scalar (0..1.5) for a resource by season.

        Simplified heuristic:
        - Berries/plant foods: high in Summer, medium Spring/Autumn, low Winter.
        - Roots: steady year round, slight dip in Summer dry stress.
        - Meat: moderate all seasons, slight winter bump (hunting migrations) but logistic penalty keeps ~1.0.
        - Wood: constant 1.0.
        - Stone/Ore: constant 1.0.
        Unrecognized resources default 1.0.
        """
        r = resource.lower()
        if r in ("berries", "berry", "fruit", "fruits", "plant", "plants"):
            return [0.9, 1.3, 0.85, 0.4][season] if 0 <= season <= 3 else 1.0
        if r in ("roots", "root"):
            return [1.0, 0.95, 1.0, 1.0][season] if 0 <= season <= 3 else 1.0
        if r in ("meat", "game", "animal"):
            return [1.0, 1.05, 1.0, 1.1][season] if 0 <= season <= 3 else 1.0
        return 1.0  # Default availability

    def _check_predator_switch(self, world_context, faction_memory):
        """Check if NPC should switch to Predator faction based on conditions.

        Returns an action dict if switching should occur, None otherwise.
        """
        # Only human NPCs can become predators
        if self.faction_id != "Human":
            return None

        # Get current conditions
        food_level = self.needs.get("food", 100)
        current_chunk = world_context.get("current_chunk")

        # Check for severe starvation (primary trigger)
        severe_starvation = food_level < 10

        # Check for prolonged hunger (secondary trigger)
        prolonged_hunger = food_level < 25 and self.age > 50  # Been hungry for a while

        # Check for social isolation (tertiary trigger)
        social_isolation = len(self.relationships) < 2  # Very few social connections

        # Check for environmental desperation (quaternary trigger)
        environmental_desperation = False
        if current_chunk:
            # Check if chunk has very low food resources
            chunk_food = current_chunk.resources.get("food", 0)
            environmental_desperation = chunk_food < 5

            # Check for famine events
            event_manager = world_context.get("event_manager")
            if event_manager:
                active_events = event_manager.get_events_for_location(current_chunk.coordinates)
                famine_active = any(event.name == "Famine" for event in active_events)
                if famine_active and food_level < 30:
                    environmental_desperation = True

        # Personality factor - some NPCs are more prone to predatory behavior
        personality_factor = 0.1  # Base 10% chance
        if "aggressive" in self.traits:
            personality_factor += 0.2
        if "survivor" in self.traits:
            personality_factor += 0.15
        if "cunning" in self.traits:
            personality_factor += 0.1

        # Calculate switching probability
        switch_probability = 0.0

        if severe_starvation:
            switch_probability = 0.8  # 80% chance when starving
        elif prolonged_hunger and environmental_desperation:
            switch_probability = 0.4  # 40% chance with hunger + bad environment
        elif prolonged_hunger and social_isolation:
            switch_probability = 0.3  # 30% chance with hunger + isolation
        elif environmental_desperation and social_isolation:
            switch_probability = 0.2  # 20% chance with bad environment + isolation
        elif prolonged_hunger:
            switch_probability = 0.1  # 10% chance with just prolonged hunger

        # Apply personality modifier
        switch_probability *= 1.0 + personality_factor
        switch_probability = min(switch_probability, 0.95)  # Cap at 95%

        # Make the decision
        if random.random() < switch_probability:
            self.logger.info(
                f"NPC {self.name} switching to Predator faction! "
                f"Food: {food_level:.1f}, Conditions: starvation={severe_starvation}, "
                f"hunger={prolonged_hunger}, isolation={social_isolation}, "
                f"desperation={environmental_desperation}"
            )

            # Switch faction
            old_faction = self.faction_id
            self.faction_id = "Predator"

            # Update faction memberships
            world = world_context.get("world")
            if world and old_faction in world.factions:
                world.factions[old_faction].remove_member(self.name)
            if world and self.faction_id in world.factions:
                world.factions[self.faction_id].add_member(self.name)

            # Update traits to reflect predatory nature
            if "predator" not in self.traits:
                self.traits.append("predator")

            # Clear tribal membership (predators don't belong to tribes)
            # This would need to be handled by the tribal manager if implemented

            return {
                "action": "switch_faction",
                "new_faction": "Predator",
                "reason": "survival_instincts",
                "old_faction": old_faction,
            }

        return None

    def _decide_predator_action(self, world_context, faction_memory):
        """Decide what action a predator NPC should take.

        Predators prioritize:
        1. Hunting/scavenging for food
        2. Aggression toward non-predators
        3. Territory defense
        4. Survival over social behavior
        """
        current_chunk = world_context.get("current_chunk")
        if not current_chunk:
            return None

        # ===== PREDATOR FOOD PRIORITY =====
        # Predators are always hungry and prioritize food aggressively
        food_level = self.needs.get("food", 100)
        if food_level < 80:  # Much higher threshold than normal NPCs
            # Look for prey (other NPCs in the same chunk)
            potential_prey = [
                npc
                for npc in current_chunk.npcs
                if npc != self and npc.faction_id != "Predator" and npc.health > 0
            ]

            if potential_prey:
                # Attack the weakest prey
                prey = min(potential_prey, key=lambda x: x.health)
                self.logger.debug(
                    f"Predator {self.name} targeting prey: {prey.name} (health: {prey.health})"
                )
                return {"action": "attack", "target": prey.name, "reason": "hunting"}

            # If no prey, aggressively seek food resources
            food_action = self._seek_food_action(
                world_context, season_modifier=2.0
            )  # More aggressive food seeking
            if food_action:
                return food_action

        # ===== PREDATOR TERRITORY DEFENSE =====
        # Predators defend their territory from other predators
        other_predators = [
            npc for npc in current_chunk.npcs if npc != self and npc.faction_id == "Predator"
        ]
        if other_predators and random.random() < 0.3:  # 30% chance to challenge
            target = random.choice(other_predators)
            return {
                "action": "attack",
                "target": target.name,
                "reason": "territory_defense",
            }

        # ===== PREDATOR SCAVENGING =====
        # Check for dead NPCs to scavenge
        dead_npcs = [npc for npc in current_chunk.npcs if npc.health <= 0]
        if dead_npcs and food_level < 90:
            # Scavenge from the dead
            return {
                "action": "scavenge",
                "target": random.choice(dead_npcs).name,
                "reason": "scavenging",
            }

        # ===== PREDATOR EXPLORATION =====
        # Predators explore more aggressively to find prey/territory
        if (
            self.needs.get("food", 100) > 50
            and self.needs.get("safety", 100) > 50
            and random.random() < 0.4
        ):  # 40% chance vs normal exploration
            nearby_chunks = world_context.get("nearby_chunks", [])
            if nearby_chunks:
                # Prefer chunks with more NPCs (potential prey)
                prey_rich_chunks = []
                for chunk in nearby_chunks:
                    npc_count = len([npc for npc in chunk.npcs if npc.faction_id != "Predator"])
                    prey_rich_chunks.extend([chunk] * max(1, npc_count))  # Weight by prey count

                if prey_rich_chunks:
                    target_chunk = random.choice(prey_rich_chunks)
                    return {
                        "action": "move",
                        "new_coords": target_chunk.coordinates,
                        "reason": "hunting_grounds",
                    }

        # ===== PREDATOR REST =====
        # Predators rest when they're not hunting
        if self.needs.get("rest", 100) < 60:
            return {"action": "rest", "reason": "predator_recovery"}

        # Default: wander predator-style (more aggressive movement)
        if random.random() < 0.6:  # 60% chance to move vs normal wandering
            nearby_chunks = world_context.get("nearby_chunks", [])
            safe_chunks = [c for c in nearby_chunks if not getattr(c, "impassable", False)]
            if safe_chunks:
                target = random.choice(safe_chunks)
                return {
                    "action": "move",
                    "new_coords": target.coordinates,
                    "reason": "predator_prowling",
                }

        # If nothing else, rest
        return {"action": "rest", "reason": "predator_ambush"}
