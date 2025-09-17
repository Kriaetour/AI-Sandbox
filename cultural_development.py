#!/usr/bin/env python3
"""
Cultural Development System - AI Sandbox Feature

An independent cultural simulation system that evolves languages, art, traditions,
and cultural exchanges between tribes. This system runs parallel to military
activities and focuses on the "soft power" aspects of tribal development.

Features:
- Language evolution and dialect formation
- Artistic expression (music, visual arts, dance)
- Cultural traditions and rituals
- Storytelling and oral histories
- Cultural exchange and influence
- Cultural evolution over generations

Usage:
  python cultural_development.py --tribes 8 --generations 100
  python cultural_development.py --interactive --cultural-exchange-rate 0.3
"""

import argparse
import json
import random
import time
import os
from typing import Dict, List, Tuple, Any

# --------------------------------------------------------------------------------------
# Configuration Constants
# --------------------------------------------------------------------------------------

CULTURAL_DATA_FILE = "artifacts/cultural_data.json"
ARTIFACTS_DIR = "artifacts"

# Cultural evolution parameters
LANGUAGE_MUTATION_RATE = 0.05
ARTISTIC_INNOVATION_RATE = 0.03
TRADITION_TRANSMISSION_RATE = 0.8
CULTURAL_EXCHANGE_RATE = 0.2
GENERATION_LENGTH = 50  # ticks per generation

# --------------------------------------------------------------------------------------
# Cultural Data Structures
# --------------------------------------------------------------------------------------

class Language:
    """Represents a tribe's language with vocabulary and grammar rules."""
    def __init__(self, tribe_name: str, seed_words: List[str] = None):
        self.tribe_name = tribe_name
        self.vocabulary: Dict[str, str] = {}
        self.grammar_rules: Dict[str, Any] = {}
        self.dialects: List[Dict] = []

        # Initialize with seed vocabulary
        if seed_words:
            for word in seed_words:
                self.vocabulary[word] = self._generate_pronunciation(word)
        else:
            self._initialize_basic_vocabulary()

    def _initialize_basic_vocabulary(self):
        """Create basic vocabulary for new languages."""
        basic_concepts = [
            "water", "fire", "earth", "sky", "sun", "moon", "star",
            "food", "home", "friend", "enemy", "love", "fear", "joy",
            "hunt", "gather", "dance", "sing", "story", "dream"
        ]
        for concept in basic_concepts:
            self.vocabulary[concept] = self._generate_pronunciation(concept)

    def _generate_pronunciation(self, concept: str) -> str:
        """Generate a pseudo-linguistic pronunciation for a concept."""
        vowels = "aeiou"
        consonants = "ptkmnslr"
        syllables = random.randint(1, 3)

        pronunciation = ""
        for _ in range(syllables):
            if random.random() < 0.7:  # 70% chance of consonant
                pronunciation += random.choice(consonants)
            pronunciation += random.choice(vowels)
            if random.random() < 0.4:  # 40% chance of final consonant
                pronunciation += random.choice(consonants)

        return pronunciation

    def evolve(self, mutation_rate: float = LANGUAGE_MUTATION_RATE):
        """Evolve the language through time."""
        # Add new words for new concepts
        new_concepts = ["warrior", "healer", "elder", "child", "spirit", "magic"]
        for concept in new_concepts:
            if concept not in self.vocabulary and random.random() < 0.1:
                self.vocabulary[concept] = self._generate_pronunciation(concept)

        # Mutate existing words
        for concept in list(self.vocabulary.keys()):
            if random.random() < mutation_rate:
                original = self.vocabulary[concept]
                # Simple mutation: change a random character
                if len(original) > 1:
                    pos = random.randint(0, len(original) - 1)
                    chars = "aeioupkmt"
                    new_char = random.choice(chars)
                    mutated = original[:pos] + new_char + original[pos + 1:]
                    self.vocabulary[concept] = mutated

    def exchange_with(self, other_language: 'Language', exchange_rate: float = CULTURAL_EXCHANGE_RATE):
        """Exchange words and concepts with another language."""
        # Borrow words from other language
        for concept, word in other_language.vocabulary.items():
            if concept not in self.vocabulary and random.random() < exchange_rate:
                # Adapt the pronunciation to fit our language's style
                adapted_word = self._adapt_pronunciation(word)
                self.vocabulary[concept] = adapted_word

    def _adapt_pronunciation(self, foreign_word: str) -> str:
        """Adapt a foreign word to fit our language's pronunciation patterns."""
        # Simple adaptation: occasionally change characters
        adapted = ""
        for char in foreign_word:
            if random.random() < 0.3:  # 30% chance to change
                if char in "aeiou":
                    adapted += random.choice("aeiou")
                else:
                    adapted += random.choice("ptkmnslr")
            else:
                adapted += char
        return adapted

