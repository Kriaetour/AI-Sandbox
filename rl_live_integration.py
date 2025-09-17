"""
Real-time RL Integration for AI Sandbox

Manages RL agents during live simulation, providing:
- Agent loading/saving/persistence
- Real-time decision making
- Live learning capabilities
- Performance monitoring
"""

import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
import random

from rl_agent import RLSandboxEnv, ACTION_NAMES
from rl_diplomacy_agent import DiplomacyRLAgent
from rl_diplomacy_interface import get_diplomacy_state_vector
from world.engine import WorldEngine


class RLAgentManager:
    """Manages multiple RL agents during live simulation."""

    def __init__(self, model_dir: str = "artifacts/models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # Agent instances
        self.population_agent: Optional[RLSandboxEnv] = None
        self.diplomacy_agent: Optional[DiplomacyRLAgent] = None

        # Agent states
        self.population_enabled = False
        self.diplomacy_enabled = False

        # Performance tracking
        self.performance_log = []
        self.decision_log = []

        # Learning settings
        self.learning_enabled = True
        self.decision_interval = 10  # Make decisions every N ticks
        self.last_decision_tick = 0

    def load_population_agent(self, model_path: Optional[str] = None) -> bool:
        """Load trained population control agent."""
        if model_path is None:
            model_path = self.model_dir / "qtable_pop_1000_1000.json"

        try:
            if model_path.exists():
                with open(model_path, 'r') as f:
                    qtable_data = json.load(f)

                # Create agent and load Q-table
                self.population_agent = RLSandboxEnv()
                self.population_agent.q = qtable_data  # Load Q-table into self.q
                self.population_enabled = True

                print(f"✅ Loaded population RL agent from {model_path}")
                return True
            else:
                print(f"❌ Population agent model not found: {model_path}")
                return False

        except Exception as e:
            print(f"❌ Error loading population agent: {e}")
            return False

    def load_diplomacy_agent(self, model_path: Optional[str] = None) -> bool:
        """Load trained diplomacy agent."""
        if model_path is None:
            model_path = self.model_dir / "diplomacy_qtable.json"

        try:
            if model_path.exists():
                # Create agent and load Q-table using the agent's load method
                self.diplomacy_agent = DiplomacyRLAgent()
                success = self.diplomacy_agent.load_q_table(str(model_path))
                if success:
                    self.diplomacy_enabled = True
                    print(f"✅ Loaded diplomacy RL agent from {model_path}")
                    return True
                else:
                    print(f"❌ Failed to load diplomacy agent from {model_path}")
                    return False
            else:
                print(f"❌ Diplomacy agent model not found: {model_path}")
                return False

        except Exception as e:
            print(f"❌ Error loading diplomacy agent: {e}")
            return False

    def save_agents(self):
        """Save current agent states."""
        try:
            if self.population_agent and hasattr(self.population_agent, 'q'):
                pop_path = self.model_dir / "population_qtable.json"
                with open(pop_path, 'w') as f:
                    json.dump(dict(self.population_agent.q), f, indent=2)
                print(f"💾 Saved population agent to {pop_path}")

            if self.diplomacy_agent and hasattr(self.diplomacy_agent, 'q_table'):
                dip_path = self.model_dir / "diplomacy_qtable.json"
                # Use the agent's save method to save in correct format
                self.diplomacy_agent.save_q_table(str(dip_path))
                print(f"💾 Saved diplomacy agent to {dip_path}")

        except Exception as e:
            print(f"❌ Error saving agents: {e}")

    def make_population_decision(self, world: WorldEngine) -> Optional[str]:
        """Make population control decision."""
        if not self.population_enabled or not self.population_agent:
            return None

        try:
            # Set the world on the agent
            self.population_agent.world = world

            # Get current state from the agent
            state = self.population_agent._get_state()

            # Choose action
            if random.random() < self.population_agent.epsilon:
                action_idx = random.randint(0, len(ACTION_NAMES) - 1)
            else:
                # Use the agent's Q-table to get best action
                key = self.population_agent._discretize_state(state)
                if hasattr(self.population_agent, 'q') and key in self.population_agent.q:
                    q_values = self.population_agent.q[key]
                    action_idx = q_values.index(max(q_values))
                else:
                    action_idx = random.randint(0, len(ACTION_NAMES) - 1)

            action_name = ACTION_NAMES[action_idx]

            # Execute action on the world
            self.population_agent._execute_action(world, action_idx)

            # Log decision
            self.decision_log.append({
                'tick': world._tick_count,
                'agent': 'population',
                'action': action_name,
                'state': state
            })

            return action_name

        except Exception as e:
            print(f"❌ Population decision error: {e}")
            return None

    def make_diplomacy_decision(self, world: WorldEngine) -> Optional[str]:
        """Make diplomacy decision."""
        if not self.diplomacy_enabled or not self.diplomacy_agent:
            return None

        try:
            # Get diplomacy state
            state_vector = get_diplomacy_state_vector(world)
            if not state_vector:
                return None

            # Choose action using the agent's select_action method
            action_idx = self.diplomacy_agent.select_action(state_vector)
            action_name = self.diplomacy_agent.action_names[action_idx]

            # Execute diplomacy action
            self._execute_diplomacy_action(world, action_idx)

            # Log decision
            self.decision_log.append({
                'tick': world._tick_count,
                'agent': 'diplomacy',
                'action': action_name,
                'state': state_vector
            })

            return action_name

        except Exception as e:
            print(f"❌ Diplomacy decision error: {e}")
            return None

    def _execute_diplomacy_action(self, world: WorldEngine, action_idx: int):
        """Execute diplomacy action in the world."""
        # This would integrate with your diplomacy system
        # For now, just log the intended action
        action_name = self.diplomacy_agent.action_names[action_idx]
        print(f"🎭 RL Diplomacy Action: {action_name}")

    def update_agents(self, world: WorldEngine, reward: float):
        """Update agent learning with reward feedback."""
        if not self.learning_enabled:
            return

        try:
            # Update population agent
            if self.population_agent and self.population_enabled:
                # This would implement Q-learning update
                pass  # TODO: Implement learning update

            # Update diplomacy agent
            if self.diplomacy_agent and self.diplomacy_enabled:
                # This would implement Q-learning update
                pass  # TODO: Implement learning update

        except Exception as e:
            print(f"❌ Agent update error: {e}")

    def should_make_decision(self, current_tick: int) -> bool:
        """Check if it's time to make RL decisions."""
        return (current_tick - self.last_decision_tick) >= self.decision_interval

    def record_performance(self, world: WorldEngine, rl_actions: List[str]):
        """Record performance metrics."""
        try:
            metrics = {
                'tick': world._tick_count,
                'population': len(world.npcs) if hasattr(world, 'npcs') else 0,
                'factions': len(world.factions),
                'rl_actions': rl_actions,
                'timestamp': time.time()
            }

            self.performance_log.append(metrics)

            # Keep only recent performance data
            if len(self.performance_log) > 1000:
                self.performance_log = self.performance_log[-500:]

        except Exception as e:
            print(f"❌ Performance recording error: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current RL system status."""
        return {
            'population_agent': {
                'loaded': self.population_enabled,
                'learning': self.learning_enabled
            },
            'diplomacy_agent': {
                'loaded': self.diplomacy_enabled,
                'learning': self.learning_enabled
            },
            'decisions_made': len(self.decision_log),
            'performance_records': len(self.performance_log),
            'decision_interval': self.decision_interval
        }

    def make_rl_decisions(self, world: WorldEngine) -> List[str]:
        """Make RL decisions for current world state and execute them."""
        actions_taken = []

        if self.should_make_decision(world._tick_count):
            try:
                # Make population decision
                pop_action = self.make_population_decision(world)
                if pop_action:
                    actions_taken.append(f"Pop: {pop_action}")

                # Make diplomacy decision
                dip_action = self.make_diplomacy_decision(world)
                if dip_action:
                    actions_taken.append(f"Dipl: {dip_action}")

                self.last_decision_tick = world._tick_count

                # Record performance
                self.record_performance(world, actions_taken)

                # Log summary
                if actions_taken:
                    print(f"🤖 RL Decisions at tick {world._tick_count}: {', '.join(actions_taken)}")

            except Exception as e:
                print(f"❌ RL decision making failed: {e}")

        return actions_taken


# Global RL Manager instance
rl_manager = RLAgentManager()


def initialize_rl_agents(auto_load: bool = True) -> bool:
    """Initialize RL agents for live simulation."""
    if auto_load:
        pop_loaded = rl_manager.load_population_agent()
        dip_loaded = rl_manager.load_diplomacy_agent()

        if pop_loaded or dip_loaded:
            print("🎮 RL Agents initialized for live simulation")
            return True
        else:
            print("⚠️  No trained RL agents found. Run training first or disable RL.")
            return False

    return True


def make_rl_decisions(world: WorldEngine) -> List[str]:
    """Make RL decisions for current world state."""
    actions_taken = []

    if rl_manager.should_make_decision(world._tick_count):
        # Make population decision
        pop_action = rl_manager.make_population_decision(world)
        if pop_action:
            actions_taken.append(f"Pop: {pop_action}")

        # Make diplomacy decision
        dip_action = rl_manager.make_diplomacy_decision(world)
        if dip_action:
            actions_taken.append(f"Dipl: {dip_action}")

        rl_manager.last_decision_tick = world._tick_count

    return actions_taken


def update_rl_learning(world: WorldEngine, reward: float):
    """Update RL agents with learning feedback."""
    rl_manager.update_agents(world, reward)


def save_rl_state():
    """Save current RL agent states."""
    rl_manager.save_agents()


def get_rl_status() -> Dict[str, Any]:
    """Get RL system status."""
    return rl_manager.get_status()