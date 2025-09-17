import random

# Social consequence mapping - defines relationship impacts from interactions
SOCIAL_CONSEQUENCES = {
    "insult": {
        "impact": -0.3,
        "description": "verbal insult or offensive remark",
        "memory_duration": "long",
    },
    "betrayal": {
        "impact": -0.5,
        "description": "breaking an agreement or promise",
        "memory_duration": "very_long",
    },
    "successful_trade": {
        "impact": 0.2,
        "description": "successful resource exchange",
        "memory_duration": "medium",
    },
    "alliance_help": {
        "impact": 0.4,
        "description": "providing assistance in time of need",
        "memory_duration": "long",
    },
    "conflict": {
        "impact": -0.2,
        "description": "physical confrontation or dispute",
        "memory_duration": "medium",
    },
    "gift": {
        "impact": 0.15,
        "description": "giving a valuable item or resource",
        "memory_duration": "medium",
    },
    "deception": {
        "impact": -0.4,
        "description": "lying or misleading",
        "memory_duration": "long",
    },
    "successful_negotiation": {
        "impact": 0.25,
        "description": "reaching a favorable agreement",
        "memory_duration": "medium",
    },
    "failed_negotiation": {
        "impact": -0.1,
        "description": "failed attempt at agreement",
        "memory_duration": "short",
    },
    "shared_achievement": {
        "impact": 0.3,
        "description": "working together successfully",
        "memory_duration": "long",
    },
    # ===== EXPANDED INTERACTION TYPES =====
    "minor_disagreement": {
        "impact": -0.1,
        "description": "small argument or difference of opinion",
        "memory_duration": "short",
    },
    "resource_theft": {
        "impact": -0.4,
        "description": "stealing resources or goods",
        "memory_duration": "long",
    },
    "boundary_dispute": {
        "impact": -0.25,
        "description": "disagreement over territorial boundaries",
        "memory_duration": "medium",
    },
    "hunting_grounds_conflict": {
        "impact": -0.3,
        "description": "dispute over hunting or foraging rights",
        "memory_duration": "medium",
    },
    "cultural_offense": {
        "impact": -0.35,
        "description": "insulting cultural practices or beliefs",
        "memory_duration": "long",
    },
    "festival_invitation": {
        "impact": 0.2,
        "description": "inviting others to cultural celebration",
        "memory_duration": "medium",
    },
    "ceremony_participation": {
        "impact": 0.3,
        "description": "participating in another's cultural ritual",
        "memory_duration": "long",
    },
    "ritual_sharing": {
        "impact": 0.25,
        "description": "sharing cultural knowledge or traditions",
        "memory_duration": "long",
    },
    "leader_mediation": {
        "impact": 0.15,
        "description": "tribal leader helping resolve a dispute",
        "memory_duration": "medium",
    },
    "authority_challenge": {
        "impact": -0.2,
        "description": "questioning or challenging leadership authority",
        "memory_duration": "medium",
    },
}


def apply_social_consequence(speaker, listener, consequence_type, details=None, topic=None) -> None:
    """Apply a social consequence to both parties' memories."""
    if consequence_type not in SOCIAL_CONSEQUENCES:
        return

    consequence = SOCIAL_CONSEQUENCES[consequence_type]

    # Apply to speaker's memory (how they perceive their own action)
    speaker_impact = consequence["impact"]
    speaker.add_social_memory(consequence_type, listener.name, speaker_impact, details, topic)

    # Apply to listener's memory (how they perceive the speaker's action)
    listener_impact = consequence["impact"]
    # Listener's impact might be different based on their perspective
    if consequence_type in ["insult", "betrayal", "deception"]:
        listener_impact *= 1.2  # Victims remember negative actions more strongly
    elif consequence_type in ["alliance_help", "gift", "shared_achievement"]:
        listener_impact *= 0.8  # Recipients might undervalue positive actions

    listener.add_social_memory(consequence_type, speaker.name, listener_impact, details, topic)

    # Log the social consequence
    print(
        f"💭 Social consequence: {speaker.name} → {listener.name} ({consequence_type}, impact: {speaker_impact:.2f})"
    )


def get_conversation_tone_modifier(speaker, listener) -> str:
    """Get tone modifier based on social history."""
    relationship = speaker.get_relationship_with(listener.name)

    if relationship > 0.3:
        return "warm"
    elif relationship < -0.3:
        return "tense"
    else:
        return "neutral"


class NPC:
    def __init__(self, name, faction):
        self.name = name
        self.faction = faction
        # Add personality traits
        self.personality = random.choice(
            ["gruff", "friendly", "mysterious", "wise", "aggressive", "curious"]
        )
        # Add memory for conversation continuity
        self.memory = []
        # Add current mood
        self.mood = random.choice(["calm", "excited", "worried", "confident", "suspicious"])
        # Add conversation memory for remembering details
        self.conversation_memory = {
            "mentioned_locations": set(),
            "mentioned_resources": set(),
            "mentioned_events": set(),
            "mentioned_activities": set(),
            "shared_context": {},
            "relationship_history": {},
        }
        # Add social memory for tracking interaction consequences
        self.social_memory = []  # List of dicts with interaction consequences
        self.relationship_scores = {}  # Track relationship scores with other NPCs

        # Add social hierarchy and leadership influence
        self.social_influence = random.uniform(0.1, 1.0)  # Base influence level (0-1)
        self.leadership_role = None  # Will be set by tribal system
        self.faction_loyalty = random.uniform(0.5, 1.0)  # How loyal to faction (0-1)
        self.decision_influence = 0.0  # How much this NPC influences group decisions

    def add_social_memory(
        self, interaction_type, target_name, consequence_value, details=None, topic=None
    ) -> None:
        """Add a social interaction to memory with its consequences."""
        memory_entry = {
            "type": interaction_type,
            "target": target_name,
            "consequence": consequence_value,  # Positive for good interactions, negative for bad
            "details": details,
            "topic": topic,
            "timestamp": random.randint(1, 100),  # Simple timestamp for decay
        }

        self.social_memory.append(memory_entry)

        # Keep only recent memories (last 10)
        if len(self.social_memory) > 10:
            self.social_memory.pop(0)

        # Update relationship score
        if target_name not in self.relationship_scores:
            self.relationship_scores[target_name] = 0.0

        self.relationship_scores[target_name] += consequence_value
        self.relationship_scores[target_name] = max(
            -1.0, min(1.0, self.relationship_scores[target_name])
        )

    def get_relationship_with(self, target_name) -> float:
        """Get the current relationship score with another NPC."""
        return self.relationship_scores.get(target_name, 0.0)

    def decay_social_memory(self) -> None:
        """Decay old social memories over time."""
        current_time = random.randint(1, 100)

        # Remove very old memories and decay recent ones
        decayed_memory = []
        for memory in self.social_memory:
            age = current_time - memory["timestamp"]
            if age > 50:  # Very old memory
                continue
            elif age > 20:  # Old memory - reduce consequence impact
                memory["consequence"] *= 0.7

            decayed_memory.append(memory)

        self.social_memory = decayed_memory

        # Also decay relationship scores slightly
        for target in list(self.relationship_scores.keys()):
            self.relationship_scores[target] *= 0.95
            if abs(self.relationship_scores[target]) < 0.01:
                del self.relationship_scores[target]

    def get_social_context_modifier(self, target_name) -> str:
        """Get a modifier for dialogue based on social history."""
        relationship = self.get_relationship_with(target_name)

        if relationship > 0.5:
            return "warm"
        elif relationship > 0.2:
            return "friendly"
        elif relationship < -0.5:
            return "cold"
        elif relationship < -0.2:
            return "hostile"
        else:
            return "neutral"

    def set_leadership_role(self, role, influence_multiplier=1.0) -> None:
        """Set this NPC's leadership role and calculate influence."""
        self.leadership_role = role
        if role == "leader":
            self.decision_influence = self.social_influence * 2.0 * influence_multiplier
        elif role == "shaman":
            self.decision_influence = self.social_influence * 1.8 * influence_multiplier
        elif role == "elder":
            self.decision_influence = self.social_influence * 1.5 * influence_multiplier
        elif role == "warrior_captain":
            self.decision_influence = self.social_influence * 1.3 * influence_multiplier
        else:
            self.decision_influence = self.social_influence * influence_multiplier

    def get_decision_weight(self, decision_type="general") -> float:
        """Get this NPC's influence weight in group decisions."""
        base_weight = self.decision_influence

        # Adjust based on decision type and personality
        if decision_type == "diplomatic" and self.personality in ["wise", "friendly"]:
            base_weight *= 1.3
        elif decision_type == "military" and self.personality in [
            "aggressive",
            "gruff",
        ]:
            base_weight *= 1.2
        elif decision_type == "economic" and self.personality in ["wise", "mysterious"]:
            base_weight *= 1.1

        return base_weight

    def influence_faction_decision(self, decision_type, current_opinion, faction_members) -> float:
        """Apply leadership influence to a faction decision."""
        if not self.leadership_role or self.decision_influence < 0.3:
            return current_opinion

        influence_strength = self.get_decision_weight(decision_type)
        personal_bias = 0.0

        # Leaders have biases based on their personality and role
        if self.leadership_role == "leader":
            if decision_type == "diplomatic":
                personal_bias = 0.2 if self.personality == "wise" else -0.1
            elif decision_type == "military":
                personal_bias = 0.1 if self.personality == "aggressive" else -0.2
        elif self.leadership_role == "shaman":
            if decision_type == "cultural":
                personal_bias = 0.3
            elif decision_type == "diplomatic":
                personal_bias = 0.1

        # Apply influence based on faction loyalty
        total_influence = influence_strength * self.faction_loyalty * (1 + personal_bias)

        # Blend with current opinion
        influenced_opinion = (
            current_opinion * (1 - total_influence) + personal_bias * total_influence
        )

        return max(-1.0, min(1.0, influenced_opinion))