class ArtisticTradition:
    """Represents a tribe's artistic and cultural expressions."""
    def __init__(self, tribe_name: str):
        self.tribe_name = tribe_name
        self.music_styles: List[Dict] = []
        self.visual_arts: List[Dict] = []
        self.dance_forms: List[Dict] = []
        self.stories: List[Dict] = []
        self.rituals: List[Dict] = []

        self._initialize_basic_traditions()

    def _initialize_basic_traditions(self):
        """Create basic artistic traditions."""
        # Basic music style
        self.music_styles.append({
            "name": "Tribal Chant",
            "instruments": ["drums", "voices"],
            "tempo": "slow",
            "purpose": "ceremonial"
        })

        # Basic story
        self.stories.append({
            "title": "Creation of the World",
            "theme": "origin",
            "length": "long",
            "moral": "respect nature"
        })

        # Basic ritual
        self.rituals.append({
            "name": "Harvest Celebration",
            "frequency": "annual",
            "participants": "all tribe members",
            "purpose": "thanksgiving"
        })

    def innovate(self, innovation_rate: float = ARTISTIC_INNOVATION_RATE):
        """Create new artistic expressions."""
        if random.random() < innovation_rate:
            innovation_type = random.choice(["music", "art", "dance", "story", "ritual"])

            if innovation_type == "music":
                new_style = {
                    "name": f"Innovative Melody {len(self.music_styles) + 1}",
                    "instruments": random.sample(["flute", "drum", "voice", "rattle", "string"], random.randint(1, 3)),
                    "tempo": random.choice(["slow", "medium", "fast"]),
                    "purpose": random.choice(["celebration", "mourning", "hunting", "healing"])
                }
                self.music_styles.append(new_style)
                print(f"� {self.tribe_name} developed new music style: {new_style['name']}")

            elif innovation_type == "story":
                new_story = {
                    "title": f"Epic Tale {len(self.stories) + 1}",
                    "theme": random.choice(["heroism", "love", "nature", "conflict", "mystery"]),
                    "length": random.choice(["short", "medium", "long"]),
                    "moral": random.choice(["courage", "wisdom", "harmony", "perseverance"])
                }
                self.stories.append(new_story)
                print(f"� {self.tribe_name} created new story: {new_story['title']}")

            elif innovation_type == "ritual":
                new_ritual = {
                    "name": f"Sacred Ceremony {len(self.rituals) + 1}",
                    "frequency": random.choice(["daily", "weekly", "monthly", "annual"]),
                    "participants": random.choice(["elders", "warriors", "all members", "selected few"]),
                    "purpose": random.choice(["healing", "protection", "celebration", "remembrance"])
                }
                self.rituals.append(new_ritual)
                print(f"🕊️ {self.tribe_name} established new ritual: {new_ritual['name']}")

    def exchange_culture(self, other_tradition: 'ArtisticTradition', exchange_rate: float = CULTURAL_EXCHANGE_RATE):
        """Exchange cultural elements with another tribe."""
        # Exchange stories
        for story in other_tradition.stories:
            if random.random() < exchange_rate and len(self.stories) < 10:
                adapted_story = story.copy()
                adapted_story["title"] = f"Adapted: {story['title']}"
                adapted_story["origin"] = other_tradition.tribe_name
                self.stories.append(adapted_story)

        # Exchange rituals
        for ritual in other_tradition.rituals:
            if random.random() < exchange_rate and len(self.rituals) < 8:
                adapted_ritual = ritual.copy()
                adapted_ritual["name"] = f"Adapted: {ritual['name']}"
                adapted_ritual["origin"] = other_tradition.tribe_name
                self.rituals.append(adapted_ritual)

    def innovate(self, innovation_rate: float = ARTISTIC_INNOVATION_RATE):
        """Create new artistic expressions."""
        if random.random() < innovation_rate:
            innovation_type = random.choice(["music", "art", "dance", "story", "ritual"])

            if innovation_type == "music":
                new_style = {
                    "name": f"Innovative Melody {len(self.music_styles) + 1}",
                    "instruments": random.sample(["flute", "drum", "voice", "rattle", "string"], random.randint(1, 3)),
                    "tempo": random.choice(["slow", "medium", "fast"]),
                    "purpose": random.choice(["celebration", "mourning", "hunting", "healing"])
                }
                self.music_styles.append(new_style)
                print(f"🎵 {self.tribe_name} developed new music style: {new_style['name']}")

            elif innovation_type == "story":
                new_story = {
                    "title": f"Epic Tale {len(self.stories) + 1}",
                    "theme": random.choice(["heroism", "love", "nature", "conflict", "mystery"]),
                    "length": random.choice(["short", "medium", "long"]),
                    "moral": random.choice(["courage", "wisdom", "harmony", "perseverance"])
                }
                self.stories.append(new_story)
                print(f"📖 {self.tribe_name} created new story: {new_story['title']}")

            elif innovation_type == "ritual":
                new_ritual = {
                    "name": f"Sacred Ceremony {len(self.rituals) + 1}",
                    "frequency": random.choice(["daily", "weekly", "monthly", "annual"]),
                    "participants": random.choice(["elders", "warriors", "all members", "selected few"]),
                    "purpose": random.choice(["healing", "protection", "celebration", "remembrance"])
                }
                self.rituals.append(new_ritual)
                print(f"🕊️ {self.tribe_name} established new ritual: {new_ritual['name']}")

    def exchange_culture(self, other_tradition: 'ArtisticTradition', exchange_rate: float = CULTURAL_EXCHANGE_RATE):
        """Exchange cultural elements with another tribe."""
        # Exchange stories
        for story in other_tradition.stories:
            if random.random() < exchange_rate and len(self.stories) < 10:
                adapted_story = story.copy()
                adapted_story["title"] = f"Adapted: {story['title']}"
                adapted_story["origin"] = other_tradition.tribe_name
                self.stories.append(adapted_story)

        # Exchange rituals
        for ritual in other_tradition.rituals:
            if random.random() < exchange_rate and len(self.rituals) < 8:
                adapted_ritual = ritual.copy()
                adapted_ritual["name"] = f"Adapted: {ritual['name']}"
                adapted_ritual["origin"] = other_tradition.tribe_name
                self.rituals.append(adapted_ritual)


