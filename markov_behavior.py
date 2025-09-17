import random
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Any, Optional
import json


class MarkovDecisionChain:
    """A Markov chain for tribal decision-making based on context and history."""

    def __init__(self, memory_size: int = 3):
        self.model = defaultdict(lambda: defaultdict(int))  # state -> {action: count}
        self.memory_size = memory_size
        self.decision_history = deque(maxlen=memory_size)

    def train(self, state_action_pairs: List[Tuple[str, str]]):
        """Train the model with sequences of (state, action) pairs."""
        for i in range(len(state_action_pairs) - 1):
            current_state = state_action_pairs[i][0]
            next_action = state_action_pairs[i + 1][1]
            self.model[current_state][next_action] += 1

    def get_probabilities(self, state: str) -> Dict[str, float]:
        """Get probability distribution for actions given a state."""
        if state not in self.model:
            return {}

        total = sum(self.model[state].values())
        if total == 0:
            return {}

        return {action: count / total for action, count in self.model[state].items()}

    def make_decision(
        self,
        context: str,
        available_actions: List[str],
        bias_weights: Optional[Dict[str, float]] = None,
    ) -> str:
        """Make a decision based on current context and available actions."""
        # Create state from recent history + current context
        history_state = "_".join([h[1] for h in list(self.decision_history)[-2:]])
        full_state = f"{history_state}_{context}" if history_state else context

        # Get Markov probabilities
        probabilities = self.get_probabilities(full_state)

        # If no history for this exact state, try just the context
        if not probabilities and history_state:
            probabilities = self.get_probabilities(context)

        # Apply bias weights if provided
        if bias_weights:
            for action in available_actions:
                if action in probabilities and action in bias_weights:
                    probabilities[action] *= bias_weights[action]

        # Filter to only available actions
        valid_probs = {action: probabilities.get(action, 0.1) for action in available_actions}

        # Normalize probabilities
        total_prob = sum(valid_probs.values())
        if total_prob > 0:
            valid_probs = {action: prob / total_prob for action, prob in valid_probs.items()}
        else:
            # Fallback to uniform distribution
            valid_probs = {action: 1.0 / len(available_actions) for action in available_actions}

        # Make weighted random choice
        actions = list(valid_probs.keys())
        weights = list(valid_probs.values())
        chosen_action = random.choices(actions, weights=weights, k=1)[0]

        # Record decision for future context
        self.decision_history.append((full_state, chosen_action))

        return chosen_action