# Enhanced pools with more variety and theming
resources = [
    "iron ore",
    "ancient wood",
    "gold nuggets",
    "fresh game",
    "crystalline stone",
    "woven cloth",
    "healing herbs",
    "enchanted crystals",
]
locations = [
    "Riverholt",
    "Mountain Pass",
    "Forest Clearing",
    "Village Square",
    "Castle Ruins",
    "Market Town",
    "Crystal Caves",
    "Shadow Grove",
    "Sunlit Meadow",
]
events = [
    "harvest festival",
    "midnight raid",
    "grand festival",
    "merchant caravan",
    "terrible storm",
    "epic battle",
    "mysterious eclipse",
    "ancient ritual",
]
activities = [
    "mining",
    "farming",
    "hunting",
    "trading",
    "patrol",
    "crafting",
    "gathering herbs",
    "exploring ruins",
]

# Personality modifiers for dialogue - relationship and tone aware
personality_modifiers = {
    "gruff": {
        "friendly": ["Hmph.", "Well then.", "Fair enough."],
        "neutral": ["Hmph.", "Get to the point.", "Don't waste my time."],
        "hostile": ["Hmph.", "Get to the point.", "Don't waste my time."],
    },
    "friendly": {
        "friendly": ["Great to see you!", "How wonderful!", "I'm glad you're here."],
        "neutral": ["Hello there.", "How are you?", "Nice to meet you."],
        "hostile": ["Well, if I must.", "Very well.", "As you wish."],
    },
    "mysterious": {
        "friendly": [
            "The shadows whisper...",
            "Ancient secrets reveal...",
            "The winds carry tales...",
        ],
        "neutral": [
            "The shadows whisper...",
            "Ancient secrets reveal...",
            "The winds carry tales...",
        ],
        "hostile": [
            "The shadows whisper...",
            "Ancient secrets reveal...",
            "The winds carry tales...",
        ],
    },
    "wise": {
        "friendly": [
            "Ah, the wisdom of ages...",
            "Listen well, young one...",
            "The elders speak of...",
        ],
        "neutral": [
            "Ah, the wisdom of ages...",
            "Listen well, young one...",
            "The elders speak of...",
        ],
        "hostile": [
            "Ah, the wisdom of ages...",
            "Listen well, young one...",
            "The elders speak of...",
        ],
    },
    "aggressive": {
        "friendly": ["Hey there!", "Listen up!", "Pay attention!"],
        "neutral": [
            "I understand.",
            "Let's discuss this.",
            "I see your point.",
        ],  # Diplomatic override for trade
        "hostile": ["Watch yourself!", "Don't test me!", "Back down now!"],
    },
    "curious": {
        "friendly": ["Tell me more...", "How fascinating...", "I must know..."],
        "neutral": ["Tell me more...", "How fascinating...", "I must know..."],
        "hostile": ["Tell me more...", "How fascinating...", "I must know..."],
    },
}

# Faction-specific dialogue templates
faction_templates = {
    "Wildlife": {
        "friendly": [
            "The forest whispers of {event} near {location}.",
            "Have you tasted the {resource} from {location}?",
            "The herd moves with the {activity} season.",
            "Our territory grows with each {event}.",
            "The herd migrates to follow the ancient paths.",
            "We migrate with the changing seasons.",
            "I feel the herd stirring... we should move soon.",
            "The old trails are calling us northward.",
            "Our people have always followed the migrations.",
            "The seasons change, and so must we.",
            "Have you heard the migration calls?",
            "The herd gathers for the great journey.",
        ],
        "neutral": [
            "Perhaps we can find common ground.",
            "There might be room for cooperation.",
            "Let's discuss terms of peace.",
            "A truce could benefit us both.",
            "Trade might serve our interests.",
            "We could work together for mutual gain.",
            "Perhaps an alliance is possible.",
            "Let's negotiate a fair agreement.",
            "I propose a temporary ceasefire.",
            "We should establish peaceful relations.",
            "Mutual respect could serve us well.",
            "Let's explore possibilities for cooperation.",
        ],
        "hostile": [
            "Your kind disrupts the natural order!",
            "Leave our sacred {location} be!",
            "The wild rejects your presence!",
            "You bring imbalance to these lands!",
        ],
    },
    "Predators": {
        "friendly": [
            "The hunt was good at {location} today.",
            "Fresh {resource} makes for a fine meal.",
            "Our territory expands with each victory.",
            "The weak feed the strong - that's nature's way.",
        ],
        "neutral": [
            "Every creature has its place in the hunt.",
            "Strength respects strength.",
            "The pack watches your movements.",
            "Caution serves the wise hunter.",
            "Perhaps we can avoid unnecessary conflict.",
            "A temporary truce might be wise.",
            "Trade could strengthen both our positions.",
            "Let's establish hunting boundaries.",
            "We could share hunting grounds peacefully.",
            "An alliance of strength could be formed.",
            "I respect your strength.",
            "Let's find a way to coexist.",
            "Your skills are impressive.",
            "We could learn from each other.",
        ],
        "hostile": [
            "Your scent betrays your weakness!",
            "This territory belongs to the strong!",
            "Feel the predator's gaze upon you!",
            "The hunt begins now!",
            "Your weakness angers the pack!",
            "The strong take what they want!",
            "I can smell your fear from here.",
            "The hunt is upon you!",
            "Your time has come, prey.",
            "The pack grows hungry for your kind.",
            "You won't escape the hunt this time.",
            "The predator claims what it desires.",
            "Your weakness is an invitation to the hunt.",
            "The chase begins with your terror.",
        ],
    },
    "Pioneers": {
        "friendly": [
            "We've built something special here at {location}.",
            "The {resource} trade is booming!",
            "Our {activity} techniques are improving daily.",
            "Together we can tame these wild lands.",
            "We must build a better future here.",
            "Construction begins on our new outpost.",
            "I think it's time we expanded our settlement.",
            "The foundation for the new workshop is ready.",
            "Our builders are eager to start the next project.",
            "We could really use a proper storage facility.",
            "The watchtower will give us early warning.",
            "Let's put our skills to work on something grand.",
            "The trading post will bring prosperity to all.",
            "I have plans for a magnificent structure.",
        ],
        "neutral": [
            "Progress requires cooperation from all.",
            "Knowledge is our greatest tool.",
            "The frontier tests everyone's resolve.",
            "Innovation drives us forward.",
            "Perhaps we can establish trade routes.",
            "A truce would allow peaceful development.",
            "Let's discuss mutual protection.",
            "We could share technological knowledge.",
            "An alliance would benefit both our peoples.",
            "Let's negotiate fair terms.",
            "Your ingenuity is remarkable.",
            "Together we could achieve more.",
            "I value your perspective.",
            "Let's build something together.",
        ],
        "hostile": [
            "Your barbaric ways threaten our progress!",
            "Stay out of our established territories!",
            "Civilization will not be stopped!",
            "Your kind brings only chaos!",
        ],
    },
}