class Cuisine:
    """Represents a tribe's culinary traditions and food culture."""
    def __init__(self, tribe_name: str):
        self.tribe_name = tribe_name
        self.cooking_methods: List[Dict] = []
        self.ingredients: List[str] = []
        self.dishes: List[Dict] = []
        self.dietary_restrictions: List[str] = []
        self.meal_rituals: List[Dict] = []

        self._initialize_basic_cuisine()

    def _initialize_basic_cuisine(self):
        """Create basic culinary foundations."""
        # Basic cooking methods
        self.cooking_methods.append({
            "method": "Roasting",
            "tools": ["fire", "spit"],
            "purpose": "preserving meat"
        })

        # Basic ingredients based on environment
        if "Forest" in self.tribe_name:
            self.ingredients.extend(["berries", "nuts", "herbs", "forest mushrooms"])
        elif "Mountain" in self.tribe_name:
            self.ingredients.extend(["mountain herbs", "goat meat", "roots", "wild grains"])
        elif "River" in self.tribe_name:
            self.ingredients.extend(["fish", "river plants", "shellfish", "water reeds"])
        elif "Desert" in self.tribe_name:
            self.ingredients.extend(["cactus fruit", "dried meats", "desert herbs", "dates"])
        elif "Island" in self.tribe_name:
            self.ingredients.extend(["coconut", "seaweed", "tropical fruits", "fish"])
        elif "Plains" in self.tribe_name:
            self.ingredients.extend(["grains", "game meat", "wild vegetables", "honey"])
        elif "Cave" in self.tribe_name:
            self.ingredients.extend(["cave fungi", "bat meat", "minerals", "underground roots"])
        elif "Sky" in self.tribe_name:
            self.ingredients.extend(["migratory bird meat", "high-altitude herbs", "nuts", "berries"])

        # Basic dish
        self.dishes.append({
            "name": "Basic Stew",
            "ingredients": self.ingredients[:3],
            "cooking_method": "boiling",
            "occasion": "everyday"
        })

    def innovate_cuisine(self, innovation_rate: float = ARTISTIC_INNOVATION_RATE):
        """Create new culinary innovations."""
        if random.random() < innovation_rate:
            innovation_type = random.choice(["dish", "method", "ritual", "restriction"])

            if innovation_type == "dish":
                new_dish = {
                    "name": f"Specialty Dish {len(self.dishes) + 1}",
                    "ingredients": random.sample(self.ingredients, min(3, len(self.ingredients))),
                    "cooking_method": random.choice(["grilling", "steaming", "fermenting", "smoking", "drying"]),
                    "occasion": random.choice(["festival", "ceremony", "celebration", "healing"])
                }
                self.dishes.append(new_dish)
                print(f"🍽️ {self.tribe_name} created new dish: {new_dish['name']}")

            elif innovation_type == "method":
                new_method = {
                    "method": random.choice(["Fermentation", "Smoking", "Pickling", "Spice Blending", "Herb Infusion"]),
                    "tools": random.sample(["clay pots", "baskets", "stones", "wood", "bones"], 2),
                    "purpose": random.choice(["preservation", "flavor enhancement", "medicinal", "ritual"])
                }
                self.cooking_methods.append(new_method)
                print(f"🔥 {self.tribe_name} developed cooking method: {new_method['method']}")

            elif innovation_type == "ritual":
                new_ritual = {
                    "name": f"Feast Ritual {len(self.meal_rituals) + 1}",
                    "type": random.choice(["thanksgiving", "harvest", "hunting", "healing"]),
                    "participants": random.choice(["family", "extended family", "whole tribe", "elders"]),
                    "special_foods": random.sample(self.ingredients, min(2, len(self.ingredients)))
                }
                self.meal_rituals.append(new_ritual)
                print(f"🍛 {self.tribe_name} established meal ritual: {new_ritual['name']}")

    def exchange_cuisine(self, other_cuisine: 'Cuisine', exchange_rate: float = CULTURAL_EXCHANGE_RATE):
        """Exchange culinary knowledge with another tribe."""
        # Exchange ingredients
        for ingredient in other_cuisine.ingredients:
            if ingredient not in self.ingredients and random.random() < exchange_rate:
                self.ingredients.append(ingredient)

        # Exchange cooking methods
        for method in other_cuisine.cooking_methods:
            if method not in self.cooking_methods and random.random() < exchange_rate:
                adapted_method = method.copy()
                adapted_method["origin"] = other_cuisine.tribe_name
                self.cooking_methods.append(adapted_method)

        # Exchange dishes
        for dish in other_cuisine.dishes:
            if len(self.dishes) < 12 and random.random() < exchange_rate:
                adapted_dish = dish.copy()
                adapted_dish["name"] = f"Adapted: {dish['name']}"
                adapted_dish["origin"] = other_cuisine.tribe_name
                self.dishes.append(adapted_dish)