class TribalMarkovBehavior:
    """Markov chain system for tribal collective decision-making."""

    def __init__(self):
        self.diplomatic_chain = MarkovDecisionChain(memory_size=4)
        self.resource_chain = MarkovDecisionChain(memory_size=3)
        self.conflict_chain = MarkovDecisionChain(memory_size=5)
        self.cultural_chain = MarkovDecisionChain(memory_size=3)

        # Initialize with some basic training data
        self._initialize_chains()

    def _initialize_chains(self):
        """Initialize chains with basic decision patterns."""

        # Diplomatic decision patterns
        diplomatic_patterns = [
            ("high_trust_friendly", "cultural_exchange"),
            ("cultural_exchange", "trade_proposal"),
            ("trade_proposal", "alliance_proposal"),
            ("alliance_proposal", "joint_festival"),
            ("low_trust_neutral", "cautious_trade"),
            ("cautious_trade", "border_patrol"),
            ("border_patrol", "territory_dispute"),
            ("territory_dispute", "negotiation"),
            ("hostile_bitter", "raid_planning"),
            ("raid_planning", "resource_theft"),
            ("resource_theft", "territory_conflict"),
            ("territory_conflict", "alliance_betrayal"),
        ]
        self.diplomatic_chain.train(diplomatic_patterns)

        # Resource management patterns
        resource_patterns = [
            ("abundance_spring", "generous_sharing"),
            ("generous_sharing", "trade_surplus"),
            ("trade_surplus", "stockpile_building"),
            ("scarcity_winter", "resource_hoarding"),
            ("resource_hoarding", "cautious_trade"),
            ("cautious_trade", "territory_expansion"),
            ("neutral_autumn", "balanced_gathering"),
            ("balanced_gathering", "moderate_trade"),
            ("moderate_trade", "seasonal_preparation"),
        ]
        self.resource_chain.train(resource_patterns)

        # Conflict resolution patterns
        conflict_patterns = [
            ("minor_dispute", "diplomatic_talk"),
            ("diplomatic_talk", "compromise_offer"),
            ("compromise_offer", "peaceful_resolution"),
            ("major_conflict", "show_of_force"),
            ("show_of_force", "escalation"),
            ("escalation", "warfare"),
            ("warfare", "victory_or_defeat"),
            ("border_tension", "patrol_increase"),
            ("patrol_increase", "skirmish"),
            ("skirmish", "retaliation"),
        ]
        self.conflict_chain.train(conflict_patterns)

        # Cultural evolution patterns
        cultural_patterns = [
            ("stable_peaceful", "artistic_focus"),
            ("artistic_focus", "cultural_flowering"),
            ("cultural_flowering", "knowledge_sharing"),
            ("conflict_stressed", "warrior_culture"),
            ("warrior_culture", "aggressive_expansion"),
            ("aggressive_expansion", "territorial_dominance"),
            ("isolation_winter", "introspection"),
            ("introspection", "spiritual_development"),
            ("spiritual_development", "ritual_innovation"),
        ]
        self.cultural_chain.train(cultural_patterns)

    def make_diplomatic_decision(
        self, tribe_context: Dict[str, Any], available_actions: List[str]
    ) -> str:
        """Make a diplomatic decision using Markov chains."""
        # Build context string from diplomatic state
        trust_level = tribe_context.get("trust_level", 0.5)
        relationship = tribe_context.get("relationship", "neutral")

        if trust_level > 0.7:
            context = f"high_trust_{relationship}"
        elif trust_level < 0.3:
            context = f"low_trust_{relationship}"
        else:
            context = f"neutral_{relationship}"

        # Bias weights based on tribe personality/traits
        bias_weights = {}
        if "aggressive" in tribe_context.get("traits", []):
            bias_weights.update({"raid": 1.5, "territory_conflict": 1.3, "alliance_betrayal": 1.2})
        if "peaceful" in tribe_context.get("traits", []):
            bias_weights.update(
                {"cultural_exchange": 1.4, "trade_proposal": 1.3, "joint_festival": 1.2}
            )
        if "generous" in tribe_context.get("traits", []):
            bias_weights.update({"resource_sharing": 1.4, "gift_giving": 1.3})

        return self.diplomatic_chain.make_decision(context, available_actions, bias_weights)

    def make_resource_decision(
        self, tribe_context: Dict[str, Any], available_actions: List[str]
    ) -> str:
        """Make a resource management decision using Markov chains."""
        season = tribe_context.get("season", "spring")
        resource_level = tribe_context.get("resource_abundance", 0.5)

        if resource_level > 0.7:
            context = f"abundance_{season}"
        elif resource_level < 0.3:
            context = f"scarcity_{season}"
        else:
            context = f"neutral_{season}"

        # Bias weights based on economic specialization
        bias_weights = {}
        specialization = tribe_context.get("economic_specialization", "")
        if "trader" in specialization.lower():
            bias_weights.update({"trade_surplus": 1.3, "moderate_trade": 1.2})
        if "gatherer" in specialization.lower():
            bias_weights.update({"balanced_gathering": 1.3, "stockpile_building": 1.2})
        if "hunter" in specialization.lower():
            bias_weights.update({"territory_expansion": 1.3, "aggressive_gathering": 1.2})

        return self.resource_chain.make_decision(context, available_actions, bias_weights)

    def make_conflict_decision(
        self, tribe_context: Dict[str, Any], available_actions: List[str]
    ) -> str:
        """Make a conflict-related decision using Markov chains."""
        conflict_intensity = tribe_context.get("conflict_intensity", "minor")
        military_strength = tribe_context.get("military_strength", 0.5)

        context = f"{conflict_intensity}_conflict"
        if military_strength > 0.7:
            context += "_strong"
        elif military_strength < 0.3:
            context += "_weak"

        # Bias weights based on military culture
        bias_weights = {}
        if "warrior" in tribe_context.get("culture_type", ""):
            bias_weights.update({"show_of_force": 1.4, "escalation": 1.3, "warfare": 1.2})
        if "diplomatic" in tribe_context.get("culture_type", ""):
            bias_weights.update(
                {
                    "diplomatic_talk": 1.4,
                    "compromise_offer": 1.3,
                    "peaceful_resolution": 1.2,
                }
            )

        return self.conflict_chain.make_decision(context, available_actions, bias_weights)

    def make_cultural_decision(
        self, tribe_context: Dict[str, Any], available_actions: List[str]
    ) -> str:
        """Make a cultural development decision using Markov chains."""
        stability = tribe_context.get("stability", "stable")
        season = tribe_context.get("season", "spring")
        recent_conflicts = tribe_context.get("recent_conflicts", 0)

        if recent_conflicts > 2:
            context = "conflict_stressed"
        elif season == "winter":
            context = "isolation_winter"
        else:
            context = f"{stability}_peaceful"

        # Bias weights based on cultural traits
        bias_weights = {}
        cultural_focus = tribe_context.get("cultural_focus", "")
        if "spiritual" in cultural_focus:
            bias_weights.update({"spiritual_development": 1.4, "ritual_innovation": 1.3})
        if "artistic" in cultural_focus:
            bias_weights.update({"artistic_focus": 1.4, "cultural_flowering": 1.3})
        if "knowledge" in cultural_focus:
            bias_weights.update({"knowledge_sharing": 1.4, "introspection": 1.2})

        return self.cultural_chain.make_decision(context, available_actions, bias_weights)

    def learn_from_outcome(
        self, decision_type: str, context: str, action: str, outcome_success: float
    ):
        """Learn from the outcome of a decision to improve future choices."""
        # Reinforce successful patterns by adding them to training
        if outcome_success > 0.7:  # Successful outcome
            chain = getattr(self, f"{decision_type}_chain", None)
            if chain:
                # Add the successful pattern multiple times to reinforce it
                for _ in range(int(outcome_success * 3)):
                    chain.model[context][action] += 1
        elif outcome_success < 0.3:  # Failed outcome
            chain = getattr(self, f"{decision_type}_chain", None)
            if chain and context in chain.model and action in chain.model[context]:
                # Reduce weight of failed actions
                chain.model[context][action] = max(1, chain.model[context][action] - 1)