# Context types for different conversation scenarios
context_types = ["casual", "trade", "combat", "exploration", "social", "urgent"]

# Conversation tones that affect response style
conversation_tones = {
    "cooperative": {
        "response_bias": ["agreement", "acknowledgment", "follow_up"],
        "word_multipliers": {
            "together": 2.0,
            "help": 2.0,
            "share": 2.0,
            "work": 2.0,
            "alliance": 2.0,
            "mutual": 2.0,
            "benefit": 2.0,
        },
        "avoid_words": ["fight", "against", "enemy", "threat"],
    },
    "competitive": {
        "response_bias": ["disagreement", "direct_answer", "explanation"],
        "word_multipliers": {
            "better": 2.0,
            "stronger": 2.0,
            "superior": 2.0,
            "advantage": 2.0,
            "challenge": 2.0,
            "compete": 2.0,
            "win": 2.0,
        },
        "avoid_words": ["help", "together", "share", "weak"],
    },
    "neutral": {
        "response_bias": ["acknowledgment", "follow_up", "direct_answer"],
        "word_multipliers": {
            "understand": 1.5,
            "consider": 1.5,
            "perhaps": 1.5,
            "maybe": 1.5,
            "interesting": 1.5,
            "noted": 1.5,
            "see": 1.5,
        },
        "avoid_words": ["fight", "threat", "enemy", "hate"],
    },
    "hostile": {
        "response_bias": ["disagreement", "direct_answer"],
        "word_multipliers": {
            "threat": 2.0,
            "danger": 2.0,
            "enemy": 2.0,
            "destroy": 2.0,
            "fight": 2.0,
            "against": 2.0,
            "weakness": 2.0,
        },
        "avoid_words": ["help", "peace", "together", "friend"],
    },
    "diplomatic": {
        "response_bias": ["acknowledgment", "follow_up", "agreement"],
        "word_multipliers": {
            "together": 2.0,
            "peace": 2.0,
            "cooperation": 2.0,
            "alliance": 2.0,
            "negotiate": 2.0,
            "compromise": 2.0,
            "mutual": 2.0,
            "benefit": 2.0,
        },
        "avoid_words": ["fight", "threat", "enemy", "weakness"],
    },
}


def should_talk(npc1, npc2) -> bool:
    """
    Determines if two NPCs should engage in conversation.
    For now, always returns True, but can be extended with distance, mood, etc.
    """
    return True


def generate_memory_driven_line(speaker, listener, context="casual") -> str:
    """
    Generate dialogue that references past events or actions from memory
    """
    relationship = get_relationship_type(speaker, listener)

    # Override relationship for diplomatic contexts
    effective_relationship = relationship
    if context in ["trade", "diplomatic"]:
        if relationship == "hostile":
            effective_relationship = (
                "neutral"  # Use diplomatic language for trade/diplomatic contexts
            )

    # Check if speaker has any memory of recent events
    if (
        not speaker.conversation_memory["mentioned_events"]
        and not speaker.conversation_memory["mentioned_locations"]
    ):
        return None  # No memory to reference

    # Select a random event or location from memory
    memory_events = list(speaker.conversation_memory["mentioned_events"])
    memory_locations = list(speaker.conversation_memory["mentioned_locations"])
    memory_resources = list(speaker.conversation_memory["mentioned_resources"])

    memory_references = []
    if memory_events:
        memory_references.extend([f"Remember that {event}?" for event in memory_events[:2]])
    if memory_locations:
        memory_references.extend([f"What about {location}?" for location in memory_locations[:2]])
    if memory_resources:
        memory_references.extend(
            [f"Those {resource} we found..." for resource in memory_resources[:2]]
        )

    if not memory_references:
        return None

    memory_prompt = random.choice(memory_references)

    # Create memory-driven dialogue based on faction
    memory_templates = {
        "Wildlife": {
            "friendly": [
                f"{memory_prompt} The herd still talks about it.",
                f"{memory_prompt} Our ancestors would be proud.",
                f"{memory_prompt} The forest remembers everything.",
                f"{memory_prompt} That's when we learned our true strength.",
            ],
            "neutral": [
                f"{memory_prompt} Nature has its own way.",
                f"{memory_prompt} The wild teaches us all.",
                f"{memory_prompt} Balance must be maintained.",
            ],
            "hostile": [
                f"{memory_prompt} You outsiders don't understand.",
                f"{memory_prompt} Your kind disrupted everything.",
                f"{memory_prompt} The wild rejects your presence.",
            ],
        },
        "Predators": {
            "friendly": [
                f"{memory_prompt} The pack still hunts those memories.",
                f"{memory_prompt} That was a fine chase.",
                f"{memory_prompt} Strength was proven that day.",
            ],
            "neutral": [
                f"{memory_prompt} Every hunter learns from experience.",
                f"{memory_prompt} The hunt teaches respect.",
                f"{memory_prompt} Survival demands adaptation.",
            ],
            "hostile": [
                f"{memory_prompt} Your weakness was exposed then.",
                f"{memory_prompt} The predator always wins.",
                f"{memory_prompt} You were lucky to escape.",
            ],
        },
        "Pioneers": {
            "friendly": [
                f"{memory_prompt} Our settlement grew stronger after that.",
                f"{memory_prompt} Progress requires remembering the past.",
                f"{memory_prompt} We've learned so much since then.",
            ],
            "neutral": [
                f"{memory_prompt} Innovation builds on experience.",
                f"{memory_prompt} Knowledge is our greatest tool.",
                f"{memory_prompt} The frontier tests us all.",
            ],
            "hostile": [
                f"{memory_prompt} Your kind brought only chaos.",
                f"{memory_prompt} Civilization will prevail.",
                f"{memory_prompt} We build despite your interference.",
            ],
        },
    }

    faction_templates_memory = memory_templates.get(speaker.faction, memory_templates["Wildlife"])
    templates = faction_templates_memory[effective_relationship]

    # Add personality modifier
    personality_prefix = ""
    if random.random() < 0.3:
        personality_prefix = (
            random.choice(personality_modifiers[speaker.personality][effective_relationship]) + " "
        )

    return personality_prefix + random.choice(templates)


def commence_hunt(predator, target) -> None:
    """
    Trigger a hunt event when a predator declares "the hunt begins now"
    """
    print("\n🐺 *** THE HUNT BEGINS! *** 🐺")
    print(f"{predator.name} ({predator.faction}) has initiated a hunt!")

    # Determine hunt success based on various factors
    predator_bonus = 1.5 if predator.personality == "aggressive" else 1.0
    target_bonus = 1.2 if target.faction == "Wildlife" else 1.0

    hunt_success_chance = 0.6 * predator_bonus / target_bonus

    if random.random() < hunt_success_chance:
        print(f"🎯 {predator.name} successfully hunts {target.name}!")
        print("The predator claims victory in the wild.")

        # Hunt yields resources
        resources_gained = random.choice(["fresh game", "enchanted crystals", "healing herbs"])
        print(f"🏆 {predator.name} obtains: {resources_gained}")

        # Store in predator's memory
        predator.conversation_memory["mentioned_resources"].add(resources_gained)

        # Chance for target faction to respond
        if target.faction == "Wildlife" and random.random() < 0.4:
            print("🌿 Wildlife faction notices the hunt! Tensions rise...")
            # Could trigger migration or retaliation

        # Post-hunt dialogue
        if random.random() < 0.6:
            hunt_comments = [
                f"{predator.name} licks their chops. 'That was a fine hunt!'",
                f"{predator.name} howls in triumph. 'The pack will eat well tonight!'",
                f"{predator.name} examines the prize. 'Strength prevails once more.'",
            ]
            print(f"  {random.choice(hunt_comments)}")

    else:
        print(f"❌ {target.name} evades the hunt!")
        print("The prey escapes into the wilderness.")

        # Failed hunt might anger the predator
        if random.random() < 0.3:
            print(f"😠 {predator.name} grows frustrated by the failed hunt!")

        # Post-failed hunt dialogue
        if random.random() < 0.5:
            failed_comments = [
                f"{predator.name} snarls. 'You'll not escape next time!'",
                f"{predator.name} paces angrily. 'The hunt continues...'",
                f"{predator.name} glares. 'Your luck won't hold forever.'",
            ]
            print(f"  {random.choice(failed_comments)}")

    print("*** HUNT CONCLUDED ***\n")