class Architecture:
    """Represents a tribe's architectural and building traditions."""
    def __init__(self, tribe_name: str):
        self.tribe_name = tribe_name
        self.building_styles: List[Dict] = []
        self.housing_designs: List[Dict] = []
        self.monuments: List[Dict] = []
        self.construction_materials: List[str] = []
        self.building_techniques: List[Dict] = []

        self._initialize_basic_architecture()

    def _initialize_basic_architecture(self):
        """Create basic architectural foundations."""
        # Basic construction materials based on environment
        if "Forest" in self.tribe_name:
            self.construction_materials.extend(["wood", "bark", "vines", "leaves"])
        elif "Mountain" in self.tribe_name:
            self.construction_materials.extend(["stone", "mountain wood", "animal hides", "bone"])
        elif "River" in self.tribe_name:
            self.construction_materials.extend(["river reeds", "mud", "driftwood", "shells"])
        elif "Desert" in self.tribe_name:
            self.construction_materials.extend(["adobe", "palm fronds", "desert stone", "animal hides"])
        elif "Island" in self.tribe_name:
            self.construction_materials.extend(["coconut palm", "coral", "sea shells", "thatch"])
        elif "Plains" in self.tribe_name:
            self.construction_materials.extend(["grass", "buffalo hide", "wood", "mud"])
        elif "Cave" in self.tribe_name:
            self.construction_materials.extend(["cave stone", "stalactites", "bone", "crystal"])
        elif "Sky" in self.tribe_name:
            self.construction_materials.extend(["light wood", "feathers", "bone", "mountain stone"])

        # Basic housing design
        self.housing_designs.append({
            "name": "Basic Hut",
            "materials": self.construction_materials[:3],
            "purpose": "family dwelling",
            "capacity": "4-6 people"
        })

        # Basic building technique
        self.building_techniques.append({
            "technique": "Post-and-Lintel",
            "materials": ["wood", "stone"],
            "purpose": "structural support"
        })

    def innovate_architecture(self, innovation_rate: float = ARTISTIC_INNOVATION_RATE):
        """Create new architectural innovations."""
        if random.random() < innovation_rate:
            innovation_type = random.choice(["housing", "monument", "technique", "style"])

            if innovation_type == "housing":
                new_design = {
                    "name": f"Advanced Dwelling {len(self.housing_designs) + 1}",
                    "materials": random.sample(self.construction_materials, min(3, len(self.construction_materials))),
                    "purpose": random.choice(["ceremonial hall", "elder residence", "storage facility", "meeting place"]),
                    "capacity": random.choice(["10-15 people", "20-30 people", "whole tribe", "specialized use"])
                }
                self.housing_designs.append(new_design)
                print(f"🏠 {self.tribe_name} designed new housing: {new_design['name']}")

            elif innovation_type == "monument":
                new_monument = {
                    "name": f"Sacred Monument {len(self.monuments) + 1}",
                    "materials": random.sample(self.construction_materials, min(2, len(self.construction_materials))),
                    "purpose": random.choice(["ancestor memorial", "spiritual center", "tribal gathering", "victory memorial"]),
                    "significance": random.choice(["religious", "historical", "cultural", "commemorative"])
                }
                self.monuments.append(new_monument)
                print(f"🗿 {self.tribe_name} built monument: {new_monument['name']}")

            elif innovation_type == "technique":
                new_technique = {
                    "technique": random.choice(["Arch Construction", "Dome Building", "Post-and-Lintel Advanced", "Mortar Mixing", "Thatched Roofing"]),
                    "materials": random.sample(self.construction_materials, min(2, len(self.construction_materials))),
                    "purpose": random.choice(["structural integrity", "weather protection", "aesthetic appeal", "durability"])
                }
                self.building_techniques.append(new_technique)
                print(f"🔨 {self.tribe_name} developed building technique: {new_technique['technique']}")

    def exchange_architecture(self, other_architecture: 'Architecture', exchange_rate: float = CULTURAL_EXCHANGE_RATE):
        """Exchange architectural knowledge with another tribe."""
        # Exchange construction materials
        for material in other_architecture.construction_materials:
            if material not in self.construction_materials and random.random() < exchange_rate:
                self.construction_materials.append(material)

        # Exchange building techniques
        for technique in other_architecture.building_techniques:
            if technique not in self.building_techniques and random.random() < exchange_rate:
                adapted_technique = technique.copy()
                adapted_technique["origin"] = other_architecture.tribe_name
                self.building_techniques.append(adapted_technique)

        # Exchange housing designs
        for design in other_architecture.housing_designs:
            if len(self.housing_designs) < 8 and random.random() < exchange_rate:
                adapted_design = design.copy()
                adapted_design["name"] = f"Adapted: {design['name']}"
                adapted_design["origin"] = other_architecture.tribe_name
                self.housing_designs.append(adapted_design)