# Global instance for tribal decision-making
global_tribal_markov = TribalMarkovBehavior()


def make_markov_choice(
    options: List[str],
    context: str,
    decision_type: str = "diplomatic",
    tribe_context: Optional[Dict[str, Any]] = None,
) -> str:
    """Convenient function to make Markov-based choices instead of random.choice()."""
    if not options:
        return ""

    if len(options) == 1:
        return options[0]

    # Use appropriate Markov chain based on decision type
    if tribe_context is None:
        tribe_context = {}

    if decision_type == "diplomatic":
        return global_tribal_markov.make_diplomatic_decision(tribe_context, options)
    elif decision_type == "resource":
        return global_tribal_markov.make_resource_decision(tribe_context, options)
    elif decision_type == "conflict":
        return global_tribal_markov.make_conflict_decision(tribe_context, options)
    elif decision_type == "cultural":
        return global_tribal_markov.make_cultural_decision(tribe_context, options)
    else:
        # Fallback to basic Markov chain with simple context
        chain = MarkovDecisionChain()
        return chain.make_decision(context, options)


def save_markov_state(filepath: str):
    """Save the current Markov chain states to a file."""
    try:
        state = {
            "diplomatic": dict(global_tribal_markov.diplomatic_chain.model),
            "resource": dict(global_tribal_markov.resource_chain.model),
            "conflict": dict(global_tribal_markov.conflict_chain.model),
            "cultural": dict(global_tribal_markov.cultural_chain.model),
        }
        with open(filepath, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Failed to save Markov state: {e}")


def load_markov_state(filepath: str):
    """Load Markov chain states from a file."""
    try:
        with open(filepath, "r") as f:
            state = json.load(f)

        global_tribal_markov.diplomatic_chain.model = defaultdict(
            lambda: defaultdict(int), state.get("diplomatic", {})
        )
        global_tribal_markov.resource_chain.model = defaultdict(
            lambda: defaultdict(int), state.get("resource", {})
        )
        global_tribal_markov.conflict_chain.model = defaultdict(
            lambda: defaultdict(int), state.get("conflict", {})
        )
        global_tribal_markov.cultural_chain.model = defaultdict(
            lambda: defaultdict(int), state.get("cultural", {})
        )
    except Exception as e:
        print(f"Failed to load Markov state: {e}")