def commence_migration(wildlife, target) -> None:
    """
    Trigger a migration event when wildlife declares migration
    """
    print("\n🦌 *** HERD MIGRATION BEGINS! *** 🦌")
    print(f"{wildlife.name} ({wildlife.faction}) calls for the herd to migrate!")

    migration_destinations = [
        "Mountain Pass",
        "Forest Clearing",
        "Crystal Caves",
        "Sunlit Meadow",
    ]
    destination = random.choice(migration_destinations)

    print(f"🏔️ The herd migrates toward {destination}")

    # Migration benefits
    if random.random() < 0.7:
        print(f"✨ Migration successful! The herd discovers new resources at {destination}")
        resources_found = random.choice(["ancient wood", "healing herbs", "crystalline stone"])
        print(f"🎁 Resources discovered: {resources_found}")

        # Store in wildlife's memory
        wildlife.conversation_memory["mentioned_resources"].add(resources_found)
        wildlife.conversation_memory["mentioned_locations"].add(destination)

        # Success dialogue
        if random.random() < 0.6:
            success_comments = [
                f"{wildlife.name} calls out joyfully. 'The journey was worth it!'",
                f"{wildlife.name} scents the new resources. 'The herd will thrive here.'",
                f"{wildlife.name} stands tall. 'Our ancestors guide us well.'",
            ]
            print(f"  {random.choice(success_comments)}")
    else:
        print("⚠️ Migration encounters difficulties...")

        # Failure dialogue
        if random.random() < 0.5:
            failure_comments = [
                f"{wildlife.name} looks weary. 'The path was harder than expected.'",
                f"{wildlife.name} shakes their head. 'We must rest and recover.'",
                f"{wildlife.name} calls to the herd. 'Stay strong, we continue forward.'",
            ]
            print(f"  {random.choice(failure_comments)}")

    print("*** MIGRATION CONCLUDED ***\n")


def commence_construction(pioneer, target) -> None:
    """
    Trigger a construction event when pioneers declare building
    """
    print("\n🏗️ *** CONSTRUCTION BEGINS! *** 🏗️")
    print(f"{pioneer.name} ({pioneer.faction}) initiates construction!")

    structures = ["trading post", "watchtower", "workshop", "storage facility"]
    structure = random.choice(structures)

    print(f"🔨 Building a {structure}...")

    # Construction success based on personality
    success_bonus = 1.3 if pioneer.personality == "wise" else 1.0

    if random.random() < 0.8 * success_bonus:
        print(f"✅ Construction completed! {structure.title()} established.")
        print("📈 Pioneer influence grows in the region.")

        # Store construction in memory
        pioneer.conversation_memory["mentioned_activities"].add("crafting")
        pioneer.conversation_memory["mentioned_locations"].add("established territories")

        # Success dialogue
        if random.random() < 0.7:
            success_comments = [
                f"{pioneer.name} beams with pride. 'Another triumph for progress!'",
                f"{pioneer.name} wipes sweat from their brow. 'Well worth the effort.'",
                f"{pioneer.name} admires the work. 'This will serve us well.'",
            ]
            print(f"  {random.choice(success_comments)}")
    else:
        print("❌ Construction delayed due to complications...")

        # Failure dialogue
        if random.random() < 0.6:
            failure_comments = [
                f"{pioneer.name} frowns. 'We'll overcome this setback.'",
                f"{pioneer.name} studies the problem. 'A minor delay, nothing more.'",
                f"{pioneer.name} rallies the workers. 'We adapt and continue!'",
            ]
            print(f"  {random.choice(failure_comments)}")

    print("*** CONSTRUCTION CONCLUDED ***\n")


def commence_summoning(wildlife, target) -> None:
    """
    Trigger a summoning event when wildlife call upon dark powers
    """
    print("\n🌑 *** DARK SUMMONING BEGINS! *** 🌑")
    print(f"{wildlife.name} ({wildlife.faction}) channels ancient powers!")

    summons = ["shadow beasts", "ancient guardians", "dark spirits", "void entities"]
    summon = random.choice(summons)

    print(f"🌀 Summoning {summon} from the darkness...")

    # Summoning success based on personality
    success_bonus = 1.4 if wildlife.personality == "mysterious" else 1.0

    if random.random() < 0.7 * success_bonus:
        print(f"🎭 Summoning successful! {summon.title()} appear.")
        print("😱 The land grows darker with their presence.")

        # Store summoning in memory
        wildlife.conversation_memory["mentioned_events"].add("ancient ritual")
        wildlife.conversation_memory["mentioned_activities"].add("exploring ruins")

        # Success dialogue
        if random.random() < 0.6:
            success_comments = [
                f"{wildlife.name} laughs darkly. 'The ancient ones answer!'",
                f"{wildlife.name} bows reverently. 'Power flows through us.'",
                f"{wildlife.name} whispers to the shadows. 'Welcome, brethren.'",
            ]
            print(f"  {random.choice(success_comments)}")
    else:
        print("💥 Summoning backfires! Dark energies recoil...")

        # Failure dialogue
        if random.random() < 0.5:
            failure_comments = [
                f"{wildlife.name} staggers. 'The power... too unstable!'",
                f"{wildlife.name} growls. 'The ritual needs refinement.'",
                f"{wildlife.name} regains composure. 'Next time will be different.'",
            ]
            print(f"  {random.choice(failure_comments)}")

    print("*** SUMMONING CONCLUDED ***\n")


def negotiate_truce(speaker, listener) -> str:
    """
    Negotiate a temporary truce between potentially hostile factions
    """
    print("\n🤝 *** TRUCE NEGOTIATIONS BEGIN! *** 🤝")
    print(
        f"{speaker.name} ({speaker.faction}) proposes terms of peace to {listener.name} ({listener.faction})"
    )

    # Truce success depends on personalities and current relationship
    relationship = get_relationship_type(speaker, listener)

    # Diplomatic personalities have better success rates
    speaker_bonus = 1.3 if speaker.personality in ["wise", "friendly"] else 1.0
    listener_bonus = 1.2 if listener.personality in ["wise", "friendly"] else 1.0

    # Hostile relationships are harder to truce with
    relationship_modifier = 0.5 if relationship == "hostile" else 1.0

    truce_success = 0.6 * speaker_bonus * listener_bonus * relationship_modifier

    if random.random() < truce_success:
        truce_duration = random.randint(3, 8)  # 3-8 conversation turns
        print(f"✅ Truce agreed! Peace established for {truce_duration} encounters.")
        print("⚔️ Hostilities temporarily suspended between the factions.")

        # Store truce in both NPCs' memory
        speaker.conversation_memory["mentioned_events"].add("truce_agreed")
        listener.conversation_memory["mentioned_events"].add("truce_agreed")

        # Update relationship history
        speaker.conversation_memory["relationship_history"][listener.name] = "truce"
        listener.conversation_memory["relationship_history"][speaker.name] = "truce"

        # Success dialogue
        if random.random() < 0.7:
            success_comments = [
                f"{speaker.name} nods solemnly. 'Let peace reign for now.'",
                f"{listener.name} extends a hand. 'Agreed, for the time being.'",
                f"{speaker.name} smiles cautiously. 'Wisdom prevails today.'",
            ]
            print(f"  {random.choice(success_comments)}")
    else:
        print("❌ Truce negotiations fail! Terms cannot be agreed upon.")

        # Failure dialogue
        if random.random() < 0.6:
            failure_comments = [
                f"{listener.name} shakes their head. 'The terms are unacceptable.'",
                f"{speaker.name} sighs. 'Perhaps another time.'",
                f"{listener.name} stands firm. 'Trust must be earned.'",
            ]
            print(f"  {random.choice(failure_comments)}")

    print("*** NEGOTIATIONS CONCLUDED ***\n")


