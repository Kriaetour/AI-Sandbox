#!/usr/bin/env python3
"""
Enhanced Military RL Integration
Integrates optimized military RL agents into the main AI Sandbox simulation.
"""

import os
import random
import time
from typing import Dict, List, Optional, Tuple
from world.engine import WorldEngine
from tribes.tribal_manager import TribalManager
from rl_military_agent import MilitaryRLAgent
from rl_military_interface import execute_military_action, compute_military_reward

class MilitaryRLController:
    """Enhanced military RL controller for AI Sandbox integration."""

    def __init__(self, 
                 model_path: str = None, 
                 epsilon: float = 0.1,
                 decision_interval: int = 20):
        """
        Initialize military RL controller.
        
        Args:
            model_path: Path to trained model. If None, uses best available.
            epsilon: Exploration rate (0.0 for pure exploitation)
            decision_interval: Ticks between military decisions
        """
        self.decision_interval = decision_interval
        self.last_decision_tick = 0
        self.total_actions = 0
        self.total_reward = 0.0
        self.states_visited = set()
        
        # Load best model if none specified
        if model_path is None:
            model_path = self._find_best_model()
        
        # Initialize military RL agent
        self.agent = MilitaryRLAgent(epsilon=epsilon)
        self._load_model(model_path)
        
        print(f"🤖 Military RL Controller initialized")
        print(f"   Model: {model_path}")
        print(f"   States: {len(self.agent.q_table)}")
        print(f"   Decision interval: {decision_interval} ticks")
        print(f"   Exploration rate: {epsilon}")

    def _find_best_model(self) -> str:
        """Find the best available trained model."""
        models_dir = "artifacts/models"
        
        # Prioritize models by expected quality
        preferred_models = [
            "military_qtable_ultra_v2_final_ep1501.json",
            "military_qtable_ultra_v2_final_ep501.json", 
            "military_qtable_ultra_v2_final_ep21.json",
            "military_100p_final_ep5.json",
            "military_qtable_enhanced_diversity.json"
        ]
        
        for model_name in preferred_models:
            model_path = os.path.join(models_dir, model_name)
            if os.path.exists(model_path):
                return model_path
        
        # Fallback: find any military model
        if os.path.exists(models_dir):
            for file in os.listdir(models_dir):
                if file.startswith("military_") and file.endswith(".json"):
                    return os.path.join(models_dir, file)
        
        raise FileNotFoundError("No trained military models found!")

    def _load_model(self, model_path: str):
        """Load trained Q-table from file."""
        try:
            import json
            with open(model_path, 'r') as f:
                data = json.load(f)
                if 'q_table' in data:
                    self.agent.q_table = data['q_table']
                else:
                    self.agent.q_table = data
        except Exception as e:
            raise ValueError(f"Failed to load model {model_path}: {e}")

    def should_make_decision(self, current_tick: int) -> bool:
        """Check if it's time to make a military decision."""
        return (current_tick - self.last_decision_tick) >= self.decision_interval

    def make_military_decisions(self, world: WorldEngine, tribal_manager: TribalManager, current_tick: int) -> Dict:
        """Make military decisions for active tribes."""
        if not self.should_make_decision(current_tick):
            return {"actions": 0, "reward": 0.0}

        self.last_decision_tick = current_tick
        active_tribes = list(tribal_manager.tribes.values())
        
        if len(active_tribes) < 3:
            return {"actions": 0, "reward": 0.0}

        decision_results = {
            "actions": 0,
            "reward": 0.0,
            "decisions": []
        }

        # Make multiple strategic decisions per interval
        num_decisions = min(3, len(active_tribes))
        
        for _ in range(num_decisions):
            actor = random.choice(active_tribes)
            potential_targets = [t for t in active_tribes if t != actor]
            
            if len(potential_targets) < 2:
                continue

            # Select 2-4 tribes to consider in decision
            num_targets = min(len(potential_targets), random.randint(2, 4))
            targets = random.sample(potential_targets, num_targets)

            try:
                # Get military state
                state = self.agent.get_military_state(actor, targets, world)
                if state is None:
                    continue

                # Record state for analytics
                self.states_visited.add(tuple(int(x) for x in state))

                # Choose optimal action
                action_idx = self.agent.choose_action(state)
                action_name = self.agent.get_action_name(action_idx)

                # Execute action
                action_results = execute_military_action(action_name, actor, targets, tribal_manager, world)
                
                # Compute reward
                next_state = self.agent.get_military_state(actor, targets, world)
                reward = compute_military_reward(action_results, state, next_state)

                # Update tracking
                decision_results["actions"] += 1
                decision_results["reward"] += reward
                decision_results["decisions"].append({
                    "actor": actor.name,
                    "action": action_name,
                    "targets": [t.name for t in targets],
                    "reward": reward
                })

                self.total_actions += 1
                self.total_reward += reward

            except Exception as e:
                print(f"⚠️  Military decision error: {e}")
                continue

        return decision_results

    def get_performance_stats(self) -> Dict:
        """Get performance statistics."""
        return {
            "total_actions": self.total_actions,
            "total_reward": self.total_reward,
            "avg_reward_per_action": self.total_reward / max(self.total_actions, 1),
            "states_visited": len(self.states_visited),
            "model_states": len(self.agent.q_table)
        }

    def print_performance_summary(self):
        """Print performance summary."""
        stats = self.get_performance_stats()
        print("\n🎯 MILITARY RL PERFORMANCE SUMMARY")
        print("="*50)
        print(f"Total Actions: {stats['total_actions']}")
        print(f"Total Reward: {stats['total_reward']:.2f}")
        print(f"Avg Reward/Action: {stats['avg_reward_per_action']:.3f}")
        print(f"States Visited: {stats['states_visited']}")
        print(f"Model Coverage: {stats['model_states']} learned states")


