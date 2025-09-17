import random
from typing import Dict, List, Optional, Any
from datetime import datetime
from .tribe import Tribe
from markov_behavior import make_markov_choice


class TribalLanguage:
    """Rudimentary tribal language system"""

    # Base tribal vocabulary
    BASE_VOCABULARY = {
        "food": ["yum", "eat", "hunger"],
        "danger": ["bad", "threat", "fear"],
        "friend": ["ally", "together", "help"],
        "enemy": ["foe", "attack", "stranger"],
        "home": ["camp", "shelter", "rest"],
        "hunt": ["chase", "kill", "prey"],
        "gather": ["collect", "find", "take"],
        "trade": ["give", "take", "fair"],
        "help": ["aid", "assist", "support"],
        "warning": ["caution", "danger", "alert"],
        "peace": ["calm", "truce", "harmony"],
        "war": ["fight", "battle", "conflict"],
    }

    def __init__(self, tribe: Tribe):
        self.tribe = tribe
        self._initialize_dialect()

    def _initialize_dialect(self) -> None:
        """Initialize tribal dialect with base vocabulary"""
        for concept, words in self.BASE_VOCABULARY.items():
            if concept not in self.tribe.dialect:
                # Use Markov choice for vocab selection
                # based on tribal traits
                tribe_context = {
                    "cultural_focus": getattr(self.tribe, "cultural_focus", "linguistic"),
                    "traits": getattr(self.tribe, "traits", []),
                    "stability": "stable",
                    "season": "spring",
                }
                self.tribe.dialect[concept] = make_markov_choice(
                    words, f"vocabulary_{concept}", "cultural", tribe_context
                )

    def translate_to_tribal(self, concept: str) -> str:
        """Translate a concept to tribal language"""
        # Use tribe's dialect if available
        if hasattr(self.tribe, "dialect") and concept in self.tribe.dialect:
            return self.tribe.dialect[concept]

        # Fallback to base vocabulary using Markov choice
        words = self.BASE_VOCABULARY.get(concept)
        if words:
            tribe_context = {
                "cultural_focus": getattr(self.tribe, "cultural_focus", "linguistic"),
                "traits": getattr(self.tribe, "traits", []),
                "stability": "stable",
                "season": "spring",
            }
            return make_markov_choice(words, f"vocabulary_{concept}", "cultural", tribe_context)

        # Last resort: return the original term
        return concept

    def generate_tribal_phrase(self, intent: str, context: str = "general") -> str:
        """Generate a tribal phrase based on intent and context"""

        phrases = {
            "greeting": [
                f"{self.translate_to_tribal('friend')}!",
                f"{self.translate_to_tribal('home')} welcomes you",
                f"{self.tribe.symbol} {self.translate_to_tribal('peace')}",
            ],
            "warning": [
                f"{self.translate_to_tribal('danger')}! " f"{self.translate_to_tribal('warning')}",
                f"{self.translate_to_tribal('enemy')} near!",
                f"Beware the {self.translate_to_tribal('threat')}",
            ],
            "invitation": [
                f"Join our {self.translate_to_tribal('home')}",
                f"{self.translate_to_tribal('together')} we are strong",
                f"Come to {self.tribe.symbol} camp",
            ],
            "trade": [
                f"We {self.translate_to_tribal('trade')} " f"{self.translate_to_tribal('fair')}",
                f"{self.translate_to_tribal('give')} for " f"{self.translate_to_tribal('take')}",
                f"Good {self.translate_to_tribal('trade')} here",
            ],
            "alliance": [
                f"{self.translate_to_tribal('friend')} " f"{self.translate_to_tribal('together')}",
                f"{self.tribe.symbol} allies with you",
                f"Let us be {self.translate_to_tribal('peace')} brothers",
            ],
            "threat": [
                f"{self.translate_to_tribal('enemy')}! " f"{self.translate_to_tribal('war')}",
                f"Our {self.translate_to_tribal('fight')} is strong",
                f"Beware {self.tribe.symbol} " f"{self.translate_to_tribal('anger')}",
            ],
        }

        if intent in phrases:
            # Use Markov choice for phrase selection
            from markov_behavior import make_markov_choice

            tribe_context = {
                "cultural_focus": getattr(self.tribe, "cultural_focus", "communication"),
                "traits": getattr(self.tribe, "traits", []),
                "stability": "stable",
                "season": "spring",
            }

            return make_markov_choice(
                phrases[intent], f"phrase_{intent}", "cultural", tribe_context
            )

        # Fallback to simple tribal word
        return self.translate_to_tribal(intent)

    def interpret_phrase(self, phrase: str, from_tribe: Optional[Tribe] = None) -> Dict[str, Any]:
        """Interpret a phrase and determine intent"""

        # Simple keyword matching for intent detection
        intent_keywords = {
            "greeting": ["friend", "welcome", "peace", "hello"],
            "warning": ["danger", "warning", "threat", "beware", "caution"],
            "invitation": ["join", "come", "together", "camp", "home"],
            "trade": ["trade", "give", "take", "fair", "exchange"],
            "alliance": ["friend", "ally", "together", "peace", "brother"],
            "threat": ["enemy", "war", "fight", "anger", "attack"],
        }

        detected_intent = "unknown"
        confidence = 0.0

        for intent, keywords in intent_keywords.items():
            matches = sum(1 for keyword in keywords if keyword.lower() in phrase.lower())
            if matches > confidence:
                confidence = matches
                detected_intent = intent

        return {
            "intent": detected_intent,
            "confidence": confidence / max(len(keywords) for keywords in intent_keywords.values()),
            "from_tribe": from_tribe.name if from_tribe else None,
            "original_phrase": phrase,
        }


