"""
Tribal Diplomacy RL Agent: Learns optimal diplomatic strategies for
tribal interactions.
"""

import random
import json
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

from rl_diplomacy_interface import (
    get_diplomacy_actions,
    propose_alliance,
    declare_rivalry,
    mediate_conflict,
    form_trade_agreement,
)


class DiplomacyRLAgent:
    """RL Agent for learning tribal diplomacy strategies."""

    def __init__(
        self,
        num_actions: int = 5,
        epsilon: float = 0.1,
        lr: float = 0.1,
        gamma: float = 0.95,
    ):
        self.num_actions = num_actions
        self.epsilon = epsilon  # Exploration rate
        self.lr = lr  # Learning rate
        self.gamma = gamma  # Discount factor

        # Q-table: state -> action values
        # States are discretized versions of the diplomacy state vector
        self.q_table: Dict[Tuple, List[float]] = defaultdict(lambda: [0.0] * num_actions)

        # Action names for logging
        self.action_names = get_diplomacy_actions()

        # State discretization bins
        self.state_bins = {
            "avg_diplomacy": np.linspace(-1.0, 1.0, 10),
            "best_diplomacy": np.linspace(-1.0, 1.0, 10),
            "worst_diplomacy": np.linspace(-1.0, 1.0, 10),
            "avg_population": np.linspace(0.0, 2.0, 8),
            "max_population": np.linspace(0.0, 2.0, 8),
            "established_tribes": np.linspace(0.0, 1.0, 6),
            "total_food": np.linspace(0.0, 5.0, 8),
        }

    def discretize_state(self, state_vector: List[float]) -> Tuple:
        """Convert continuous state vector to discrete tuple for Q-table."""
        if len(state_vector) != 7:
            # Pad or truncate to expected length
            state_vector = (state_vector + [0.0] * 7)[:7]

        discrete_state = []
        state_keys = [
            "avg_diplomacy",
            "best_diplomacy",
            "worst_diplomacy",
            "avg_population",
            "max_population",
            "established_tribes",
            "total_food",
        ]

        for i, value in enumerate(state_vector):
            key = state_keys[i]
            bins = self.state_bins[key]
            # Find which bin this value falls into
            bin_idx = np.digitize(value, bins) - 1
            bin_idx = max(0, min(bin_idx, len(bins) - 2))
            # Clamp to valid range
            discrete_state.append(bin_idx)

        return tuple(discrete_state)

    def select_action(self, state_vector: List[float]) -> int:
        """Select action using epsilon-greedy policy."""
        state = self.discretize_state(state_vector)

        if random.random() < self.epsilon:
            # Explore: random action
            return random.randint(0, self.num_actions - 1)
        else:
            # Exploit: best action for this state
            q_values = self.q_table[state]
            max_q = max(q_values)
            # Break ties randomly
            best_actions = [i for i, q in enumerate(q_values) if q == max_q]
            return random.choice(best_actions)

    def update_q_table(
        self,
        state_vector: List[float],
        action: int,
        reward: float,
        next_state_vector: List[float],
    ) -> None:
        """Update Q-table using Q-learning."""
        state = self.discretize_state(state_vector)
        next_state = self.discretize_state(next_state_vector)

        # Q-learning update
        current_q = self.q_table[state][action]
        next_max_q = max(self.q_table[next_state])

        new_q = current_q + self.lr * (reward + self.gamma * next_max_q - current_q)
        self.q_table[state][action] = new_q

    def execute_action(
        self,
        world: Any,
        action_idx: int,
        source_tribe: Optional[str] = None,
        target_tribe: Optional[str] = None,
    ) -> bool:
        """Execute the selected diplomatic action."""
        action_name = self.action_names[action_idx]

        if action_name == "diplomacy_noop":
            return True  # No-op always succeeds

        if not source_tribe or not target_tribe:
            # Need to select tribes for action
            tribal_manager = getattr(world, "_tribal_manager", None)
            if tribal_manager and hasattr(tribal_manager, "tribes"):
                tribes = list(tribal_manager.tribes.keys())
                if len(tribes) >= 2:
                    source_tribe = random.choice(tribes)
                    target_tribe = random.choice([t for t in tribes if t != source_tribe])
                else:
                    return False  # Not enough tribes

        # Execute the action
        if action_name == "propose_alliance":
            return propose_alliance(world, source_tribe, target_tribe)
        elif action_name == "declare_rivalry":
            return declare_rivalry(world, source_tribe, target_tribe)
        elif action_name == "mediate_conflict":
            # For mediation, need a third tribe as mediator
            tribal_manager = getattr(world, "_tribal_manager", None)
            if tribal_manager:
                tribes = list(tribal_manager.tribes.keys())
                mediator = random.choice(
                    [t for t in tribes if t not in [source_tribe, target_tribe]]
                )
                return mediate_conflict(world, mediator, source_tribe, target_tribe)
            return False
        elif action_name == "form_trade_agreement":
            return form_trade_agreement(world, source_tribe, target_tribe)

        return False

    def save_q_table(self, filepath: str):
        """Save Q-table to JSON file."""
        # Convert defaultdict to regular dict for JSON serialization
        q_table_dict = {str(k): v for k, v in self.q_table.items()}

        with open(filepath, "w") as f:
            json.dump(
                {
                    "q_table": q_table_dict,
                    "epsilon": self.epsilon,
                    "lr": self.lr,
                    "gamma": self.gamma,
                    "action_names": self.action_names,
                },
                f,
                indent=2,
            )

    def load_q_table(self, filepath: str):
        """Load Q-table from JSON file."""
        try:
            with open(filepath, "r") as f:
                data = json.load(f)

            # Reconstruct Q-table
            self.q_table = defaultdict(lambda: [0.0] * self.num_actions)
            for state_str, q_values in data["q_table"].items():
                # Parse state tuple from string, handling np.int64 format
                state_str_clean = state_str.strip("()")
                state_parts = []
                for part in state_str_clean.split(","):
                    part = part.strip()
                    if part.startswith("np.int64(") and part.endswith(")"):
                        # Extract number from np.int64(X)
                        num_str = part[9:-1]  # Remove "np.int64(" and ")"
                        state_parts.append(int(num_str))
                    elif part:
                        try:
                            state_parts.append(int(part))
                        except ValueError:
                            # Handle any other non-integer parts gracefully
                            print(f"Warning: Skipping invalid state component '{part}' in {state_str}")
                            continue

                if state_parts:  # Only add if we have valid parts
                    state = tuple(state_parts)
                    self.q_table[state] = q_values

            # Load parameters
            self.epsilon = data.get("epsilon", self.epsilon)
            self.lr = data.get("lr", self.lr)
            self.gamma = data.get("gamma", self.gamma)
            self.action_names = data.get("action_names", self.action_names)

            print(f"Loaded diplomacy Q-table with {len(self.q_table)} states")
            return True
        except Exception as e:
            print(f"Failed to load diplomacy Q-table: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the learned policy."""
        total_states = len(self.q_table)
        avg_q_values = []

        for q_values in self.q_table.values():
            avg_q_values.extend(q_values)

        return {
            "total_states": total_states,
            "avg_q_value": (sum(avg_q_values) / len(avg_q_values) if avg_q_values else 0.0),
            "epsilon": self.epsilon,
            "learning_rate": self.lr,
            "discount_factor": self.gamma,
        }