def negotiate_trade_agreement(speaker, listener) -> str:
    """
    Negotiate a trade agreement for mutual economic benefit
    """
    print("\n💰 *** TRADE NEGOTIATIONS BEGIN! *** 💰")
    print(
        f"{speaker.name} ({speaker.faction}) proposes trade terms with {listener.name} ({listener.faction})"
    )

    # Trade success depends on faction compatibility and personalities

    # Pioneers are natural traders
    faction_bonus = 1.4 if "Pioneer" in [speaker.faction, listener.faction] else 1.0

    # Diplomatic personalities excel at trade
    personality_bonus = (
        1.2 if any(npc.personality in ["wise", "friendly"] for npc in [speaker, listener]) else 1.0
    )

    trade_success = 0.7 * faction_bonus * personality_bonus

    if random.random() < trade_success:
        trade_resources = random.choice(
            [
                ["iron ore", "woven cloth"],
                ["healing herbs", "enchanted crystals"],
                ["fresh game", "gold nuggets"],
                ["ancient wood", "crystalline stone"],
            ]
        )

        print(
            f"✅ Trade agreement reached! Mutual exchange of {trade_resources[0]} and {trade_resources[1]} established."
        )
        print("📈 Both factions gain economic benefits from the partnership.")

        # Store trade agreement in memory
        speaker.conversation_memory["mentioned_events"].add("trade_agreement")
        speaker.conversation_memory["mentioned_resources"].update(trade_resources)

        listener.conversation_memory["mentioned_events"].add("trade_agreement")
        listener.conversation_memory["mentioned_resources"].update(trade_resources)

        # Update relationship history
        speaker.conversation_memory["relationship_history"][listener.name] = "trade_partner"
        listener.conversation_memory["relationship_history"][speaker.name] = "trade_partner"

        # Success dialogue
        if random.random() < 0.7:
            success_comments = [
                f"{speaker.name} grins. 'Prosperity awaits us both!'",
                f"{listener.name} nods approvingly. 'A wise arrangement.'",
                f"{speaker.name} raises a toast. 'To profitable partnerships!'",
            ]
            print(f"  {random.choice(success_comments)}")
    else:
        print("❌ Trade negotiations fail! Terms cannot be mutually agreed upon.")

        # Failure dialogue
        if random.random() < 0.6:
            failure_comments = [
                f"{listener.name} counters. 'Your terms are too steep.'",
                f"{speaker.name} frowns. 'We can do better than this.'",
                f"{listener.name} hesitates. 'The risks outweigh the rewards.'",
            ]
            print(f"  {random.choice(failure_comments)}")

    print("*** TRADE NEGOTIATIONS CONCLUDED ***\n")


def form_alliance(speaker, listener) -> str:
    """
    Form a lasting alliance between factions
    """
    print("\n⚔️ *** ALLIANCE NEGOTIATIONS BEGIN! *** ⚔️")
    print(
        f"{speaker.name} ({speaker.faction}) proposes an alliance with {listener.name} ({listener.faction})"
    )

    # Alliance success is rare and requires strong diplomatic skills
    relationship = get_relationship_type(speaker, listener)

    # Only possible between compatible factions or with diplomatic personalities
    compatibility_bonus = 1.5 if relationship in ["neutral", "friendly"] else 0.3

    # Wise personalities are key to alliances
    diplomacy_bonus = 1.8 if all(npc.personality == "wise" for npc in [speaker, listener]) else 1.0

    alliance_success = 0.4 * compatibility_bonus * diplomacy_bonus

    if random.random() < alliance_success:
        alliance_type = random.choice(
            [
                "Defensive Alliance - Mutual protection against threats",
                "Economic Alliance - Shared resources and trade routes",
                "Exploratory Alliance - Joint expeditions and discoveries",
                "Cultural Alliance - Exchange of knowledge and traditions",
            ]
        )

        print(f"🎉 Alliance formed! {alliance_type}")
        print("🤝 The factions are now bound by treaty and mutual obligation.")

        # Store alliance in memory
        speaker.conversation_memory["mentioned_events"].add("alliance_formed")
        listener.conversation_memory["mentioned_events"].add("alliance_formed")

        # Update relationship history
        speaker.conversation_memory["relationship_history"][listener.name] = "ally"
        listener.conversation_memory["relationship_history"][speaker.name] = "ally"

        # Success dialogue
        if random.random() < 0.8:
            success_comments = [
                f"{speaker.name} speaks solemnly. 'Our peoples are united!'",
                f"{listener.name} bows deeply. 'An honor to stand with you.'",
                f"{speaker.name} raises their voice. 'Let history remember this day!'",
            ]
            print(f"  {random.choice(success_comments)}")
    else:
        print("❌ Alliance negotiations fail! Distrust and differences prove too great.")

        # Failure dialogue
        if random.random() < 0.6:
            failure_comments = [
                f"{listener.name} shakes their head. 'The time is not right.'",
                f"{speaker.name} sighs. 'Perhaps in another era.'",
                f"{listener.name} stands firm. 'Some wounds run too deep.'",
            ]
            print(f"  {random.choice(failure_comments)}")

    print("*** ALLIANCE NEGOTIATIONS CONCLUDED ***\n")


def get_relationship_type(npc1, npc2) -> str:
    """Determine relationship type based on factions"""
    if npc1.faction == npc2.faction:
        return "friendly"
    elif (
        npc1.faction in ["Wildlife", "Pioneers"] and npc2.faction in ["Wildlife", "Pioneers"]
    ) or (npc1.faction in ["Predators", "Wildlife"] and npc2.faction in ["Predators", "Wildlife"]):
        return "neutral"  # Similar faction types
    else:
        return "hostile"


def generate_line(speaker, listener, context="casual") -> str:
    """
    Generates a more sophisticated line of dialogue with personality and context.
    """
    relationship = get_relationship_type(speaker, listener)

    # Get social context modifier
    social_modifier = speaker.get_social_context_modifier(listener.name)

    # Override relationship for diplomatic contexts
    effective_relationship = relationship
    if context in ["trade", "diplomatic"]:
        if relationship == "hostile":
            effective_relationship = (
                "neutral"  # Use diplomatic language for trade/diplomatic contexts
            )

    # Adjust effective relationship based on social history
    if social_modifier == "warm" and effective_relationship == "neutral":
        effective_relationship = "friendly"
    elif social_modifier == "cold" and effective_relationship == "neutral":
        effective_relationship = "hostile"

    # Get faction-specific templates
    faction_templates_speaker = faction_templates.get(
        speaker.faction, faction_templates["Wildlife"]
    )
    templates = faction_templates_speaker[effective_relationship]

    # Select base template
    template = random.choice(templates)

    # Add personality modifier sometimes
    personality_prefix = ""
    if random.random() < 0.3:  # 30% chance
        personality_prefix = (
            random.choice(personality_modifiers[speaker.personality][effective_relationship]) + " "
        )

    # Format the template
    line = template.format(
        other=listener.name,
        resource=random.choice(resources),
        location=random.choice(locations),
        event=random.choice(events),
        activity=random.choice(activities),
    )

    # Add context-specific elements
    if context == "trade":
        trade_phrases = [
            "Speaking of trade...",
            "On the matter of commerce...",
            "Business before pleasure...",
        ]
        line = random.choice(trade_phrases) + " " + line
    elif context == "combat":
        combat_phrases = [
            "After that skirmish...",
            "The battle taught us...",
            "Victory demands...",
        ]
        line = random.choice(combat_phrases) + " " + line
    elif context == "urgent":
        urgent_phrases = ["Listen carefully!", "This is important!", "Pay attention!"]
        line = random.choice(urgent_phrases) + " " + line

    # Add social memory reference sometimes (if relationship is strong)
    if random.random() < 0.2 and abs(speaker.get_relationship_with(listener.name)) > 0.3:
        memory_line = generate_memory_driven_line(speaker, listener, context)
        if memory_line:
            line = memory_line

    # Store in memory for continuity
    speaker.memory.append(line)
    if len(speaker.memory) > 5:  # Keep only last 5 lines
        speaker.memory.pop(0)

    return personality_prefix + line