class SocialStructure:
    """Represents a tribe's social organization and hierarchy."""
    def __init__(self, tribe_name: str):
        self.tribe_name = tribe_name
        self.leadership_styles: List[Dict] = []
        self.family_structures: List[Dict] = []
        self.social_roles: List[Dict] = []
        self.decision_making: List[Dict] = []
        self.social_norms: List[Dict] = []

        self._initialize_basic_social_structure()

    def _initialize_basic_social_structure(self):
        """Create basic social structure foundations."""
        # Basic leadership style
        self.leadership_styles.append({
            "style": "Elder Council",
            "basis": "wisdom and experience",
            "decision_scope": "tribal matters"
        })

        # Basic family structure
        self.family_structures.append({
            "structure": "Extended Family",
            "composition": "parents, children, grandparents",
            "residence": "matrilocal"
        })

        # Basic social roles
        self.social_roles.extend([
            {"role": "Shaman", "responsibility": "spiritual guidance", "selection": "spiritual calling"},
            {"role": "Warrior", "responsibility": "protection", "selection": "proven courage"},
            {"role": "Healer", "responsibility": "medical care", "selection": "healing knowledge"}
        ])

        # Basic decision making
        self.decision_making.append({
            "method": "Consensus",
            "participants": "all adults",
            "scope": "important matters"
        })

    def innovate_social_structure(self, innovation_rate: float = ARTISTIC_INNOVATION_RATE):
        """Create new social innovations."""
        if random.random() < innovation_rate:
            innovation_type = random.choice(["leadership", "family", "role", "decision", "norm"])

            if innovation_type == "leadership":
                new_style = {
                    "style": random.choice(["War Chief", "Spiritual Leader", "Council of Warriors", "Matriarchal Leadership"]),
                    "basis": random.choice(["combat prowess", "spiritual wisdom", "hereditary", "achievement"]),
                    "decision_scope": random.choice(["military matters", "spiritual affairs", "economic decisions", "all matters"])
                }
                self.leadership_styles.append(new_style)
                print(f"👑 {self.tribe_name} developed leadership style: {new_style['style']}")

            elif innovation_type == "family":
                new_structure = {
                    "structure": random.choice(["Nuclear Family", "Clan System", "Polygamous Structure", "Communal Living"]),
                    "composition": random.choice(["nuclear unit", "extended clan", "multiple spouses", "tribal commune"]),
                    "residence": random.choice(["patrilocal", "matrilocal", "neolocal", "communal"])
                }
                self.family_structures.append(new_structure)
                print(f"👨‍👩‍👧‍👦 {self.tribe_name} adopted family structure: {new_structure['structure']}")

            elif innovation_type == "role":
                new_role = {
                    "role": random.choice(["Storyteller", "Artisan", "Trader", "Diplomat", "Teacher"]),
                    "responsibility": random.choice(["cultural preservation", "craftsmanship", "commerce", "relations", "education"]),
                    "selection": random.choice(["apprenticeship", "natural talent", "election", "hereditary"])
                }
                self.social_roles.append(new_role)
                print(f"🎭 {self.tribe_name} established social role: {new_role['role']}")

            elif innovation_type == "decision":
                new_method = {
                    "method": random.choice(["Majority Vote", "Leader's Decree", "Lottery", "Trial by Combat"]),
                    "participants": random.choice(["elders only", "warriors", "all adults", "selected representatives"]),
                    "scope": random.choice(["minor disputes", "major decisions", "emergency situations", "all matters"])
                }
                self.decision_making.append(new_method)
                print(f"⚖️ {self.tribe_name} adopted decision method: {new_method['method']}")

    def exchange_social_structure(self, other_social: 'SocialStructure', exchange_rate: float = CULTURAL_EXCHANGE_RATE):
        """Exchange social knowledge with another tribe."""
        # Exchange social roles
        for role in other_social.social_roles:
            if role not in self.social_roles and random.random() < exchange_rate:
                adapted_role = role.copy()
                adapted_role["origin"] = other_social.tribe_name
                self.social_roles.append(adapted_role)

        # Exchange leadership styles
        for style in other_social.leadership_styles:
            if style not in self.leadership_styles and random.random() < exchange_rate:
                adapted_style = style.copy()
                adapted_style["origin"] = other_social.tribe_name
                self.leadership_styles.append(adapted_style)

        # Exchange decision making methods
        for method in other_social.decision_making:
            if method not in self.decision_making and random.random() < exchange_rate:
                adapted_method = method.copy()
                adapted_method["origin"] = other_social.tribe_name
                self.decision_making.append(adapted_method)


