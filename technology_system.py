"""
Technology/Innovation System for AI Sandbox
Enables tribes to unlock technologies through sustained actions, creating dynamic growth/collapse cycles.
"""

import json
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class TechnologyCategory(Enum):
    """Categories of technologies available for research."""
    AGRICULTURE = "agriculture"
    CRAFTING = "crafting"
    WARFARE = "warfare"
    SOCIAL = "social"
    SPIRITUAL = "spiritual"
    EXPLORATION = "exploration"


class TechnologyEra(Enum):
    """Technological eras that unlock progressively advanced technologies."""
    STONE_AGE = "stone_age"
    BRONZE_AGE = "bronze_age"
    IRON_AGE = "iron_age"
    MEDIEVAL = "medieval"


@dataclass
class TechnologyRequirement:
    """Requirements needed to unlock a technology."""
    action_type: str  # Type of action (gathering, hunting, crafting, etc.)
    action_count: int  # Number of actions needed
    time_invested: int  # Ticks of sustained activity
    prerequisite_techs: List[str] = field(default_factory=list)  # Required technologies
    resource_cost: Dict[str, float] = field(default_factory=dict)  # Resource costs


@dataclass
class TechnologyEffect:
    """Effects that a technology provides when unlocked."""
    population_multiplier: float = 1.0  # Multiplier for population capacity
    resource_multipliers: Dict[str, float] = field(default_factory=dict)  # Resource production multipliers
    reproduction_bonus: float = 0.0  # Bonus to reproduction rate
    mortality_reduction: float = 0.0  # Reduction in mortality rate
    combat_bonus: float = 0.0  # Combat effectiveness bonus
    exploration_range: int = 0  # Additional exploration range
    special_abilities: List[str] = field(default_factory=list)  # Special abilities unlocked


class TradeType(Enum):
    """Types of technology trades available."""
    DIRECT_EXCHANGE = "direct_exchange"  # Technology for technology
    RESOURCE_PAYMENT = "resource_payment"  # Technology for resources
    ALLIANCE_FORMATION = "alliance_formation"  # Technology for alliance
    ESPIONAGE = "espionage"  # Steal technology through spying


@dataclass
class TechnologyTradeOffer:
    """Represents a technology trade offer between tribes."""
    offering_tribe: str
    receiving_tribe: str
    offered_technology: str
    requested_technology: Optional[str] = None  # For direct exchange
    resource_payment: Dict[str, float] = field(default_factory=dict)  # For resource payment
    trade_type: TradeType = TradeType.DIRECT_EXCHANGE
    diplomatic_bonus: float = 0.0  # Relationship bonus from successful trade
    risk_factor: float = 0.0  # Chance of trade failure or betrayal
    created_tick: int = 0
    expires_tick: int = 0


@dataclass
class TechnologyTrade:
    """Represents a completed technology trade."""
    offering_tribe: str
    receiving_tribe: str
    technology_transferred: str
    trade_type: TradeType
    resources_exchanged: Dict[str, float] = field(default_factory=dict)
    relationship_change: float = 0.0
    completed_tick: int = 0
    success: bool = True


@dataclass
class Technology:
    """Represents a technology that tribes can research and unlock."""
    id: str
    name: str
    description: str
    category: TechnologyCategory
    era: TechnologyEra
    requirement: TechnologyRequirement
    effect: TechnologyEffect
    research_time: int  # Base ticks needed to research
    unlock_message: str  # Message shown when unlocked
    trade_value: int = 100  # Base value for trading (1-1000 scale)
    trade_rarity: str = "common"  # common, rare, epic, legendary