def generate_response(
    speaker,
    listener,
    previous_line,
    context="casual",
    conversation_history=None,
    tone="neutral",
) -> str:
    """
    Generates a response that remembers conversation details and adapts to tone.
    """
    if conversation_history is None:
        conversation_history = []

    relationship = get_relationship_type(speaker, listener)

    # Get social context modifier
    social_modifier = speaker.get_social_context_modifier(listener.name)

    # Override relationship for diplomatic contexts
    effective_relationship = relationship
    if context in ["trade", "diplomatic"] and tone in [
        "diplomatic",
        "neutral",
        "cooperative",
    ]:
        if relationship == "hostile":
            effective_relationship = (
                "neutral"  # Use diplomatic language for trade/diplomatic contexts
            )

    # Adjust effective relationship based on social history
    if social_modifier == "warm" and effective_relationship == "neutral":
        effective_relationship = "friendly"
    elif social_modifier == "cold" and effective_relationship == "neutral":
        effective_relationship = "hostile"

    # Get faction-specific templates
    faction_templates_speaker = faction_templates.get(
        speaker.faction, faction_templates["Wildlife"]
    )
    templates = faction_templates_speaker[effective_relationship]

    # Analyze conversation history to avoid loops
    recent_questions = sum(
        1
        for line in conversation_history[-3:]
        if any(word in line.lower() for word in ["what", "how", "why", "tell me", "elaborate", "?"])
    )

    # Always define prev_lower for later use
    prev_lower = previous_line.lower()

    # Extract and remember details from previous line
    for word in locations:
        if word.lower() in prev_lower:
            speaker.conversation_memory["mentioned_locations"].add(word)
            listener.conversation_memory["mentioned_locations"].add(word)

    for word in resources:
        if word.lower() in prev_lower:
            speaker.conversation_memory["mentioned_resources"].add(word)
            listener.conversation_memory["mentioned_resources"].add(word)

    for word in events:
        if word.lower() in prev_lower:
            speaker.conversation_memory["mentioned_events"].add(word)
            listener.conversation_memory["mentioned_events"].add(word)

    for word in activities:
        if word.lower() in prev_lower:
            speaker.conversation_memory["mentioned_activities"].add(word)
            listener.conversation_memory["mentioned_activities"].add(word)

    # Get tone settings
    tone_settings = conversation_tones.get(tone, conversation_tones["neutral"])

    # If we've had too many questions recently, provide a substantive answer
    if recent_questions >= 2:
        response_type = random.choice(["direct_answer", "explanation", "follow_up"])
    else:
        # Bias response type based on tone
        base_choices = [
            "acknowledgment",
            "follow_up",
            "agreement",
            "question",
            "direct_answer",
        ]
        if tone_settings["response_bias"]:
            # Weight towards tone's preferred responses
            weighted_choices = tone_settings["response_bias"] * 3 + [
                choice for choice in base_choices if choice not in tone_settings["response_bias"]
            ]
            response_type = random.choice(weighted_choices)
        else:
            response_type = random.choice(base_choices)

        # Override with specific logic based on previous line
        if any(word in prev_lower for word in ["what", "how", "why", "when", "where", "?"]):
            response_type = "question" if random.random() < 0.3 else "direct_answer"
        elif any(word in prev_lower for word in ["agree", "right", "good point", "same"]):
            response_type = "agreement"
        elif any(word in prev_lower for word in ["disagree", "not sure", "debatable", "wrong"]):
            response_type = "disagreement"
        elif any(word in prev_lower for word in ["speaking", "reminds", "related", "topic"]):
            response_type = "follow_up"

    # Enhanced response patterns
    response_patterns = {
        "agreement": [
            "I agree, {other}. {template}",
            "You're right about that. {template}",
            "That's a good point. {template}",
            "I feel the same way. {template}",
            "Exactly! {template}",
        ],
        "disagreement": [
            "I'm not so sure about that. {template}",
            "That's not how I see it. {template}",
            "I disagree. {template}",
            "That's debatable. {template}",
            "I see it differently. {template}",
        ],
        "question": [
            "What do you mean by that?",
            "Can you elaborate on {topic}?",
            "Why do you think that?",
            "Tell me more about {topic}.",
        ],
        "direct_answer": [
            "I mean that {explanation}",
            "It's about {topic} - {explanation}",
            "Let me explain: {explanation}",
            "What I meant was {explanation}",
            "To clarify: {explanation}",
        ],
        "explanation": [
            "It's because {reason}. {template}",
            "The situation involves {topic}. {template}",
            "Here's what happened: {explanation}",
            "The key point is {topic}. {template}",
        ],
        "acknowledgment": [
            "I hear you about {topic}.",
            "That's interesting about {topic}.",
            "I understand your concern about {topic}.",
            "That makes sense regarding {topic}.",
            "I see what you mean about {topic}.",
        ],
        "follow_up": [
            "Speaking of which, {template}",
            "That reminds me, {template}",
            "On that topic, {template}",
            "Related to that, {template}",
            "That brings to mind, {template}",
        ],
    }

    # Extract topic from previous line for reference
    topic_words = []
    for word in [
        "forest",
        "hunt",
        "territory",
        "trade",
        "battle",
        "mountain",
        "river",
        "castle",
        "crystal",
        "ancient",
        "merchant",
        "caravan",
    ]:
        if word in prev_lower:
            topic_words.append(word)
    topic = random.choice(topic_words) if topic_words else "that"

    # Generate explanations for direct answers
    explanations = {
        "forest": "the ancient woods hold many secrets and resources we must protect",
        "hunt": "the balance of predator and prey is crucial to our survival",
        "territory": "our lands are shrinking due to external pressures",
        "trade": "commerce between our peoples could bring mutual benefits",
        "battle": "the recent conflicts have changed everything",
        "mountain": "the peaks contain valuable minerals and strategic positions",
        "river": "the waterways are vital for transportation and resources",
        "castle": "the ruins hold artifacts of great power",
        "crystal": "these gems have mystical properties",
        "ancient": "our ancestors knew secrets we've forgotten",
        "merchant": "traders bring news from distant lands",
        "caravan": "these groups carry goods and information across territories",
    }
    explanation = explanations.get(topic, "it's a matter of great importance to our people")

    # Select response pattern
    pattern = random.choice(response_patterns[response_type])

    # Get a template for the second part (if needed)
    template = random.choice(templates)

    # Add personality modifier sometimes
    personality_prefix = ""
    if random.random() < 0.4:  # 40% chance for more personality
        personality_prefix = (
            random.choice(personality_modifiers[speaker.personality][relationship]) + " "
        )

    # Safe template formatting function
    def safe_format_template(template_str) -> str:
        """Format template with available placeholders, ignoring missing ones."""
        try:
            return template_str.format(
                other=listener.name,
                resource=random.choice(resources),
                location=random.choice(locations),
                event=random.choice(events),
                activity=random.choice(activities),
            )
        except KeyError as e:
            # If a placeholder is missing, try without it
            missing_key = str(e).strip("'")
            if missing_key == "other":
                return template_str.format(
                    resource=random.choice(resources),
                    location=random.choice(locations),
                    event=random.choice(events),
                    activity=random.choice(activities),
                )
            elif missing_key == "resource":
                return template_str.format(
                    other=listener.name,
                    location=random.choice(locations),
                    event=random.choice(events),
                    activity=random.choice(activities),
                )
            elif missing_key == "location":
                return template_str.format(
                    other=listener.name,
                    resource=random.choice(resources),
                    event=random.choice(events),
                    activity=random.choice(activities),
                )
            elif missing_key == "event":
                return template_str.format(
                    other=listener.name,
                    resource=random.choice(resources),
                    location=random.choice(locations),
                    activity=random.choice(activities),
                )
            elif missing_key == "activity":
                return template_str.format(
                    other=listener.name,
                    resource=random.choice(resources),
                    location=random.choice(locations),
                    event=random.choice(events),
                )
            else:
                # If we can't format, return the template as-is
                return template_str

    # Format the response
    if response_type in ["question", "acknowledgment"]:
        response = pattern.format(topic=topic)
    elif response_type == "direct_answer":
        # Handle patterns that may or may not have {topic}
        try:
            response = pattern.format(explanation=explanation, topic=topic)
        except KeyError:
            try:
                response = pattern.format(explanation=explanation)
            except KeyError:
                response = pattern.replace("{explanation}", explanation).replace("{topic}", topic)
    elif response_type == "explanation":
        formatted_template = safe_format_template(template)
        try:
            response = pattern.format(reason=explanation, topic=topic, template=formatted_template)
        except KeyError:
            try:
                response = pattern.format(reason=explanation, template=formatted_template)
            except KeyError:
                response = (
                    pattern.replace("{reason}", explanation)
                    .replace("{topic}", topic)
                    .replace("{template}", formatted_template)
                )
    else:
        # Handle other response types (agreement, disagreement, follow_up)
        formatted_template = safe_format_template(template)
        try:
            response = pattern.format(other=listener.name, topic=topic, template=formatted_template)
        except KeyError:
            try:
                response = pattern.format(topic=topic, template=formatted_template)
            except KeyError:
                response = (
                    pattern.replace("{other}", listener.name)
                    .replace("{topic}", topic)
                    .replace("{template}", formatted_template)
                )

    # Add context-specific elements
    if context == "trade":
        if random.random() < 0.3:
            response = "On the business side... " + response
    elif context == "combat":
        if random.random() < 0.3:
            response = "After what happened... " + response
    elif context == "urgent":
        if random.random() < 0.3:
            response = "This is crucial... " + response

    # Store in memory
    speaker.memory.append(response)
    if len(speaker.memory) > 5:
        speaker.memory.pop(0)

    return personality_prefix + response