def run_simulation_with_military_rl(num_ticks: int = 2000,
                                   model_path: str = None,
                                   epsilon: float = 0.1,
                                   decision_interval: int = 20,
                                   num_tribes: int = 8,
                                   verbose: bool = True) -> Dict:
    """
    Run AI Sandbox simulation with enhanced military RL integration.
    
    Args:
        num_ticks: Number of simulation ticks
        model_path: Path to trained model (auto-selected if None)
        epsilon: Exploration rate (0.0 for pure exploitation)
        decision_interval: Ticks between military decisions
        num_tribes: Number of tribes to create
        verbose: Enable detailed output
    
    Returns:
        Simulation results dictionary
    """
    
    if verbose:
        print("🚀 STARTING AI SANDBOX WITH MILITARY RL")
        print("="*60)
    
    # Initialize world and tribes
    world = WorldEngine(seed=random.randint(0, 999999))
    tribal_manager = TribalManager()
    world._tribal_manager = tribal_manager
    
    # Create diverse tribes using the tribal manager directly
    for i in range(num_tribes):
        # Generate random location for the tribe
        location = (random.randint(-20, 20), random.randint(-20, 20))
        
        # Generate tribe name
        tribe_name = f"Tribe_{i+1}_{random.choice(['River', 'Mountain', 'Forest', 'Desert'])}"
        founder_id = f"founder_{tribe_name.lower().replace(' ', '_')}"
        
        # Create the tribe
        tribe = tribal_manager.create_tribe(tribe_name, founder_id, location)
        
        if verbose and i < 3:  # Show first few tribes
            print(f"🏘️  Created tribe: {tribe.name}")
        
        # Add some initial members
        member_count = random.randint(3, 7)
        for j in range(member_count):
            member_id = f"{tribe_name.lower().replace(' ', '_')}_member_{j}"
            from tribes.tribe import TribalRole
            tribe.add_member(member_id, random.choice(list(TribalRole)))
    
    # Initialize military RL controller
    military_controller = MilitaryRLController(
        model_path=model_path,
        epsilon=epsilon,
        decision_interval=decision_interval
    )
    
    # Run simulation
    start_time = time.time()
    total_military_actions = 0
    total_military_reward = 0.0
    
    for tick in range(num_ticks):
        # Standard world tick
        world.world_tick()
        
        # Military RL decisions
        if len(tribal_manager.tribes) >= 3:
            military_results = military_controller.make_military_decisions(world, tribal_manager, tick)
            total_military_actions += military_results["actions"]
            total_military_reward += military_results["reward"]
            
            # Verbose logging
            if verbose and military_results["actions"] > 0:
                print(f"Tick {tick}: {military_results['actions']} military actions, "
                      f"reward: {military_results['reward']:.1f}")
        
        # Periodic status
        if verbose and tick % 500 == 0 and tick > 0:
            active_tribes = len(tribal_manager.tribes)
            print(f"[{tick:4d}] Active tribes: {active_tribes}, "
                  f"Military actions: {total_military_actions}, "
                  f"Avg reward: {total_military_reward/max(total_military_actions,1):.2f}")
    
    duration = time.time() - start_time
    
    # Final results
    results = {
        "duration": duration,
        "final_tribes": len(tribal_manager.tribes),
        "military_actions": total_military_actions,
        "military_reward": total_military_reward,
        "military_stats": military_controller.get_performance_stats()
    }
    
    if verbose:
        print("\n" + "="*60)
        print("🏆 SIMULATION COMPLETE")
        print("="*60)
        print(f"Duration: {duration:.1f} seconds")
        print(f"Final tribes: {results['final_tribes']}")
        print(f"Military actions: {total_military_actions}")
        print(f"Military reward: {total_military_reward:.2f}")
        
        military_controller.print_performance_summary()
    
    return results


if __name__ == "__main__":
    # Demo run
    results = run_simulation_with_military_rl(
        num_ticks=1000,
        epsilon=0.0,  # Pure exploitation
        decision_interval=15,
        num_tribes=6,
        verbose=True
    )
    print(f"\n✅ Demo completed: {results['military_actions']} military actions taken")