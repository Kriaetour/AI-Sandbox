#!/usr/bin/env python3
"""
Optimal Military RL Inference Runner
Uses trained models for optimal gameplay without further training.
"""

import argparse
import json
import os
import random
import time
from typing import Dict, List, Tuple

# Import your simulation components
from world.engine import WorldEngine
from tribes.tribal_manager import TribalManager
from rl_military_agent import MilitaryRLAgent
from rl_military_interface import execute_military_action, compute_military_reward

class OptimalMilitaryRunner:
    """Runs optimal military simulations using trained RL models."""

    def __init__(self, model_path: str, epsilon: float = 0.0):
        """Initialize with trained model."""
        self.agent = MilitaryRLAgent(epsilon=epsilon)
        self.load_model(model_path)
        print(f"✅ Loaded model: {model_path}")
        print(f"📊 Model has {len(self.agent.q_table)} learned states")

    def load_model(self, model_path: str):
        """Load trained Q-table from file."""
        try:
            with open(model_path, 'r') as f:
                data = json.load(f)
                if 'q_table' in data:
                    self.agent.q_table = data['q_table']
                else:
                    # Direct Q-table format
                    self.agent.q_table = data
        except Exception as e:
            raise ValueError(f"Failed to load model {model_path}: {e}")

    def run_optimal_simulation(self,
                              num_episodes: int = 1,
                              max_ticks: int = 1000,
                              num_tribes: int = 8,
                              world_seed: int = None,
                              verbose: bool = True) -> Dict:
        """Run optimal simulation using trained policy."""

        results = {
            'episodes': [],
            'total_actions': 0,
            'total_rewards': 0,
            'avg_reward_per_action': 0,
            'states_visited': set(),
            'action_distribution': {},
            'duration_seconds': 0
        }

        start_time = time.time()

        for episode in range(num_episodes):
            if verbose:
                print(f"\n🎯 Episode {episode + 1}/{num_episodes}")

            # Initialize world
            seed = world_seed or random.randint(0, 999999)
            world = WorldEngine(seed=seed, disable_faction_saving=True)
            tribal_manager = TribalManager()
            world._tribal_manager = tribal_manager

            # Create diverse tribes
            tribes = []
            for i in range(num_tribes):
                tribe = self._create_diverse_tribe(tribal_manager, world, episode, i, seed)
                tribes.append(tribe)

            episode_results = self._run_episode(world, tribal_manager, tribes, max_ticks, verbose)
            results['episodes'].append(episode_results)

            # Aggregate results
            results['total_actions'] += episode_results['actions']
            results['total_rewards'] += episode_results['total_reward']
            results['states_visited'].update(episode_results['states_visited'])

            for action, count in episode_results['action_counts'].items():
                results['action_distribution'][action] = results['action_distribution'].get(action, 0) + count

        results['duration_seconds'] = time.time() - start_time
        results['avg_reward_per_action'] = results['total_rewards'] / max(results['total_actions'], 1)
        results['unique_states_visited'] = len(results['states_visited'])

        return results

    def _create_diverse_tribe(self, tribal_manager, world, episode_num, tribe_idx, world_seed):
        """Create a tribe with diverse characteristics for interesting scenarios."""
        from technology_system import technology_manager
        from factions.faction import Faction

        random.seed(world_seed * 1000 + episode_num * 997 + tribe_idx * 13)

        # Diverse archetypes
        archetypes = [
            ("Outpost", (20, 100), 0.5),
            ("Village", (100, 300), 1.0),
            ("Town", (300, 800), 2.0),
            ("City", (800, 1500), 3.0),
            ("Citadel", (1500, 2500), 4.0),
        ]

        name_root, pop_range, res_mult = random.choice(archetypes)
        base_name = f"{name_root}_{episode_num}_{tribe_idx}"

        faction = Faction(name=base_name)
        faction.population = random.randint(*pop_range)

        # Diverse resources
        base_resources = random.randint(100, 500) * res_mult
        faction.resources = {
            "food": float(random.randint(int(base_resources * 0.5), int(base_resources * 2.0))),
            "Wood": float(random.randint(int(base_resources * 0.3), int(base_resources * 1.8))),
            "Ore": float(random.randint(int(base_resources * 0.2), int(base_resources * 1.5))),
        }

        # Diverse territory
        territory_radius = random.randint(3, 8)
        territory = []
        cx = random.randint(-30, 30)
        cy = random.randint(-30, 30)
        for dx in range(-territory_radius, territory_radius + 1):
            for dy in range(-territory_radius, territory_radius + 1):
                if abs(dx) + abs(dy) <= territory_radius:
                    territory.append((cx + dx, cy + dy))
        faction.territory = territory

        # Diverse diplomatic relationships
        for existing_name, existing_faction in world.factions.items():
            rel = random.uniform(-1.0, 1.0)
            faction.relationships[existing_name] = rel
            if isinstance(existing_faction, Faction):
                existing_faction.relationships[base_name] = rel

        # Diverse technology
        all_techs = [
            "weapons", "iron_weapons", "steel_weapons", "military_organization",
            "siege_engineering", "horseback_riding", "archery", "shield_making",
            "castle_building", "naval_warfare", "gunpowder", "cannon"
        ]

        unlock_count = random.randint(2, 8)
        unlocked_techs = random.sample(all_techs, min(unlock_count, len(all_techs)))
        technology_manager.unlocked_technologies[base_name] = set(unlocked_techs)

        world.factions[base_name] = faction

        # Create tribe
        if base_name not in tribal_manager.tribes:
            tribe = tribal_manager.create_tribe(base_name, (cx, cy))
            if not hasattr(tribe, 'id'):
                setattr(tribe, 'id', base_name)

        return tribal_manager.tribes[base_name]

    def _run_episode(self, world, tribal_manager, tribes, max_ticks, verbose):
        """Run a single episode using optimal policy."""
        episode_results = {
            'actions': 0,
            'total_reward': 0,
            'states_visited': set(),
            'action_counts': {},
            'ticks': 0
        }

        for tick in range(max_ticks):
            world.world_tick()
            active = list(tribal_manager.tribes.values())

            if len(active) < 3:
                if verbose:
                    print(f"  Episode ended early: only {len(active)} tribes remaining")
                break

            # Multiple decisions per tick for optimal play
            decisions = min(8, len(active))
            for _ in range(decisions):
                actor = random.choice(active)
                targets_pool = [t for t in active if t != actor]

                if len(targets_pool) < 2:
                    continue

                # Select optimal number of targets
                sel_count = min(len(targets_pool), random.randint(2, 4))
                selected = random.sample(targets_pool, sel_count)

                state = self.agent.get_military_state(actor, selected, world)
                if state is None:
                    continue

                episode_results['states_visited'].add(tuple(int(x) for x in state))
                action_idx = self.agent.choose_action(state)
                action_name = self.agent.get_action_name(action_idx)

                episode_results['actions'] += 1
                episode_results['action_counts'][action_name] = episode_results['action_counts'].get(action_name, 0) + 1

                action_results = execute_military_action(action_name, actor, selected, tribal_manager, world)
                next_state = self.agent.get_military_state(actor, selected, world)
                reward = compute_military_reward(action_results, state, next_state)

                episode_results['total_reward'] += reward

            episode_results['ticks'] = tick + 1

            if verbose and tick % 100 == 0:
                print(f"  Tick {tick}: {episode_results['actions']} actions, reward: {episode_results['total_reward']:.1f}")

        return episode_results