class CulturalSystem:
    """Main cultural development system manager."""
    def __init__(self, num_tribes: int = 5):
        self.tribes: Dict[str, Dict] = {}
        self.languages: Dict[str, Language] = {}
        self.traditions: Dict[str, ArtisticTradition] = {}
        self.cuisines: Dict[str, Cuisine] = {}
        self.architectures: Dict[str, Architecture] = {}
        self.social_structures: Dict[str, SocialStructure] = {}
        self.cultural_relations: Dict[Tuple[str, str], float] = {}
        self.generation = 0

        self._initialize_tribes(num_tribes)

    def _initialize_tribes(self, num_tribes: int):
        """Create initial tribes with their cultural foundations."""
        tribe_names = [
            "Forest People", "Mountain Clan", "River Tribe", "Desert Nomads",
            "Island Folk", "Plains Wanderers", "Cave Dwellers", "Sky Watchers"
        ]

        for i in range(num_tribes):
            tribe_name = tribe_names[i] if i < len(tribe_names) else f"Tribe_{i+1}"

            # Create language
            self.languages[tribe_name] = Language(tribe_name)

            # Create artistic traditions
            self.traditions[tribe_name] = ArtisticTradition(tribe_name)

            # Create cuisine
            self.cuisines[tribe_name] = Cuisine(tribe_name)

            # Create architecture
            self.architectures[tribe_name] = Architecture(tribe_name)

            # Create social structure
            self.social_structures[tribe_name] = SocialStructure(tribe_name)

            # Initialize tribe data
            self.tribes[tribe_name] = {
                "population": random.randint(50, 200),
                "location": (random.randint(-100, 100), random.randint(-100, 100)),
                "cultural_influence": 1.0,
                "language_complexity": 1.0,
                "artistic_development": 1.0
            }

    def simulate_generation(self, cultural_exchange_rate: float = CULTURAL_EXCHANGE_RATE):
        """Simulate one generation of cultural development."""
        self.generation += 1
        print(f"\n🌅 Generation {self.generation} - Cultural Evolution")

        # Language evolution
        print("\n📝 Language Evolution:")
        for tribe_name, language in self.languages.items():
            language.evolve()
            self.tribes[tribe_name]["language_complexity"] += random.uniform(-0.1, 0.2)

        # Artistic innovation
        print("\n🎨 Artistic Innovation:")
        for tribe_name, tradition in self.traditions.items():
            tradition.innovate()
            self.tribes[tribe_name]["artistic_development"] += random.uniform(-0.05, 0.15)

        # Culinary innovation
        print("\n🍽️ Culinary Innovation:")
        for tribe_name, cuisine in self.cuisines.items():
            cuisine.innovate_cuisine()
            # Add culinary development to tribe stats
            if "culinary_development" not in self.tribes[tribe_name]:
                self.tribes[tribe_name]["culinary_development"] = 1.0
            self.tribes[tribe_name]["culinary_development"] += random.uniform(-0.05, 0.15)

        # Architectural innovation
        print("\n🏗️ Architectural Innovation:")
        for tribe_name, architecture in self.architectures.items():
            architecture.innovate_architecture()
            # Add architectural development to tribe stats
            if "architectural_development" not in self.tribes[tribe_name]:
                self.tribes[tribe_name]["architectural_development"] = 1.0
            self.tribes[tribe_name]["architectural_development"] += random.uniform(-0.05, 0.15)

        # Social innovation
        print("\n👥 Social Innovation:")
        for tribe_name, social in self.social_structures.items():
            social.innovate_social_structure()
            # Add social development to tribe stats
            if "social_development" not in self.tribes[tribe_name]:
                self.tribes[tribe_name]["social_development"] = 1.0
            self.tribes[tribe_name]["social_development"] += random.uniform(-0.05, 0.15)

        # Cultural exchange between nearby tribes
        print("\n🤝 Cultural Exchange:")
        tribe_list = list(self.tribes.keys())
        for i in range(len(tribe_list)):
            for j in range(i + 1, len(tribe_list)):
                tribe1, tribe2 = tribe_list[i], tribe_list[j]

                # Calculate cultural proximity (closer tribes exchange more)
                loc1 = self.tribes[tribe1]["location"]
                loc2 = self.tribes[tribe2]["location"]
                distance = ((loc1[0] - loc2[0]) ** 2 + (loc1[1] - loc2[1]) ** 2) ** 0.5

                if distance < 50:  # Close enough for cultural exchange
                    exchange_probability = cultural_exchange_rate * (1 - distance / 50)

                    if random.random() < exchange_probability:
                        # Language exchange
                        self.languages[tribe1].exchange_with(self.languages[tribe2])
                        self.languages[tribe2].exchange_with(self.languages[tribe1])

                        # Cultural exchange
                        self.traditions[tribe1].exchange_culture(self.traditions[tribe2])
                        self.traditions[tribe2].exchange_culture(self.traditions[tribe1])

                        # Cuisine exchange
                        self.cuisines[tribe1].exchange_cuisine(self.cuisines[tribe2])
                        self.cuisines[tribe2].exchange_cuisine(self.cuisines[tribe1])

                        # Architecture exchange
                        self.architectures[tribe1].exchange_architecture(self.architectures[tribe2])
                        self.architectures[tribe2].exchange_architecture(self.architectures[tribe1])

                        # Social structure exchange
                        self.social_structures[tribe1].exchange_social_structure(self.social_structures[tribe2])
                        self.social_structures[tribe2].exchange_social_structure(self.social_structures[tribe1])

                        print(f"  📚 {tribe1} ↔ {tribe2}: Cultural exchange occurred")

        # Update cultural influence based on development
        for tribe_name, tribe_data in self.tribes.items():
            influence_factors = [
                tribe_data["population"] / 200,  # Population factor
                tribe_data["language_complexity"],  # Language development
                tribe_data["artistic_development"],  # Artistic development
                tribe_data.get("culinary_development", 1.0),  # Culinary development
                tribe_data.get("architectural_development", 1.0),  # Architectural development
                tribe_data.get("social_development", 1.0),  # Social development
                len(self.languages[tribe_name].vocabulary) / 50,  # Vocabulary size
                len(self.traditions[tribe_name].stories) / 10,  # Story repertoire
                len(self.cuisines[tribe_name].dishes) / 5,  # Culinary repertoire
                len(self.architectures[tribe_name].housing_designs) / 3,  # Architectural repertoire
                len(self.social_structures[tribe_name].social_roles) / 5,  # Social complexity
            ]
            tribe_data["cultural_influence"] = sum(influence_factors) / len(influence_factors)

    def get_cultural_summary(self) -> Dict:
        """Get a summary of the current cultural state."""
        summary = {
            "generation": self.generation,
            "tribes": {},
            "total_languages": len(self.languages),
            "total_stories": sum(len(t.stories) for t in self.traditions.values()),
            "total_rituals": sum(len(t.rituals) for t in self.traditions.values()),
            "total_music_styles": sum(len(t.music_styles) for t in self.traditions.values()),
            "total_dishes": sum(len(c.dishes) for c in self.cuisines.values()),
            "total_cooking_methods": sum(len(c.cooking_methods) for c in self.cuisines.values()),
            "total_housing_designs": sum(len(a.housing_designs) for a in self.architectures.values()),
            "total_monuments": sum(len(a.monuments) for a in self.architectures.values()),
            "total_social_roles": sum(len(s.social_roles) for s in self.social_structures.values()),
            "total_leadership_styles": sum(len(s.leadership_styles) for s in self.social_structures.values())
        }

        for tribe_name in self.tribes:
            summary["tribes"][tribe_name] = {
                "population": self.tribes[tribe_name]["population"],
                "cultural_influence": round(self.tribes[tribe_name]["cultural_influence"], 2),
                "language_complexity": round(self.tribes[tribe_name]["language_complexity"], 2),
                "artistic_development": round(self.tribes[tribe_name]["artistic_development"], 2),
                "culinary_development": round(self.tribes[tribe_name].get("culinary_development", 1.0), 2),
                "architectural_development": round(self.tribes[tribe_name].get("architectural_development", 1.0), 2),
                "social_development": round(self.tribes[tribe_name].get("social_development", 1.0), 2),
                "vocabulary_size": len(self.languages[tribe_name].vocabulary),
                "stories_count": len(self.traditions[tribe_name].stories),
                "rituals_count": len(self.traditions[tribe_name].rituals),
                "music_styles_count": len(self.traditions[tribe_name].music_styles),
                "dishes_count": len(self.cuisines[tribe_name].dishes),
                "cooking_methods_count": len(self.cuisines[tribe_name].cooking_methods),
                "housing_designs_count": len(self.architectures[tribe_name].housing_designs),
                "monuments_count": len(self.architectures[tribe_name].monuments),
                "social_roles_count": len(self.social_structures[tribe_name].social_roles),
                "leadership_styles_count": len(self.social_structures[tribe_name].leadership_styles)
            }

        return summary

    def save_cultural_data(self):
        """Save the current cultural state."""
        os.makedirs(ARTIFACTS_DIR, exist_ok=True)

        data = {
            "generation": self.generation,
            "tribes": self.tribes,
            "languages": {
                name: {
                    "vocabulary": lang.vocabulary,
                    "grammar_rules": lang.grammar_rules
                }
                for name, lang in self.languages.items()
            },
            "traditions": {
                name: {
                    "stories": trad.stories,
                    "rituals": trad.rituals,
                    "music_styles": trad.music_styles
                }
                for name, trad in self.traditions.items()
            },
            "cuisines": {
                name: {
                    "cooking_methods": cuisine.cooking_methods,
                    "ingredients": cuisine.ingredients,
                    "dishes": cuisine.dishes,
                    "meal_rituals": cuisine.meal_rituals
                }
                for name, cuisine in self.cuisines.items()
            },
            "architectures": {
                name: {
                    "building_styles": arch.building_styles,
                    "housing_designs": arch.housing_designs,
                    "monuments": arch.monuments,
                    "construction_materials": arch.construction_materials,
                    "building_techniques": arch.building_techniques
                }
                for name, arch in self.architectures.items()
            },
            "social_structures": {
                name: {
                    "leadership_styles": social.leadership_styles,
                    "family_structures": social.family_structures,
                    "social_roles": social.social_roles,
                    "decision_making": social.decision_making,
                    "social_norms": social.social_norms
                }
                for name, social in self.social_structures.items()
            }
        }

        with open(CULTURAL_DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load_cultural_data(self):
        """Load cultural state from file."""
        if not os.path.exists(CULTURAL_DATA_FILE):
            return False

        try:
            with open(CULTURAL_DATA_FILE, "r") as f:
                data = json.load(f)

            self.generation = data.get("generation", 0)
            self.tribes = data.get("tribes", {})

            # Reconstruct languages
            for name, lang_data in data.get("languages", {}).items():
                lang = Language(name)
                lang.vocabulary = lang_data.get("vocabulary", {})
                lang.grammar_rules = lang_data.get("grammar_rules", {})
                self.languages[name] = lang

            # Reconstruct traditions
            for name, trad_data in data.get("traditions", {}).items():
                trad = ArtisticTradition(name)
                trad.stories = trad_data.get("stories", [])
                trad.rituals = trad_data.get("rituals", [])
                trad.music_styles = trad_data.get("music_styles", [])
                self.traditions[name] = trad

            # Reconstruct cuisines
            for name, cuisine_data in data.get("cuisines", {}).items():
                cuisine = Cuisine(name)
                cuisine.cooking_methods = cuisine_data.get("cooking_methods", [])
                cuisine.ingredients = cuisine_data.get("ingredients", [])
                cuisine.dishes = cuisine_data.get("dishes", [])
                cuisine.meal_rituals = cuisine_data.get("meal_rituals", [])
                self.cuisines[name] = cuisine

            # Reconstruct architectures
            for name, arch_data in data.get("architectures", {}).items():
                arch = Architecture(name)
                arch.building_styles = arch_data.get("building_styles", [])
                arch.housing_designs = arch_data.get("housing_designs", [])
                arch.monuments = arch_data.get("monuments", [])
                arch.construction_materials = arch_data.get("construction_materials", [])
                arch.building_techniques = arch_data.get("building_techniques", [])
                self.architectures[name] = arch

            # Reconstruct social structures
            for name, social_data in data.get("social_structures", {}).items():
                social = SocialStructure(name)
                social.leadership_styles = social_data.get("leadership_styles", [])
                social.family_structures = social_data.get("family_structures", [])
                social.social_roles = social_data.get("social_roles", [])
                social.decision_making = social_data.get("decision_making", [])
                social.social_norms = social_data.get("social_norms", [])
                self.social_structures[name] = social

            return True
        except Exception as e:
            print(f"Error loading cultural data: {e}")
            return False

# --------------------------------------------------------------------------------------
# Main Functions
# --------------------------------------------------------------------------------------

def run_cultural_simulation(
    num_tribes: int = 5,
    generations: int = 50,
    cultural_exchange_rate: float = CULTURAL_EXCHANGE_RATE,
    interactive: bool = False,
    save_interval: int = 10
):
    """Run the cultural development simulation."""
    print("🎭 AI SANDBOX - CULTURAL DEVELOPMENT SYSTEM")
    print("=" * 60)
    print(f"Tribes: {num_tribes}")
    print(f"Generations: {generations}")
    print(f"Cultural Exchange Rate: {cultural_exchange_rate}")
    print(f"Interactive Mode: {interactive}")
    print("=" * 60)

    # Initialize or load cultural system
    cultural_system = CulturalSystem(num_tribes)

    if not cultural_system.load_cultural_data():
        print("🌱 Initializing new cultural simulation...")
    else:
        print(f"📚 Resuming from generation {cultural_system.generation}...")

    try:
        for gen in range(cultural_system.generation + 1, cultural_system.generation + generations + 1):
            start_time = time.time()

            # Simulate one generation
            cultural_system.simulate_generation(cultural_exchange_rate)

            # Periodic saving
            if gen % save_interval == 0:
                cultural_system.save_cultural_data()
                print(f"💾 Cultural data saved at generation {gen}")

            # Display summary
            if interactive or gen % 10 == 0:
                summary = cultural_system.get_cultural_summary()
                print(f"\n📊 Generation {gen} Summary:")
                print(f"   Total Stories: {summary['total_stories']}")
                print(f"   Total Rituals: {summary['total_rituals']}")
                print(f"   Total Music Styles: {summary['total_music_styles']}")
                print(f"   Total Dishes: {summary['total_dishes']}")
                print(f"   Total Cooking Methods: {summary['total_cooking_methods']}")
                print(f"   Total Housing Designs: {summary['total_housing_designs']}")
                print(f"   Total Monuments: {summary['total_monuments']}")
                print(f"   Total Social Roles: {summary['total_social_roles']}")
                print(f"   Total Leadership Styles: {summary['total_leadership_styles']}")
                print(f"   Total Languages: {summary['total_languages']}")

                # Show top 3 most influential tribes
                sorted_tribes = sorted(
                    summary['tribes'].items(),
                    key=lambda x: x[1]['cultural_influence'],
                    reverse=True
                )
                print("\nMost Culturally Influential Tribes:")
                for i, (name, data) in enumerate(sorted_tribes[:3]):
                    print(f"   {i+1}. {name}: {data['cultural_influence']} influence")

            gen_time = time.time() - start_time
            if interactive:
                print(f"Generation completed in {gen_time:.2f} seconds")
                input("Press Enter to continue...")

        # Final save
        cultural_system.save_cultural_data()
        print("\nFinal cultural data saved!")
        print(f"Cultural simulation completed after {generations} generations!")

    except KeyboardInterrupt:
        print("\nCultural simulation interrupted by user")
        cultural_system.save_cultural_data()
        print("Cultural data saved before exit")

def interactive_cultural_demo():
    """Run an interactive demonstration of the cultural system."""
    print("🎭 CULTURAL DEVELOPMENT SYSTEM - INTERACTIVE DEMO")
    print("=" * 60)

    cultural_system = CulturalSystem(4)

    while True:
        print("\nAvailable Actions:")
        print("1. Simulate one generation")
        print("2. View cultural summary")
        print("3. Show tribe details")
        print("4. Show language evolution")
        print("5. Show artistic traditions")
        print("6. Save current state")
        print("7. Exit")

        try:
            choice = input("\nChoose an action (1-7): ").strip()

            if choice == "1":
                cultural_system.simulate_generation()
                print(f"✅ Generation {cultural_system.generation} completed")

            elif choice == "2":
                summary = cultural_system.get_cultural_summary()
                print(f"\n📊 Cultural Summary (Generation {summary['generation']}):")
                print(f"   Total Stories: {summary['total_stories']}")
                print(f"   Total Rituals: {summary['total_rituals']}")
                print(f"   Total Music Styles: {summary['total_music_styles']}")

            elif choice == "3":
                summary = cultural_system.get_cultural_summary()
                print("\n🏛️ Tribe Details:")
                for name, data in summary['tribes'].items():
                    print(f"   {name}:")
                    print(f"     Population: {data['population']}")
                    print(f"     Cultural Influence: {data['cultural_influence']}")
                    print(f"     Stories: {data['stories_count']}")
                    print(f"     Rituals: {data['rituals_count']}")

            elif choice == "4":
                print("\n📝 Language Evolution:")
                for name, language in cultural_system.languages.items():
                    vocab_size = len(language.vocabulary)
                    print(f"   {name}: {vocab_size} words")
                    if vocab_size > 0:
                        sample_words = list(language.vocabulary.items())[:3]
                        for concept, word in sample_words:
                            print(f"     {concept} → {word}")

            elif choice == "5":
                print("\n🎨 Artistic Traditions:")
                for name, tradition in cultural_system.traditions.items():
                    print(f"   {name}:")
                    print(f"     Stories: {len(tradition.stories)}")
                    print(f"     Rituals: {len(tradition.rituals)}")
                    print(f"     Music Styles: {len(tradition.music_styles)}")

            elif choice == "6":
                cultural_system.save_cultural_data()
                print("💾 Cultural data saved!")

            elif choice == "7":
                print("👋 Goodbye!")
                break

            else:
                print("❌ Invalid choice. Please select 1-7.")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Cultural Development System - AI Sandbox")
    parser.add_argument("--tribes", type=int, default=5, help="Number of tribes to simulate")
    parser.add_argument("--generations", type=int, default=50, help="Number of generations to simulate")
    parser.add_argument("--cultural-exchange-rate", type=float, default=CULTURAL_EXCHANGE_RATE,
                       help="Rate of cultural exchange between tribes")
    parser.add_argument("--interactive", action="store_true",
                       help="Run in interactive mode")
    parser.add_argument("--demo", action="store_true",
                       help="Run interactive cultural demo")
    parser.add_argument("--save-interval", type=int, default=10,
                       help="Save data every N generations")

    args = parser.parse_args()

    if args.demo:
        interactive_cultural_demo()
    elif args.interactive:
        run_cultural_simulation(
            num_tribes=args.tribes,
            generations=args.generations,
            cultural_exchange_rate=args.cultural_exchange_rate,
            interactive=True,
            save_interval=args.save_interval
        )
    else:
        run_cultural_simulation(
            num_tribes=args.tribes,
            generations=args.generations,
            cultural_exchange_rate=args.cultural_exchange_rate,
            interactive=False,
            save_interval=args.save_interval
        )

if __name__ == "__main__":
    main()