class TechnologyManager:
    """Manages technology research and effects for tribes."""

    def __init__(self):
        self.technologies = self._load_technologies()
        self.tribe_research_progress: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.unlocked_technologies: Dict[str, Set[str]] = {}

        # Technology trading system
        self.pending_trade_offers: Dict[str, List[TechnologyTradeOffer]] = {}
        self.completed_trades: List[TechnologyTrade] = []
        self.trade_relationships: Dict[str, Dict[str, float]] = {}  # tribe -> tribe -> relationship score

    def _load_technologies(self) -> Dict[str, Technology]:
        """Load all available technologies."""
        technologies = {}

        # Agriculture Technologies
        technologies["farming"] = Technology(
            id="farming",
            name="Primitive Farming",
            description="Learn to cultivate plants for reliable food production",
            category=TechnologyCategory.AGRICULTURE,
            era=TechnologyEra.STONE_AGE,
            requirement=TechnologyRequirement(
                action_type="gathering",
                action_count=50,
                time_invested=200,
                resource_cost={"food": 20.0}
            ),
            effect=TechnologyEffect(
                population_multiplier=1.3,
                resource_multipliers={"food": 1.5, "plant": 2.0},
                reproduction_bonus=0.02,
                special_abilities=["cultivate_crops", "store_food"]
            ),
            research_time=300,
            unlock_message="🌾 Your tribe has discovered farming! Food production has increased significantly.",
            trade_value=150,
            trade_rarity="common"
        )

        technologies["irrigation"] = Technology(
            id="irrigation",
            name="Irrigation Systems",
            description="Develop systems to control water for enhanced agriculture",
            category=TechnologyCategory.AGRICULTURE,
            era=TechnologyEra.BRONZE_AGE,
            requirement=TechnologyRequirement(
                action_type="gathering",
                action_count=100,
                time_invested=400,
                prerequisite_techs=["farming"],
                resource_cost={"food": 50.0, "wood": 30.0}
            ),
            effect=TechnologyEffect(
                population_multiplier=1.2,
                resource_multipliers={"food": 1.8, "plant": 2.5},
                reproduction_bonus=0.03,
                special_abilities=["advanced_farming", "water_control"]
            ),
            research_time=500,
            unlock_message="💧 Irrigation systems allow your tribe to cultivate land more effectively!",
            trade_value=300,
            trade_rarity="rare"
        )

        # Crafting Technologies
        technologies["tools"] = Technology(
            id="tools",
            name="Stone Tools",
            description="Craft improved tools for better resource gathering",
            category=TechnologyCategory.CRAFTING,
            era=TechnologyEra.STONE_AGE,
            requirement=TechnologyRequirement(
                action_type="crafting",
                action_count=30,
                time_invested=150,
                resource_cost={"stone": 15.0}
            ),
            effect=TechnologyEffect(
                resource_multipliers={"mineral": 1.4, "wood": 1.3},
                special_abilities=["improved_tools", "better_weapons"]
            ),
            research_time=200,
            unlock_message="🔨 Stone tools make gathering resources much more efficient!",
            trade_value=120,
            trade_rarity="common"
        )

        technologies["weapons"] = Technology(
            id="weapons",
            name="Advanced Weapons",
            description="Develop better weapons for hunting and defense",
            category=TechnologyCategory.WARFARE,
            era=TechnologyEra.STONE_AGE,
            requirement=TechnologyRequirement(
                action_type="hunting",
                action_count=40,
                time_invested=180,
                prerequisite_techs=["tools"],
                resource_cost={"wood": 25.0, "stone": 20.0}
            ),
            effect=TechnologyEffect(
                resource_multipliers={"animal": 1.6},
                combat_bonus=0.3,
                special_abilities=["advanced_hunting", "better_defense"]
            ),
            research_time=250,
            unlock_message="⚔️ Advanced weapons make hunting more successful and defense stronger!",
            trade_value=180,
            trade_rarity="common"
        )

        # Social Technologies
        technologies["organization"] = Technology(
            id="organization",
            name="Tribal Organization",
            description="Develop structured social systems for better coordination",
            category=TechnologyCategory.SOCIAL,
            era=TechnologyEra.STONE_AGE,
            requirement=TechnologyRequirement(
                action_type="social",
                action_count=25,
                time_invested=120
            ),
            effect=TechnologyEffect(
                population_multiplier=1.15,
                reproduction_bonus=0.01,
                special_abilities=["coordinated_hunting", "resource_sharing"]
            ),
            research_time=180,
            unlock_message="👥 Tribal organization improves coordination and resource management!"
        )

        technologies["diplomacy"] = Technology(
            id="diplomacy",
            name="Diplomatic Relations",
            description="Learn to form alliances and trade with other tribes",
            category=TechnologyCategory.SOCIAL,
            era=TechnologyEra.BRONZE_AGE,
            requirement=TechnologyRequirement(
                action_type="social",
                action_count=60,
                time_invested=300,
                prerequisite_techs=["organization"],
                resource_cost={"food": 30.0}
            ),
            effect=TechnologyEffect(
                population_multiplier=1.1,
                special_abilities=["trade_agreements", "alliances", "peace_treaties"]
            ),
            research_time=400,
            unlock_message="🤝 Diplomatic relations open new opportunities for trade and alliances!"
        )

        # Spiritual Technologies
        technologies["rituals"] = Technology(
            id="rituals",
            name="Spiritual Rituals",
            description="Develop spiritual practices that boost morale and reproduction",
            category=TechnologyCategory.SPIRITUAL,
            era=TechnologyEra.STONE_AGE,
            requirement=TechnologyRequirement(
                action_type="spiritual",
                action_count=20,
                time_invested=100
            ),
            effect=TechnologyEffect(
                reproduction_bonus=0.015,
                mortality_reduction=0.05,
                special_abilities=["morale_boost", "healing_rituals"]
            ),
            research_time=150,
            unlock_message="🙏 Spiritual rituals strengthen your tribe's resolve and health!"
        )

        # Exploration Technologies
        technologies["navigation"] = Technology(
            id="navigation",
            name="Basic Navigation",
            description="Learn to navigate and explore farther territories",
            category=TechnologyCategory.EXPLORATION,
            era=TechnologyEra.STONE_AGE,
            requirement=TechnologyRequirement(
                action_type="exploration",
                action_count=35,
                time_invested=160
            ),
            effect=TechnologyEffect(
                exploration_range=2,
                special_abilities=["map_territory", "find_resources"]
            ),
            research_time=220,
            unlock_message="🗺️ Navigation skills allow your tribe to explore new lands!"
        )

        # ===== BRONZE AGE TECHNOLOGIES =====

        # Crafting - Bronze Age
        technologies["metalworking"] = Technology(
            id="metalworking",
            name="Metalworking",
            description="Learn to extract and work metals from ore",
            category=TechnologyCategory.CRAFTING,
            era=TechnologyEra.BRONZE_AGE,
            requirement=TechnologyRequirement(
                action_type="crafting",
                action_count=80,
                time_invested=350,
                prerequisite_techs=["tools"],
                resource_cost={"mineral": 40.0, "wood": 20.0}
            ),
            effect=TechnologyEffect(
                resource_multipliers={"mineral": 1.6, "ore": 2.0},
                special_abilities=["smelt_metals", "forge_tools", "create_alloys"]
            ),
            research_time=450,
            unlock_message="🔥 Metalworking revolution! Your tribe can now forge metal tools and weapons!",
            trade_value=400,
            trade_rarity="rare"
        )

        technologies["pottery"] = Technology(
            id="pottery",
            name="Pottery",
            description="Learn to shape and fire clay into useful containers",
            category=TechnologyCategory.CRAFTING,
            era=TechnologyEra.BRONZE_AGE,
            requirement=TechnologyRequirement(
                action_type="crafting",
                action_count=45,
                time_invested=200,
                prerequisite_techs=["tools"],
                resource_cost={"clay": 15.0}
            ),
            effect=TechnologyEffect(
                resource_multipliers={"food": 1.3},
                special_abilities=["store_food_long_term", "cook_advanced_foods", "ceramic_tools"]
            ),
            research_time=300,
            unlock_message="🏺 Pottery allows better food storage and preservation!",
            trade_value=250,
            trade_rarity="common"
        )

        # Agriculture - Bronze Age
        technologies["animal_domestication"] = Technology(
            id="animal_domestication",
            name="Animal Domestication",
            description="Learn to domesticate and breed animals for labor and food",
            category=TechnologyCategory.AGRICULTURE,
            era=TechnologyEra.BRONZE_AGE,
            requirement=TechnologyRequirement(
                action_type="gathering",
                action_count=70,
                time_invested=320,
                prerequisite_techs=["farming"],
                resource_cost={"animal": 25.0, "food": 30.0}
            ),
            effect=TechnologyEffect(
                population_multiplier=1.25,
                resource_multipliers={"animal": 1.8, "food": 1.4, "milk": 1.0},
                reproduction_bonus=0.025,
                special_abilities=["animal_labor", "dairy_products", "transport_animals"]
            ),
            research_time=400,
            unlock_message="🐄 Animal domestication provides reliable labor and food sources!"
        )

        technologies["selective_breeding"] = Technology(
            id="selective_breeding",
            name="Selective Breeding",
            description="Develop techniques to breed better crops and livestock",
            category=TechnologyCategory.AGRICULTURE,
            era=TechnologyEra.BRONZE_AGE,
            requirement=TechnologyRequirement(
                action_type="gathering",
                action_count=90,
                time_invested=380,
                prerequisite_techs=["farming", "animal_domestication"],
                resource_cost={"food": 40.0}
            ),
            effect=TechnologyEffect(
                population_multiplier=1.35,
                resource_multipliers={"food": 2.0, "plant": 2.2, "animal": 1.7},
                reproduction_bonus=0.035,
                special_abilities=["improved_crops", "better_livestock", "disease_resistance"]
            ),
            research_time=500,
            unlock_message="🌱 Selective breeding creates superior crops and livestock!"
        )

        # Warfare - Bronze Age
        technologies["bronze_weapons"] = Technology(
            id="bronze_weapons",
            name="Bronze Weapons",
            description="Forge weapons from bronze for superior combat effectiveness",
            category=TechnologyCategory.WARFARE,
            era=TechnologyEra.BRONZE_AGE,
            requirement=TechnologyRequirement(
                action_type="crafting",
                action_count=60,
                time_invested=280,
                prerequisite_techs=["weapons", "metalworking"],
                resource_cost={"ore": 35.0, "wood": 25.0}
            ),
            effect=TechnologyEffect(
                resource_multipliers={"animal": 1.9},
                combat_bonus=0.5,
                special_abilities=["bronze_armor", "siege_weapons", "military_tactics"]
            ),
            research_time=380,
            unlock_message="⚔️ Bronze weapons give your warriors a decisive advantage in battle!"
        )

        technologies["fortifications"] = Technology(
            id="fortifications",
            name="Fortifications",
            description="Build defensive structures to protect settlements",
            category=TechnologyCategory.WARFARE,
            era=TechnologyEra.BRONZE_AGE,
            requirement=TechnologyRequirement(
                action_type="crafting",
                action_count=75,
                time_invested=350,
                prerequisite_techs=["tools", "organization"],
                resource_cost={"stone": 50.0, "wood": 40.0}
            ),
            effect=TechnologyEffect(
                population_multiplier=1.2,
                combat_bonus=0.4,
                special_abilities=["defensive_structures", "safe_storage", "settlement_protection"]
            ),
            research_time=450,
            unlock_message="🏰 Fortifications provide security and allow permanent settlements!"
        )

        # Social - Bronze Age
        technologies["writing"] = Technology(
            id="writing",
            name="Writing Systems",
            description="Develop systems to record information and preserve knowledge",
            category=TechnologyCategory.SOCIAL,
            era=TechnologyEra.BRONZE_AGE,
            requirement=TechnologyRequirement(
                action_type="social",
                action_count=55,
                time_invested=280,
                prerequisite_techs=["organization"],
                resource_cost={"stone": 20.0}
            ),
            effect=TechnologyEffect(
                population_multiplier=1.3,
                special_abilities=["record_history", "trade_records", "legal_systems", "knowledge_preservation"]
            ),
            research_time=420,
            unlock_message="📜 Writing systems preserve knowledge and enable complex societies!"
        )

        technologies["trade_networks"] = Technology(
            id="trade_networks",
            name="Trade Networks",
            description="Establish extensive trade routes and merchant systems",
            category=TechnologyCategory.SOCIAL,
            era=TechnologyEra.BRONZE_AGE,
            requirement=TechnologyRequirement(
                action_type="social",
                action_count=65,
                time_invested=320,
                prerequisite_techs=["diplomacy"],
                resource_cost={"food": 35.0}
            ),
            effect=TechnologyEffect(
                population_multiplier=1.25,
                resource_multipliers={"food": 1.2, "wood": 1.2, "ore": 1.2},
                special_abilities=["merchant_class", "currency_system", "economic_specialization"]
            ),
            research_time=480,
            unlock_message="💰 Trade networks create wealth and connect distant civilizations!"
        )

        # ===== IRON AGE TECHNOLOGIES =====

        # Crafting - Iron Age
        technologies["iron_smelting"] = Technology(
            id="iron_smelting",
            name="Iron Smelting",
            description="Master the difficult process of smelting iron from ore",
            category=TechnologyCategory.CRAFTING,
            era=TechnologyEra.IRON_AGE,
            requirement=TechnologyRequirement(
                action_type="crafting",
                action_count=120,
                time_invested=500,
                prerequisite_techs=["metalworking"],
                resource_cost={"ore": 60.0, "wood": 40.0}
            ),
            effect=TechnologyEffect(
                resource_multipliers={"mineral": 1.8, "ore": 2.5},
                special_abilities=["iron_tools", "advanced_forging", "machinery"]
            ),
            research_time=600,
            unlock_message="🔥 Iron smelting unlocks the power of the strongest metal!",
            trade_value=600,
            trade_rarity="epic"
        )

        # Warfare - Iron Age
        technologies["iron_weapons"] = Technology(
            id="iron_weapons",
            name="Iron Weapons",
            description="Forge superior weapons from iron for unmatched combat power",
            category=TechnologyCategory.WARFARE,
            era=TechnologyEra.IRON_AGE,
            requirement=TechnologyRequirement(
                action_type="crafting",
                action_count=100,
                time_invested=450,
                prerequisite_techs=["bronze_weapons", "iron_smelting"],
                resource_cost={"ore": 50.0, "wood": 30.0}
            ),
            effect=TechnologyEffect(
                resource_multipliers={"animal": 2.1},
                combat_bonus=0.7,
                special_abilities=["iron_armor", "advanced_siege", "professional_army"]
            ),
            research_time=550,
            unlock_message="⚔️ Iron weapons make your tribe nearly invincible in battle!",
            trade_value=700,
            trade_rarity="epic"
        )

        technologies["military_organization"] = Technology(
            id="military_organization",
            name="Military Organization",
            description="Develop structured military units and command systems",
            category=TechnologyCategory.WARFARE,
            era=TechnologyEra.IRON_AGE,
            requirement=TechnologyRequirement(
                action_type="social",
                action_count=85,
                time_invested=400,
                prerequisite_techs=["fortifications", "writing"],
                resource_cost={"food": 45.0}
            ),
            effect=TechnologyEffect(
                population_multiplier=1.15,
                combat_bonus=0.6,
                special_abilities=["military_hierarchy", "tactical_training", "logistics"]
            ),
            research_time=520,
            unlock_message="🎖️ Military organization creates disciplined and effective armies!"
        )

        # Agriculture - Iron Age
        technologies["advanced_farming"] = Technology(
            id="advanced_farming",
            name="Advanced Farming",
            description="Develop advanced agricultural techniques and crop rotation",
            category=TechnologyCategory.AGRICULTURE,
            era=TechnologyEra.IRON_AGE,
            requirement=TechnologyRequirement(
                action_type="gathering",
                action_count=110,
                time_invested=480,
                prerequisite_techs=["irrigation", "selective_breeding"],
                resource_cost={"food": 55.0, "wood": 25.0}
            ),
            effect=TechnologyEffect(
                population_multiplier=1.5,
                resource_multipliers={"food": 2.5, "plant": 3.0},
                reproduction_bonus=0.045,
                special_abilities=["crop_rotation", "fertilizers", "large_scale_farming"]
            ),
            research_time=650,
            unlock_message="🌾 Advanced farming techniques maximize agricultural output!"
        )

        # Social - Iron Age
        technologies["organized_religion"] = Technology(
            id="organized_religion",
            name="Organized Religion",
            description="Establish formal religious institutions and priesthood",
            category=TechnologyCategory.SPIRITUAL,
            era=TechnologyEra.IRON_AGE,
            requirement=TechnologyRequirement(
                action_type="spiritual",
                action_count=70,
                time_invested=360,
                prerequisite_techs=["rituals", "writing"],
                resource_cost={"food": 40.0}
            ),
            effect=TechnologyEffect(
                population_multiplier=1.2,
                reproduction_bonus=0.02,
                mortality_reduction=0.08,
                special_abilities=["religious_institutions", "moral_authority", "cultural_unity"]
            ),
            research_time=500,
            unlock_message="⛪ Organized religion provides social cohesion and spiritual guidance!"
        )

        technologies["architecture"] = Technology(
            id="architecture",
            name="Architecture",
            description="Master the art of designing and building large structures",
            category=TechnologyCategory.CRAFTING,
            era=TechnologyEra.IRON_AGE,
            requirement=TechnologyRequirement(
                action_type="crafting",
                action_count=95,
                time_invested=420,
                prerequisite_techs=["pottery", "fortifications"],
                resource_cost={"stone": 60.0, "wood": 35.0}
            ),
            effect=TechnologyEffect(
                population_multiplier=1.4,
                special_abilities=["monumental_buildings", "urban_planning", "engineering"]
            ),
            research_time=580,
            unlock_message="🏛️ Architecture enables the construction of great cities and monuments!"
        )

        # Exploration - Advanced
        technologies["cartography"] = Technology(
            id="cartography",
            name="Cartography",
            description="Create detailed maps and navigation systems",
            category=TechnologyCategory.EXPLORATION,
            era=TechnologyEra.IRON_AGE,
            requirement=TechnologyRequirement(
                action_type="exploration",
                action_count=80,
                time_invested=380,
                prerequisite_techs=["navigation", "writing"],
                resource_cost={"stone": 25.0}
            ),
            effect=TechnologyEffect(
                exploration_range=5,
                special_abilities=["detailed_maps", "navigation_instruments", "trade_routes"]
            ),
            research_time=480,
            unlock_message="🗺️ Cartography enables precise navigation and exploration!"
        )

        # ===== MEDIEVAL TECHNOLOGIES =====

        # Warfare - Medieval
        technologies["steel_weapons"] = Technology(
            id="steel_weapons",
            name="Steel Weapons",
            description="Master steel production for the finest weapons and armor",
            category=TechnologyCategory.WARFARE,
            era=TechnologyEra.MEDIEVAL,
            requirement=TechnologyRequirement(
                action_type="crafting",
                action_count=140,
                time_invested=600,
                prerequisite_techs=["iron_weapons"],
                resource_cost={"ore": 80.0, "wood": 50.0}
            ),
            effect=TechnologyEffect(
                resource_multipliers={"animal": 2.3},
                combat_bonus=0.9,
                special_abilities=["steel_armor", "plate_armor", "chivalry"]
            ),
            research_time=750,
            unlock_message="⚔️ Steel weapons represent the pinnacle of medieval warfare!",
            trade_value=850,
            trade_rarity="legendary"
        )

        technologies["siege_engineering"] = Technology(
            id="siege_engineering",
            name="Siege Engineering",
            description="Develop machines and tactics for assaulting fortifications",
            category=TechnologyCategory.WARFARE,
            era=TechnologyEra.MEDIEVAL,
            requirement=TechnologyRequirement(
                action_type="crafting",
                action_count=130,
                time_invested=550,
                prerequisite_techs=["military_organization", "architecture"],
                resource_cost={"wood": 70.0, "ore": 60.0}
            ),
            effect=TechnologyEffect(
                combat_bonus=0.8,
                special_abilities=["siege_towers", "catapults", "mining_tactics"]
            ),
            research_time=700,
            unlock_message="🏰 Siege engineering allows conquest of even the strongest fortresses!",
            trade_value=750,
            trade_rarity="epic"
        )

        # Social - Medieval
        technologies["feudalism"] = Technology(
            id="feudalism",
            name="Feudal System",
            description="Establish a hierarchical social and political system",
            category=TechnologyCategory.SOCIAL,
            era=TechnologyEra.MEDIEVAL,
            requirement=TechnologyRequirement(
                action_type="social",
                action_count=100,
                time_invested=480,
                prerequisite_techs=["writing", "military_organization"],
                resource_cost={"food": 60.0}
            ),
            effect=TechnologyEffect(
                population_multiplier=1.6,
                special_abilities=["social_hierarchy", "vassalage", "nobility", "legal_codes"]
            ),
            research_time=650,
            unlock_message="👑 Feudalism creates structured societies with clear social roles!",
            trade_value=500,
            trade_rarity="rare"
        )

        technologies["guilds"] = Technology(
            id="guilds",
            name="Craft Guilds",
            description="Organize artisans into professional guilds and apprenticeships",
            category=TechnologyCategory.SOCIAL,
            era=TechnologyEra.MEDIEVAL,
            requirement=TechnologyRequirement(
                action_type="crafting",
                action_count=90,
                time_invested=420,
                prerequisite_techs=["trade_networks", "architecture"],
                resource_cost={"wood": 40.0}
            ),
            effect=TechnologyEffect(
                resource_multipliers={"wood": 1.5, "ore": 1.5, "stone": 1.5},
                special_abilities=["quality_control", "apprenticeship", "craft_secrets"]
            ),
            research_time=550,
            unlock_message="⚒️ Guilds ensure high-quality craftsmanship and knowledge preservation!",
            trade_value=450,
            trade_rarity="rare"
        )

        # Agriculture - Medieval
        technologies["three_field_system"] = Technology(
            id="three_field_system",
            name="Three-Field System",
            description="Implement advanced crop rotation for maximum agricultural efficiency",
            category=TechnologyCategory.AGRICULTURE,
            era=TechnologyEra.MEDIEVAL,
            requirement=TechnologyRequirement(
                action_type="gathering",
                action_count=120,
                time_invested=520,
                prerequisite_techs=["advanced_farming"],
                resource_cost={"food": 70.0}
            ),
            effect=TechnologyEffect(
                population_multiplier=1.7,
                resource_multipliers={"food": 3.0, "plant": 3.5},
                reproduction_bonus=0.055,
                special_abilities=["crop_rotation", "fallow_fields", "sustainable_farming"]
            ),
            research_time=720,
            unlock_message="🌾 Three-field system maximizes agricultural productivity!",
            trade_value=400,
            trade_rarity="rare"
        )

        # Spiritual - Medieval
        technologies["monasticism"] = Technology(
            id="monasticism",
            name="Monastic Orders",
            description="Establish religious communities dedicated to learning and service",
            category=TechnologyCategory.SPIRITUAL,
            era=TechnologyEra.MEDIEVAL,
            requirement=TechnologyRequirement(
                action_type="spiritual",
                action_count=85,
                time_invested=400,
                prerequisite_techs=["organized_religion", "writing"],
                resource_cost={"food": 50.0}
            ),
            effect=TechnologyEffect(
                population_multiplier=1.25,
                reproduction_bonus=0.025,
                mortality_reduction=0.1,
                special_abilities=["scholarship", "healing_centers", "education"]
            ),
            research_time=580,
            unlock_message="⛪ Monasteries become centers of learning and healing!",
            trade_value=350,
            trade_rarity="uncommon"
        )

        return technologies

    def start_research(self, tribe_id: str, tech_id: str) -> bool:
        """Start researching a technology for a tribe."""
        if tech_id not in self.technologies:
            return False

        if tribe_id not in self.tribe_research_progress:
            self.tribe_research_progress[tribe_id] = {}

        if tech_id in self.tribe_research_progress[tribe_id]:
            return False  # Already researching

        # Check prerequisites
        tech = self.technologies[tech_id]
        unlocked = self.unlocked_technologies.get(tribe_id, set())

        for prereq in tech.requirement.prerequisite_techs:
            if prereq not in unlocked:
                return False

        # Initialize research progress
        self.tribe_research_progress[tribe_id][tech_id] = {
            "progress": 0,
            "action_count": 0,
            "time_invested": 0,
            "started_tick": None
        }

        return True

    def update_research(self, tribe_id: str, action_type: str, tick: int) -> List[str]:
        """Update research progress for a tribe based on their actions."""
        if tribe_id not in self.tribe_research_progress:
            return []

        unlocked_techs = []

        for tech_id, progress in list(self.tribe_research_progress[tribe_id].items()):
            tech = self.technologies[tech_id]

            # Initialize start tick if not set
            if progress["started_tick"] is None:
                progress["started_tick"] = tick

            # Update progress based on action type
            if action_type == tech.requirement.action_type:
                progress["action_count"] += 1
                progress["time_invested"] += 1

                # Calculate research progress
                action_progress = min(1.0, progress["action_count"] / tech.requirement.action_count)
                time_progress = min(1.0, progress["time_invested"] / tech.requirement.time_invested)
                progress["progress"] = min(action_progress, time_progress)

                # Check if technology is complete
                if progress["progress"] >= 1.0:
                    self._unlock_technology(tribe_id, tech_id)
                    unlocked_techs.append(tech_id)
                    del self.tribe_research_progress[tribe_id][tech_id]

        return unlocked_techs

    def _unlock_technology(self, tribe_id: str, tech_id: str):
        """Unlock a technology for a tribe."""
        if tribe_id not in self.unlocked_technologies:
            self.unlocked_technologies[tribe_id] = set()

        self.unlocked_technologies[tribe_id].add(tech_id)

        tech = self.technologies[tech_id]
        print(f"[TECHNOLOGY] {tribe_id} unlocked: {tech.name}")
        print(f"[TECHNOLOGY] {tech.unlock_message}")

        # Trigger technology events
        self._trigger_technology_events(tribe_id, tech_id)

    def _trigger_technology_events(self, tribe_id: str, tech_id: str):
        """Trigger events related to technology unlocks."""
        tech = self.technologies[tech_id]

        # Technology-specific events
        if tech_id == "farming":
            self._trigger_farming_discovery_event(tribe_id)
        elif tech_id == "tools":
            self._trigger_tool_discovery_event(tribe_id)
        elif tech_id == "weapons":
            self._trigger_weapon_discovery_event(tribe_id)
        elif tech_id == "irrigation":
            self._trigger_irrigation_event(tribe_id)
        elif tech_id == "metalworking":
            self._trigger_metalworking_event(tribe_id)
        elif tech_id == "iron_smelting":
            self._trigger_iron_age_event(tribe_id)
        elif tech_id == "writing":
            self._trigger_literacy_event(tribe_id)
        elif tech_id == "steel_weapons":
            self._trigger_medieval_revolution_event(tribe_id)

        # Category-based events
        if tech.category == TechnologyCategory.AGRICULTURE:
            self._trigger_agricultural_revolution_event(tribe_id)
        elif tech.category == TechnologyCategory.WARFARE:
            self._trigger_warfare_revolution_event(tribe_id)
        elif tech.category == TechnologyCategory.CRAFTING:
            self._trigger_crafting_revolution_event(tribe_id)

        # Era-based events
        if tech.era == TechnologyEra.BRONZE_AGE:
            self._trigger_bronze_age_event(tribe_id)
        elif tech.era == TechnologyEra.IRON_AGE:
            self._trigger_iron_age_event(tribe_id)
        elif tech.era == TechnologyEra.MEDIEVAL:
            self._trigger_medieval_era_event(tribe_id)

    def _trigger_farming_discovery_event(self, tribe_id: str):
        """Trigger events when farming is discovered."""
        print(f"[EVENT] 🌾 Agricultural Revolution begins for {tribe_id}!")
        print(f"[EVENT] {tribe_id} can now cultivate crops and store surplus food.")
        print("[EVENT] Population growth potential increases significantly.")

    def _trigger_tool_discovery_event(self, tribe_id: str):
        """Trigger events when tools are discovered."""
        print(f"[EVENT] 🔨 Tool-making revolution for {tribe_id}!")
        print("[EVENT] Resource gathering becomes more efficient.")
        print("[EVENT] New crafting possibilities emerge.")

    def _trigger_weapon_discovery_event(self, tribe_id: str):
        """Trigger events when weapons are discovered."""
        print(f"[EVENT] ⚔️ Warfare technology breakthrough for {tribe_id}!")
        print("[EVENT] Hunting becomes more effective.")
        print("[EVENT] Defense capabilities improve.")

    def _trigger_irrigation_event(self, tribe_id: str):
        """Trigger events when irrigation is discovered."""
        print(f"[EVENT] 💧 Irrigation systems developed by {tribe_id}!")
        print("[EVENT] Agricultural productivity doubles.")
        print("[EVENT] Sustainable food production achieved.")

    def _trigger_agricultural_revolution_event(self, tribe_id: str):
        """Trigger broader agricultural revolution events."""
        unlocked_agri_techs = sum(1 for tech_id in self.unlocked_technologies.get(tribe_id, set())
                                 if self.technologies[tech_id].category == TechnologyCategory.AGRICULTURE)

        if unlocked_agri_techs >= 2:
            print(f"[EVENT] 🌱 Full Agricultural Revolution for {tribe_id}!")
            print("[EVENT] Sedentary lifestyle becomes possible.")
            print("[EVENT] Civilization foundations established.")

    def _trigger_medieval_revolution_event(self, tribe_id: str):
        """Trigger events when steel weapons are discovered."""
        print(f"[EVENT] ⚔️ Medieval Revolution for {tribe_id}!")
        print("[EVENT] Steel weapons usher in a new era of warfare!")
        print("[EVENT] Chivalry and knighthood become central to society.")

    def _trigger_crafting_revolution_event(self, tribe_id: str):
        """Trigger crafting revolution events."""
        unlocked_crafting_techs = sum(1 for tech_id in self.unlocked_technologies.get(tribe_id, set())
                                     if self.technologies[tech_id].category == TechnologyCategory.CRAFTING)

        if unlocked_crafting_techs >= 3:
            print(f"[EVENT] ⚒️ Crafting Revolution for {tribe_id}!")
            print("[EVENT] Advanced manufacturing capabilities achieved.")
            print("[EVENT] Economic specialization becomes possible.")

    def _trigger_bronze_age_event(self, tribe_id: str):
        """Trigger Bronze Age advancement events."""
        unlocked_bronze_techs = sum(1 for tech_id in self.unlocked_technologies.get(tribe_id, set())
                                   if self.technologies[tech_id].era == TechnologyEra.BRONZE_AGE)

        if unlocked_bronze_techs >= 2:
            print(f"[EVENT] 🏺 Bronze Age Civilization for {tribe_id}!")
            print("[EVENT] Metal tools revolutionize daily life.")
            print("[EVENT] Complex societies and trade networks emerge.")

    def _trigger_iron_age_event(self, tribe_id: str):
        """Trigger Iron Age advancement events."""
        unlocked_iron_techs = sum(1 for tech_id in self.unlocked_technologies.get(tribe_id, set())
                                 if self.technologies[tech_id].era == TechnologyEra.IRON_AGE)

        if unlocked_iron_techs >= 2:
            print(f"[EVENT] 🔨 Iron Age Mastery for {tribe_id}!")
            print("[EVENT] Iron tools and weapons dominate technology.")
            print("[EVENT] Large-scale construction and military power achieved.")

    def _trigger_medieval_era_event(self, tribe_id: str):
        """Trigger Medieval era advancement events."""
        unlocked_medieval_techs = sum(1 for tech_id in self.unlocked_technologies.get(tribe_id, set())
                                     if self.technologies[tech_id].era == TechnologyEra.MEDIEVAL)

        if unlocked_medieval_techs >= 2:
            print(f"[EVENT] 🏰 Medieval Era for {tribe_id}!")
            print("[EVENT] Feudal societies and advanced warfare emerge.")
            print("[EVENT] Cultural and technological sophistication peaks.")

    def _trigger_metalworking_event(self, tribe_id: str):
        """Trigger events when metalworking is discovered."""
        print(f"[EVENT] 🔥 Metalworking Revolution for {tribe_id}!")
        print("[EVENT] The ability to work metal transforms society.")
        print("[EVENT] New tools, weapons, and possibilities emerge.")

    def _trigger_literacy_event(self, tribe_id: str):
        """Trigger events when writing is discovered."""
        print(f"[EVENT] 📚 Literacy Revolution for {tribe_id}!")
        print("[EVENT] Knowledge can now be preserved and shared.")
        print("[EVENT] Administration and scholarship become possible.")

    def get_technology_events(self, tribe_id: str, tick: int) -> List[Dict[str, Any]]:
        """Get technology-related events for logging."""
        events = []

        # Check for research milestones
        for tech_id, progress in self.tribe_research_progress.get(tribe_id, {}).items():
            tech = self.technologies[tech_id]

            # Milestone events at 25%, 50%, 75% progress
            milestones = [0.25, 0.5, 0.75]
            for milestone in milestones:
                if progress["progress"] >= milestone and not progress.get(f"milestone_{milestone}", False):
                    progress[f"milestone_{milestone}"] = True
                    events.append({
                        "type": "research_milestone",
                        "tribe_id": tribe_id,
                        "technology": tech.name,
                        "progress": progress["progress"],
                        "milestone": milestone,
                        "tick": tick
                    })

        # Check for technology unlocks
        for tech_id in self.unlocked_technologies.get(tribe_id, set()):
            tech = self.technologies[tech_id]
            if not getattr(tech, "unlock_logged", False):
                tech.unlock_logged = True
                events.append({
                    "type": "technology_unlocked",
                    "tribe_id": tribe_id,
                    "technology": tech.name,
                    "category": tech.category.value,
                    "era": tech.era.value,
                    "tick": tick
                })

        return events

    def get_available_technologies(self, tribe_id: str) -> List[str]:
        """Get technologies available for research by a tribe."""
        unlocked = self.unlocked_technologies.get(tribe_id, set())
        available = []

        for tech_id, tech in self.technologies.items():
            # Check if already unlocked or researching
            if tech_id in unlocked:
                continue
            if tribe_id in self.tribe_research_progress and tech_id in self.tribe_research_progress[tribe_id]:
                continue

            # Check prerequisites
            prereqs_met = all(prereq in unlocked for prereq in tech.requirement.prerequisite_techs)
            if prereqs_met:
                available.append(tech_id)

        return available

    def get_research_progress(self, tribe_id: str, tech_id: str) -> Optional[Dict[str, Any]]:
        """Get research progress for a specific technology."""
        if tribe_id not in self.tribe_research_progress:
            return None
        return self.tribe_research_progress[tribe_id].get(tech_id)

    def get_technology_effect(self, tribe_id: str, tech_id: str) -> Optional[TechnologyEffect]:
        """Get the effect of a technology if unlocked by the tribe."""
        if tribe_id not in self.unlocked_technologies:
            return None
        if tech_id not in self.unlocked_technologies[tribe_id]:
            return None
        return self.technologies[tech_id].effect

    def calculate_tribe_multipliers(self, tribe_id: str) -> Dict[str, float]:
        """Calculate combined multipliers from all unlocked technologies."""
        multipliers = {
            "population": 1.0,
            "food": 1.0,
            "wood": 1.0,
            "stone": 1.0,
            "mineral": 1.0,
            "animal": 1.0,
            "plant": 1.0,
            "reproduction": 0.0,
            "mortality": 0.0,
            "combat": 0.0
        }

        if tribe_id not in self.unlocked_technologies:
            return multipliers

        for tech_id in self.unlocked_technologies[tribe_id]:
            effect = self.technologies[tech_id].effect

            # Population multiplier
            multipliers["population"] *= effect.population_multiplier

            # Resource multipliers
            for resource, mult in effect.resource_multipliers.items():
                if resource in multipliers:
                    multipliers[resource] *= mult

            # Reproduction and mortality bonuses
            multipliers["reproduction"] += effect.reproduction_bonus
            multipliers["mortality"] += effect.mortality_reduction
            multipliers["combat"] += effect.combat_bonus

        return multipliers

    def get_tribe_abilities(self, tribe_id: str) -> Set[str]:
        """Get all special abilities unlocked by a tribe's technologies."""
        abilities = set()

        if tribe_id not in self.unlocked_technologies:
            return abilities

        for tech_id in self.unlocked_technologies[tribe_id]:
            effect = self.technologies[tech_id].effect
            abilities.update(effect.special_abilities)

        return abilities

    def save_state(self, filepath: str):
        """Save technology system state to file."""
        state = {
            "unlocked_technologies": {k: list(v) for k, v in self.unlocked_technologies.items()},
            "research_progress": self.tribe_research_progress
        }

        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)

    def load_state(self, filepath: str):
        """Load technology system state from file."""
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)

            self.unlocked_technologies = {k: set(v) for k, v in state.get("unlocked_technologies", {}).items()}
            self.tribe_research_progress = state.get("research_progress", {})

            print(f"Loaded technology state: {len(self.unlocked_technologies)} tribes with technologies")
            return True
        except Exception as e:
            print(f"Failed to load technology state: {e}")
            return False

    # ===== TECHNOLOGY TRADING SYSTEM =====

    def create_trade_offer(self, offering_tribe: str, receiving_tribe: str,
                          offered_tech: str, trade_type: TradeType = TradeType.DIRECT_EXCHANGE,
                          requested_tech: Optional[str] = None,
                          resource_payment: Optional[Dict[str, float]] = None,
                          current_tick: int = 0) -> bool:
        """Create a technology trade offer."""
        # Validate tribes have the technologies
        if offered_tech not in self.unlocked_technologies.get(offering_tribe, set()):
            return False

        if trade_type == TradeType.DIRECT_EXCHANGE and requested_tech:
            if requested_tech not in self.unlocked_technologies.get(receiving_tribe, set()):
                return False

        # Calculate trade parameters
        diplomatic_bonus = self._calculate_trade_relationship_bonus(offering_tribe, receiving_tribe)
        risk_factor = self._calculate_trade_risk(offering_tribe, receiving_tribe, trade_type)

        # Create the offer
        offer = TechnologyTradeOffer(
            offering_tribe=offering_tribe,
            receiving_tribe=receiving_tribe,
            offered_technology=offered_tech,
            requested_technology=requested_tech,
            resource_payment=resource_payment or {},
            trade_type=trade_type,
            diplomatic_bonus=diplomatic_bonus,
            risk_factor=risk_factor,
            created_tick=current_tick,
            expires_tick=current_tick + 200  # 200 ticks to respond
        )

        # Add to pending offers
        if receiving_tribe not in self.pending_trade_offers:
            self.pending_trade_offers[receiving_tribe] = []
        self.pending_trade_offers[receiving_tribe].append(offer)

        print(f"[TRADE OFFER] {offering_tribe} offers {offered_tech} to {receiving_tribe}")
        return True

    def accept_trade_offer(self, receiving_tribe: str, offer_index: int, current_tick: int) -> bool:
        """Accept a pending trade offer."""
        if receiving_tribe not in self.pending_trade_offers:
            return False

        offers = self.pending_trade_offers[receiving_tribe]
        if offer_index >= len(offers):
            return False

        offer = offers[offer_index]

        # Check if offer has expired
        if current_tick > offer.expires_tick:
            print(f"[TRADE] Offer from {offer.offering_tribe} to {receiving_tribe} has expired")
            offers.pop(offer_index)
            return False

        # Process the trade
        success = self._execute_trade(offer, current_tick)

        # Remove the offer
        offers.pop(offer_index)

        if success:
            print(f"[TRADE SUCCESS] {receiving_tribe} accepts {offer.offered_technology} from {offer.offering_tribe}")
            self._update_trade_relationships(offer.offering_tribe, offer.receiving_tribe, 15.0)  # Positive relationship boost
        else:
            print(f"[TRADE FAILED] Trade between {offer.offering_tribe} and {receiving_tribe} failed")
            self._update_trade_relationships(offer.offering_tribe, offer.receiving_tribe, -10.0)  # Negative relationship hit

        return success

    def reject_trade_offer(self, receiving_tribe: str, offer_index: int) -> bool:
        """Reject a pending trade offer."""
        if receiving_tribe not in self.pending_trade_offers:
            return False

        offers = self.pending_trade_offers[receiving_tribe]
        if offer_index >= len(offers):
            return False

        offer = offers[offer_index]
        offers.pop(offer_index)

        print(f"[TRADE REJECTED] {receiving_tribe} rejects offer from {offer.offering_tribe}")
        self._update_trade_relationships(offer.offering_tribe, offer.receiving_tribe, -5.0)  # Small relationship penalty

        return True

    def get_pending_offers(self, tribe_id: str) -> List[TechnologyTradeOffer]:
        """Get all pending trade offers for a tribe."""
        return self.pending_trade_offers.get(tribe_id, [])

    def get_tradeable_technologies(self, tribe_id: str) -> List[str]:
        """Get technologies that a tribe can offer for trade."""
        unlocked = self.unlocked_technologies.get(tribe_id, set())
        tradeable = []

        for tech_id in unlocked:
            tech = self.technologies.get(tech_id)
            if tech and tech.trade_value > 0:
                tradeable.append(tech_id)

        return tradeable

    def get_desired_technologies(self, tribe_id: str) -> List[str]:
        """Get technologies that a tribe might want to acquire."""
        unlocked = self.unlocked_technologies.get(tribe_id, set())
        desired = []

        for tech_id, tech in self.technologies.items():
            if tech_id not in unlocked:
                # Check if prerequisites are met
                prereqs_met = all(prereq in unlocked for prereq in tech.requirement.prerequisite_techs)
                if prereqs_met:
                    desired.append(tech_id)

        return desired

    def _execute_trade(self, offer: TechnologyTradeOffer, current_tick: int) -> bool:
        """Execute a technology trade."""
        import random

        # Calculate success chance
        base_success = 0.8  # 80% base success rate
        relationship_modifier = offer.diplomatic_bonus * 0.1
        risk_modifier = -offer.risk_factor * 0.2

        success_chance = min(0.95, max(0.1, base_success + relationship_modifier - risk_modifier))

        if random.random() > success_chance:
            # Trade failed
            trade = TechnologyTrade(
                offering_tribe=offer.offering_tribe,
                receiving_tribe=offer.receiving_tribe,
                technology_transferred=offer.offered_technology,
                trade_type=offer.trade_type,
                completed_tick=current_tick,
                success=False
            )
            self.completed_trades.append(trade)
            return False

        # Trade successful - transfer technology
        receiving_unlocked = self.unlocked_technologies.get(offer.receiving_tribe, set())
        receiving_unlocked.add(offer.offered_technology)
        self.unlocked_technologies[offer.receiving_tribe] = receiving_unlocked

        # Handle reciprocal transfer for direct exchange
        if offer.trade_type == TradeType.DIRECT_EXCHANGE and offer.requested_technology:
            offering_unlocked = self.unlocked_technologies.get(offer.offering_tribe, set())
            offering_unlocked.add(offer.requested_technology)
            self.unlocked_technologies[offer.offering_tribe] = offering_unlocked

        # Record the successful trade
        trade = TechnologyTrade(
            offering_tribe=offer.offering_tribe,
            receiving_tribe=offer.receiving_tribe,
            technology_transferred=offer.offered_technology,
            trade_type=offer.trade_type,
            resources_exchanged=offer.resource_payment.copy(),
            relationship_change=offer.diplomatic_bonus,
            completed_tick=current_tick,
            success=True
        )
        self.completed_trades.append(trade)

        # Trigger technology unlock events for the receiving tribe
        self._trigger_technology_events(offer.receiving_tribe, offer.offered_technology)

        return True

    def _calculate_trade_relationship_bonus(self, offering_tribe: str, receiving_tribe: str) -> float:
        """Calculate diplomatic bonus for trade between tribes."""
        # Get base relationship from trade history
        relationship = self.trade_relationships.get(offering_tribe, {}).get(receiving_tribe, 0.0)

        # Add bonus for previous successful trades
        successful_trades = sum(1 for trade in self.completed_trades
                               if ((trade.offering_tribe == offering_tribe and trade.receiving_tribe == receiving_tribe) or
                                   (trade.offering_tribe == receiving_tribe and trade.receiving_tribe == offering_tribe))
                               and trade.success)

        return relationship + (successful_trades * 2.0)

    def _calculate_trade_risk(self, offering_tribe: str, receiving_tribe: str, trade_type: TradeType) -> float:
        """Calculate risk factor for a trade."""
        base_risk = 0.1  # 10% base risk

        # Higher risk for espionage
        if trade_type == TradeType.ESPIONAGE:
            base_risk += 0.4

        # Risk increases with technology value
        offered_tech = self.technologies.get(self.unlocked_technologies.get(offering_tribe, set()).pop() if self.unlocked_technologies.get(offering_tribe) else None)
        if offered_tech:
            value_risk = (offered_tech.trade_value / 1000.0) * 0.2
            base_risk += value_risk

        # Risk decreases with good relationships
        relationship_bonus = self._calculate_trade_relationship_bonus(offering_tribe, receiving_tribe)
        relationship_modifier = max(-0.3, relationship_bonus * -0.05)  # Max 30% risk reduction

        return max(0.0, base_risk + relationship_modifier)

    def _update_trade_relationships(self, tribe_a: str, tribe_b: str, change: float):
        """Update trade relationships between tribes."""
        if tribe_a not in self.trade_relationships:
            self.trade_relationships[tribe_a] = {}
        if tribe_b not in self.trade_relationships:
            self.trade_relationships[tribe_b] = {}

        self.trade_relationships[tribe_a][tribe_b] = self.trade_relationships[tribe_a].get(tribe_b, 0.0) + change
        self.trade_relationships[tribe_b][tribe_a] = self.trade_relationships[tribe_b].get(tribe_a, 0.0) + change

    def get_trade_statistics(self, tribe_id: str) -> Dict[str, Any]:
        """Get trading statistics for a tribe."""
        successful_offers = sum(1 for trade in self.completed_trades
                               if trade.offering_tribe == tribe_id and trade.success)
        successful_receipts = sum(1 for trade in self.completed_trades
                                 if trade.receiving_tribe == tribe_id and trade.success)
        failed_trades = sum(1 for trade in self.completed_trades
                           if (trade.offering_tribe == tribe_id or trade.receiving_tribe == tribe_id)
                           and not trade.success)

        return {
            "technologies_offered": successful_offers,
            "technologies_received": successful_receipts,
            "failed_trades": failed_trades,
            "pending_offers": len(self.pending_trade_offers.get(tribe_id, [])),
            "trade_partners": len(self.trade_relationships.get(tribe_id, {}))
        }

    def cleanup_expired_offers(self, current_tick: int):
        """Remove expired trade offers."""
        for tribe_id in list(self.pending_trade_offers.keys()):
            offers = self.pending_trade_offers[tribe_id]
            self.pending_trade_offers[tribe_id] = [
                offer for offer in offers if current_tick <= offer.expires_tick
            ]

            # Remove empty lists
            if not self.pending_trade_offers[tribe_id]:
                del self.pending_trade_offers[tribe_id]


# Global technology manager instance
technology_manager = TechnologyManager()