# Duplicate function removed - keeping the first definition at line 618


def conversation(npc1, npc2, turns=4, context="casual", tone="neutral") -> list:
    """
    Natural conversation with responsive dialogue, memory, and tone.
    """
    if not should_talk(npc1, npc2):
        print(f"{npc1.name} and {npc2.name} have nothing to say.")
        return

    relationship = get_relationship_type(npc1, npc2)

    print(f"=== {context.title()} Conversation ({tone.title()} Tone) ===")
    print(
        f"Between {npc1.name} ({npc1.faction}, {npc1.personality}) and {npc2.name} ({npc2.faction}, {npc2.personality})"
    )
    print(f"Relationship: {relationship}")
    print()

    conversation_history = []
    current_speaker = npc1
    current_listener = npc2

    for turn in range(turns):
        if turn == 0:
            # First turn - start with a regular line
            line = generate_line(current_speaker, current_listener, context)
        else:
            # Check if we should use memory-driven dialogue (20% chance if speaker has memory)
            memory_line = None
            if random.random() < 0.2:  # 20% chance
                memory_line = generate_memory_driven_line(
                    current_speaker, current_listener, context
                )

            if memory_line:
                line = memory_line
            else:
                # Subsequent turns - respond to previous line
                previous_line = conversation_history[-1]
                line = generate_response(
                    current_speaker,
                    current_listener,
                    previous_line,
                    context,
                    conversation_history,
                    tone,
                )

        conversation_history.append(line)
        print(f"{current_speaker.name}: {line}")

        # Check for action triggers
        line_lower = line.lower()

        # Hunt trigger - Predators (expanded phrases)
        if (
            any(
                phrase in line_lower
                for phrase in [
                    "the hunt begins now",
                    "the hunt is upon you",
                    "your time has come",
                    "the chase begins",
                    "the predator claims",
                    "hunt this time",
                    "smell your fear",
                    "pack grows hungry",
                    "escape the hunt",
                ]
            )
            and current_speaker.faction == "Predators"
        ):
            print(f"\n⚠️  {current_listener.name} reacts with alarm!")
            commence_hunt(current_speaker, current_listener)
            break

        # Migration trigger - Wildlife (expanded phrases)
        elif (
            any(
                phrase in line_lower
                for phrase in [
                    "herd migrates",
                    "we migrate",
                    "migration begins",
                    "herd stirring",
                    "old trails",
                    "great journey",
                    "migration calls",
                    "seasons change",
                    "herd gathers",
                    "ancient paths",
                    "changing seasons",
                ]
            )
            and current_speaker.faction == "Wildlife"
        ):
            print(f"\n🌿 {current_listener.name} senses the movement!")
            commence_migration(current_speaker, current_listener)
            break

        # Construction trigger - Pioneers (expanded phrases)
        elif (
            any(
                phrase in line_lower
                for phrase in [
                    "we must build",
                    "construction begins",
                    "expanded our settlement",
                    "foundation ready",
                    "builders eager",
                    "storage facility",
                    "watchtower",
                    "put our skills",
                    "trading post",
                    "plans for structure",
                    "new workshop",
                    "proper storage",
                    "early warning",
                    "magnificent structure",
                ]
            )
            and current_speaker.faction == "Pioneers"
        ):
            print(f"\n🔨 {current_listener.name} sees the ambition!")
            commence_construction(current_speaker, current_listener)
            break

        # Summoning trigger - Wildlife (expanded phrases)
        elif (
            any(
                phrase in line_lower
                for phrase in [
                    "ancient powers",
                    "dark summoning",
                    "summoning begins",
                    "ancient energies",
                    "old ones whisper",
                    "call upon darkness",
                    "ritual circle",
                    "shadows restless",
                    "powerful entities",
                    "ancient pact",
                    "dark forces align",
                    "great power",
                    "darkness tonight",
                ]
            )
            and current_speaker.faction == "Wildlife"
        ):
            print(f"\n🌓 {current_listener.name} feels the darkness gathering!")
            commence_summoning(current_speaker, current_listener)
            break

        # Truce trigger - Any faction (diplomatic phrases)
        elif any(
            phrase in line_lower
            for phrase in [
                "terms of peace",
                "truce could benefit",
                "discuss terms",
                "temporary truce",
                "avoid conflict",
                "peace established",
                "negotiate fair",
                "find common ground",
                "room for cooperation",
                "temporary ceasefire",
                "peaceful relations",
                "mutual respect",
                "possibilities for cooperation",
            ]
        ):
            print(f"\n🤝 {current_listener.name} considers the diplomatic proposal!")
            negotiate_truce(current_speaker, current_listener)
            break

        # Trade agreement trigger - Any faction (trade phrases)
        elif any(
            phrase in line_lower
            for phrase in [
                "trade might serve",
                "establish trade routes",
                "mutual gain",
                "trade agreement",
                "share resources",
                "economic alliance",
                "profitable partnership",
                "trade terms",
                "mutual exchange",
                "work together",
                "cooperation",
            ]
        ):
            print(f"\n💰 {current_listener.name} ponders the trade proposal!")
            negotiate_trade_agreement(current_speaker, current_listener)
            break

        # Alliance trigger - Any faction (alliance phrases)
        elif any(
            phrase in line_lower
            for phrase in [
                "alliance possible",
                "lasting alliance",
                "mutual obligation",
                "bound by treaty",
                "stand together",
                "united front",
                "alliance formed",
                "joint alliance",
                "defensive alliance",
            ]
        ):
            print(f"\n⚔️ {current_listener.name} weighs the alliance proposal!")
            form_alliance(current_speaker, current_listener)
            break

        # Add listening indicators more frequently
        if random.random() < 0.6:  # 60% chance
            listening_cues = {
                "Wildlife": [
                    "(ears twitch attentively)",
                    "(sniffs the air thoughtfully)",
                    "(nods slowly)",
                ],
                "Predators": [
                    "(watches intently)",
                    "(growls softly in agreement)",
                    "(eyes narrow)",
                ],
                "Pioneers": [
                    "(takes notes mentally)",
                    "(nods thoughtfully)",
                    "(considers this)",
                ],
            }
            cue = random.choice(
                listening_cues.get(current_listener.faction, ["(listens carefully)"])
            )
            print(f"  {cue}")

        # Switch speakers
        current_speaker, current_listener = current_listener, current_speaker

        # Add natural pauses or transitions
        if turn < turns - 1 and random.random() < 0.3:  # 30% chance
            transitions = [
                f"({current_speaker.name} pauses to consider)",
                f"({current_speaker.name} gathers their thoughts)",
                f"({current_speaker.name} looks around before continuing)",
                f"({current_speaker.name} takes a moment)",
            ]
            print(f"  {random.choice(transitions)}")

    print()