def main():
    parser = argparse.ArgumentParser(description="Optimal Military RL Inference Runner")
    parser.add_argument("--model", required=True,
                       help="Path to trained model (e.g., artifacts/models/military_100p_final_ep10000.json)")
    parser.add_argument("--episodes", type=int, default=5, help="Number of episodes to run")
    parser.add_argument("--ticks", type=int, default=1000, help="Max ticks per episode")
    parser.add_argument("--tribes", type=int, default=8, help="Number of tribes per episode")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")

    args = parser.parse_args()

    # Validate model exists
    if not os.path.exists(args.model):
        print(f"❌ Model file not found: {args.model}")
        print("\nAvailable models:")
        models_dir = "artifacts/models"
        if os.path.exists(models_dir):
            for model_file in sorted(os.listdir(models_dir)):
                if model_file.endswith('.json'):
                    print(f"  {models_dir}/{model_file}")
        return

    # Run optimal simulation
    runner = OptimalMilitaryRunner(args.model, epsilon=0.0)  # Pure exploitation

    print(f"🚀 Running optimal simulation with {args.episodes} episodes...")
    print(f"📊 Using model: {args.model}")
    print(f"🎯 Tribes per episode: {args.tribes}")
    print(f"⏰ Max ticks: {args.ticks}")

    results = runner.run_optimal_simulation(
        num_episodes=args.episodes,
        max_ticks=args.ticks,
        num_tribes=args.tribes,
        world_seed=args.seed,
        verbose=not args.quiet
    )

    # Print results
    print("\n" + "="*60)
    print("🏆 OPTIMAL SIMULATION RESULTS")
    print("="*60)
    print(f"Episodes completed: {len(results['episodes'])}")
    print(f"Total actions taken: {results['total_actions']}")
    print(f"Total reward: {results['total_rewards']:.2f}")
    print(f"Average reward per action: {results['avg_reward_per_action']:.3f}")
    print(f"Unique states visited: {results['unique_states_visited']}")
    print(f"Duration: {results['duration_seconds']:.1f} seconds")

    print("\n📈 Action Distribution:")
    for action, count in sorted(results['action_distribution'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / results['total_actions']) * 100
        print(f"  {action}: {count} ({percentage:.1f}%)")

    print("\n💾 Episode Breakdown:")
    for i, ep in enumerate(results['episodes']):
        print(f"  Episode {i+1}: {ep['actions']} actions, {ep['total_reward']:.2f} reward, {len(ep['states_visited'])} states")

if __name__ == "__main__":
    main()