class TribalCommunication:
    """Handles communication between tribes"""

    def __init__(self) -> None:
        self.languages: Dict[str, TribalLanguage] = {}

    def get_tribal_language(self, tribe: Tribe) -> TribalLanguage:
        """Get or create language system for a tribe"""
        if tribe.name not in self.languages:
            self.languages[tribe.name] = TribalLanguage(tribe)
        return self.languages[tribe.name]

    def tribal_conversation(
        self,
        speaker_tribe: Tribe,
        listener_tribe: Tribe,
        intent: str,
        context: str = "general",
    ) -> Dict[str, Any]:
        """Facilitate conversation between tribes"""

        speaker_lang = self.get_tribal_language(speaker_tribe)
        listener_lang = self.get_tribal_language(listener_tribe)

        # Generate tribal phrase
        tribal_phrase = speaker_lang.generate_tribal_phrase(intent, context)

        # Listener interprets the phrase
        interpretation = listener_lang.interpret_phrase(tribal_phrase, speaker_tribe)

        # Record in tribal memories
        speaker_tribe.add_tribal_memory(
            "communication_sent",
            {
                "to_tribe": listener_tribe.name,
                "phrase": tribal_phrase,
                "intent": intent,
                "context": context,
            },
        )

        listener_tribe.add_tribal_memory(
            "communication_received",
            {
                "from_tribe": speaker_tribe.name,
                "phrase": tribal_phrase,
                "interpreted_intent": interpretation["intent"],
                "confidence": interpretation["confidence"],
            },
        )

        return {
            "speaker_tribe": speaker_tribe.name,
            "listener_tribe": listener_tribe.name,
            "tribal_phrase": tribal_phrase,
            "intended_intent": intent,
            "interpreted_intent": interpretation["intent"],
            "success": interpretation["intent"] == intent,
            "confidence": interpretation["confidence"],
        }

    def broadcast_message(
        self, speaker_tribe: Tribe, intent: str, target_tribes: List[Tribe]
    ) -> List[Dict[str, Any]]:
        """Broadcast message to multiple tribes"""

        results = []
        for target_tribe in target_tribes:
            result = self.tribal_conversation(speaker_tribe, target_tribe, intent)
            results.append(result)

        return results

    def negotiate_with_tribe(
        self,
        initiating_tribe: Tribe,
        target_tribe: Tribe,
        negotiation_type: str,
    ) -> Dict[str, Any]:
        """Handle tribal negotiations"""

        intents = {
            "alliance": "alliance",
            "truce": "peace",
            "trade": "trade",
            "territory": "warning",  # Territory disputes use warnings
        }

        intent = intents.get(negotiation_type, "general")

        conversation_result = self.tribal_conversation(
            initiating_tribe, target_tribe, intent, "negotiation"
        )

        # Determine negotiation outcome based on tribal relationships and
        # communication success
        success_chance = conversation_result["confidence"]

        # Modify based on existing relationships
        if target_tribe.name in initiating_tribe.alliances:
            success_chance += 0.3
        elif target_tribe.name in initiating_tribe.rivalries:
            success_chance -= 0.3

        negotiation_success = random.random() < success_chance

        if negotiation_success:
            if negotiation_type == "alliance":
                initiating_tribe.form_alliance(target_tribe.name)
                target_tribe.form_alliance(initiating_tribe.name)
            elif negotiation_type == "truce":
                initiating_tribe.negotiate_truce(target_tribe.name)
                target_tribe.negotiate_truce(initiating_tribe.name)
            elif negotiation_type == "trade":
                # Trade agreements are handled separately
                pass

        return {
            **conversation_result,
            "negotiation_type": negotiation_type,
            "negotiation_success": negotiation_success,
            "outcome": "success" if negotiation_success else "failure",
        }

    def process_communication_turn(self, tribes: Dict[str, Tribe]) -> None:
        """Process communication dynamics between tribes"""
        from markov_behavior import make_markov_choice

        # Random chance for tribes to communicate with each other
        tribe_names = list(tribes.keys())

        for speaker_name in tribe_names:
            speaker_tribe = tribes[speaker_name]

            # Chance to communicate with other tribes
            for listener_name in tribe_names:
                if speaker_name != listener_name and random.random() < 0.05:  # 5% chance per turn
                    listener_tribe = tribes[listener_name]

                    # Determine communication intent based on relationship -
                    # use Markov choice
                    speaker_context = {
                        "traits": getattr(speaker_tribe, "traits", []),
                        # Default, could be refined based on actual
                        # relationship
                        "relationship": "neutral",
                        "trust_level": 0.5,
                        "recent_events": [],
                    }

                    if listener_name in speaker_tribe.alliances:
                        intent_options = ["greeting", "alliance", "trade"]
                        speaker_context["relationship"] = "ally"
                    elif listener_name in speaker_tribe.rivalries:
                        intent_options = ["warning", "threat"]
                        speaker_context["relationship"] = "enemy"
                    elif listener_name in speaker_tribe.truces:
                        intent_options = ["peace", "trade"]
                        speaker_context["relationship"] = "neutral"
                    else:
                        intent_options = ["greeting", "trade", "invitation"]
                        speaker_context["relationship"] = "unknown"

                    intent = make_markov_choice(
                        intent_options,
                        f"communication_{speaker_context['relationship']}",
                        "diplomatic",
                        speaker_context,
                    )

                    # Perform communication
                    result = self.tribal_conversation(speaker_tribe, listener_tribe, intent)

                    # Apply social consequences based on communication outcome
                    self._apply_communication_consequences(
                        speaker_tribe, listener_tribe, result, intent
                    )

                    # Log to communication log file in DM format
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with open("communication_log.txt", "a", encoding="utf-8") as comm_log:
                        if result["success"]:
                            comm_log.write(
                                f"[{timestamp}] 🗣️ {speaker_name} → "
                                f"{listener_name}: '{intent}' (✓ understood)\n"
                            )
                            comm_log.write(
                                f"[{timestamp}] 💬 {listener_name} "
                                f"acknowledges the message from "
                                f"{speaker_name}\n\n"
                            )
                        else:
                            comm_log.write(
                                f"[{timestamp}] 🗣️ {speaker_name} → "
                                f"{listener_name}: '"
                                f"{intent}' (✗ misunderstood as '"
                                f"{result['interpreted_intent']}')\n"
                            )
                            comm_log.write(
                                f"[{timestamp}] ❓ {listener_name} "
                                f"seems confused by {speaker_name}'s "
                                f"message\n\n"
                            )

    def _apply_communication_consequences(
        self,
        speaker_tribe: Tribe,
        listener_tribe: Tribe,
        result: Dict[str, Any],
        intent: str,
    ) -> None:
        """Apply social consequences based on communication outcomes."""
        # Map communication intents to social consequences
        consequence_mapping = {
            "greeting": ("successful_negotiation" if result["success"] else "failed_negotiation"),
            "alliance": "alliance_help" if result["success"] else "betrayal",
            "trade": ("successful_trade" if result["success"] else "failed_negotiation"),
            "warning": (
                "conflict" if result["success"] else None
            ),  # Warnings don't create consequences if misunderstood
            "threat": (
                "conflict" if result["success"] else "insult"
            ),  # Misunderstood threats become insults
            "invitation": "shared_achievement" if result["success"] else None,
            "peace": ("successful_negotiation" if result["success"] else "failed_negotiation"),
        }

        consequence_type = consequence_mapping.get(intent)

        if consequence_type and hasattr(speaker_tribe, "npcs") and hasattr(listener_tribe, "npcs"):
            # Get representative NPCs from each tribe
            speaker_npcs = speaker_tribe.npcs[:2] if speaker_tribe.npcs else []
            listener_npcs = listener_tribe.npcs[:2] if listener_tribe.npcs else []

            # Apply consequences between representative NPCs
            for speaker_npc in speaker_npcs:
                for listener_npc in listener_npcs:
                    if hasattr(speaker_npc, "add_social_memory"):
                        from communication import apply_social_consequence

                        apply_social_consequence(
                            speaker_npc,
                            listener_npc,
                            consequence_type,
                            details=f"tribal communication: {intent}",
                            topic="communication",
                        )