# Demonstration
if __name__ == "__main__":
    # Create NPCs with different personalities
    npc1 = NPC("Arkan", "Wildlife")  # Will get random personality
    npc2 = NPC("Vel", "Wildlife")  # Will get random personality

    print("=== Casual Wildlife Conversation ===")
    conversation(npc1, npc2, turns=6, context="casual", tone="cooperative")

    # Different faction NPCs
    npc3 = NPC("Throg", "Predators")
    npc4 = NPC("Elara", "Pioneers")

    print("=== Trade Conversation (Predators vs Pioneers) ===")
    conversation(npc3, npc4, turns=8, context="trade", tone="neutral")

    # Wildlife migration scenario
    npc5 = NPC("Luna", "Wildlife")
    npc6 = NPC("Talon", "Wildlife")

    print("=== Wildlife Migration Discussion ===")
    conversation(npc5, npc6, turns=6, context="casual", tone="friendly")

    # Pioneer construction scenario
    npc7 = NPC("Grok", "Pioneers")
    npc8 = NPC("Elara", "Pioneers")

    print("=== Pioneer Construction Planning ===")
    conversation(npc7, npc8, turns=6, context="trade", tone="cooperative")

    # Wildlife summoning scenario
    npc9 = NPC("Zorg", "Wildlife")
    npc10 = NPC("Nyx", "Wildlife")

    print("=== Wildlife Ritual Discussion ===")
    conversation(npc9, npc10, turns=6, context="urgent", tone="friendly")

    # Diplomatic scenarios - more focused on neutral/diplomatic tones
    npc11 = NPC("Draven", "Predators")
    npc12 = NPC("Sylvana", "Wildlife")

    print("=== Diplomatic Wildlife-Predator Discussion ===")
    conversation(npc11, npc12, turns=10, context="casual", tone="neutral")

    # Trade negotiation scenario
    npc13 = NPC("Marcus", "Pioneers")
    npc14 = NPC("Vorath", "Wildlife")

    print("=== Pioneer-Wildlife Trade Negotiations ===")
    conversation(npc13, npc14, turns=10, context="trade", tone="neutral")

    # Alliance possibility scenario
    npc15 = NPC("Eldrin", "Pioneers")
    npc16 = NPC("Thrain", "Pioneers")

    print("=== Wise Pioneer Alliance Discussion ===")
    conversation(npc15, npc16, turns=8, context="casual", tone="diplomatic")


# Test the enhanced social consequences system
def test_social_consequences() -> None:
    """Test the social consequences system with various interactions."""
    print("\n" + "=" * 60)
    print("🧪 TESTING ENHANCED SOCIAL CONSEQUENCES SYSTEM")
    print("=" * 60)

    # Create test NPCs
    npc1 = NPC("Thrain", "Pioneers")
    npc2 = NPC("Vorath", "Wildlife")

    print(
        f"\n👥 Test NPCs: {npc1.name} ({npc1.faction}, {npc1.personality}) and {npc2.name} ({npc2.faction}, {npc2.personality})"
    )
    print(f"Initial relationship: {npc1.get_relationship_with(npc2.name):.2f}")

    # Test 1: Successful trade
    print("\n1️⃣ Testing successful trade interaction...")
    apply_social_consequence(npc1, npc2, "successful_trade", "iron ore exchange", "trade")
    print(f"Relationship after trade: {npc1.get_relationship_with(npc2.name):.2f}")

    # Test 2: Insult
    print("\n2️⃣ Testing insult interaction...")
    apply_social_consequence(npc1, npc2, "insult", "called you weak", "personality")
    print(f"Relationship after insult: {npc1.get_relationship_with(npc2.name):.2f}")

    # Test 3: Alliance help
    print("\n3️⃣ Testing alliance help...")
    apply_social_consequence(npc2, npc1, "alliance_help", "helped in battle", "defense")
    print(f"Relationship after help: {npc1.get_relationship_with(npc2.name):.2f}")

    # Test dialogue generation with social context
    print("\n💬 Testing dialogue with social memory...")
    print(f"Social context: {npc1.get_social_context_modifier(npc2.name)}")

    # Generate dialogue that references social history
    memory_line = generate_memory_driven_line(npc1, npc2, "casual")
    if memory_line:
        print(f"Memory-driven dialogue: {memory_line}")
    else:
        print("No memory-driven dialogue available")

    # Test memory decay
    print("\n⏰ Testing memory decay...")
    original_relationship = npc1.get_relationship_with(npc2.name)
    npc1.decay_social_memory()
    npc2.decay_social_memory()
    decayed_relationship = npc1.get_relationship_with(npc2.name)
    print(f"Relationship before decay: {original_relationship:.2f}")
    print(f"Relationship after decay: {decayed_relationship:.2f}")

    print("\n✅ Social consequences test completed!")


def test_expanded_interactions() -> None:
    """Test the expanded interaction types system."""
    print("\n" + "=" * 60)
    print("🧪 TESTING EXPANDED INTERACTION TYPES")
    print("=" * 60)

    # Create test NPCs with leadership roles
    npc1 = NPC("Thrain", "Pioneers")
    npc2 = NPC("Vorath", "Wildlife")
    npc3 = NPC("Eldrin", "Pioneers")  # Leader
    npc4 = NPC("Mira", "Wildlife")  # Shaman

    # Assign leadership roles
    npc3.set_leadership_role("leader")
    npc4.set_leadership_role("shaman")

    print("\n👥 Test NPCs:")
    print(
        f"  {npc1.name} ({npc1.faction}, {npc1.personality}) - Influence: {npc1.decision_influence:.2f}"
    )
    print(
        f"  {npc2.name} ({npc2.faction}, {npc2.personality}) - Influence: {npc2.decision_influence:.2f}"
    )
    print(
        f"  {npc3.name} ({npc3.faction}, {npc3.personality}) - {npc3.leadership_role} - Influence: {npc3.decision_influence:.2f}"
    )
    print(
        f"  {npc4.name} ({npc4.faction}, {npc4.personality}) - {npc4.leadership_role} - Influence: {npc4.decision_influence:.2f}"
    )

    # Test 1: Minor disagreement
    print("\n1️⃣ Testing minor disagreement...")
    apply_social_consequence(
        npc1, npc2, "minor_disagreement", "disagree about hunting grounds", "territory"
    )
    print(f"Relationship after disagreement: {npc1.get_relationship_with(npc2.name):.2f}")

    # Test 2: Resource theft
    print("\n2️⃣ Testing resource theft...")
    apply_social_consequence(npc1, npc2, "resource_theft", "stole food supplies", "food")
    print(f"Relationship after theft: {npc1.get_relationship_with(npc2.name):.2f}")

    # Test 3: Cultural offense
    print("\n3️⃣ Testing cultural offense...")
    apply_social_consequence(npc2, npc1, "cultural_offense", "mocked sacred totem", "religion")
    print(f"Relationship after offense: {npc1.get_relationship_with(npc2.name):.2f}")

    # Test 4: Festival invitation
    print("\n4️⃣ Testing festival invitation...")
    apply_social_consequence(
        npc3, npc4, "festival_invitation", "invited to harvest festival", "celebration"
    )
    print(f"Relationship after invitation: {npc3.get_relationship_with(npc4.name):.2f}")

    # Test 5: Leader mediation
    print("\n5️⃣ Testing leader mediation...")
    apply_social_consequence(
        npc3, npc1, "leader_mediation", "mediated boundary dispute", "diplomacy"
    )
    apply_social_consequence(
        npc3, npc2, "leader_mediation", "mediated boundary dispute", "diplomacy"
    )
    print(
        f"Thrain's relationship with Eldrin (mediator): {npc1.get_relationship_with(npc3.name):.2f}"
    )
    print(
        f"Vorath's relationship with Eldrin (mediator): {npc2.get_relationship_with(npc3.name):.2f}"
    )

    # Test leadership influence on decisions
    print("\n👑 Testing leadership influence on decisions...")
    base_diplomatic_opinion = 0.0  # Neutral starting point
    leader_influenced = npc3.influence_faction_decision(
        "diplomatic", base_diplomatic_opinion, [npc3, npc4]
    )
    print(f"Base diplomatic opinion: {base_diplomatic_opinion:.2f}")
    print(f"Leader-influenced opinion: {leader_influenced:.2f}")

    # Test memory-driven dialogue with new interaction types
    print("\n💬 Testing memory-driven dialogue...")
    memory_line1 = generate_memory_driven_line(npc1, npc2, "casual")
    memory_line2 = generate_memory_driven_line(npc3, npc4, "casual")
    if memory_line1:
        print(f"Thrain about Vorath: {memory_line1}")
    if memory_line2:
        print(f"Eldrin about Mira: {memory_line2}")

    print("\n✅ Expanded interactions test completed!")


if __name__ == "__main__":
    # Run new expanded interactions test
    test_expanded_interactions()
