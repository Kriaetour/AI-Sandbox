#!/usr/bin/env python3
"""
Ultra Training: Maximum diversity approach for Military RL Agent.

This script uses extreme measures to force state diversity and learning.
"""

import time
import os
import random
from pathlib import Path

from world.engine import WorldEngine
from tribes.tribal_manager import TribalManager
from rl_military_agent import MilitaryRLAgent
from rl_military_interface import (
    execute_military_action,
    get_military_state_vector,
    compute_military_reward
)


def create_ultra_diverse_scenario(seed_offset=0):
    """Create maximum diversity scenario with extreme randomization."""
    # Force single-threaded execution
    os.environ["SANDBOX_WORLD_FAST"] = "1"
    os.environ["SANDBOX_DISABLE_PARALLELISM"] = "1"

    # Use highly variable seeds
    world_seed = random.randint(0, 100000) + seed_offset * 1000
    world = WorldEngine(seed=world_seed, disable_faction_saving=True)
    tribal_manager = TribalManager()
    world._tribal_manager = tribal_manager

    # Create 5-8 tribes with extreme randomization
    num_tribes = random.randint(5, 8)

    tribe_configs = []
    for i in range(num_tribes):
        # Extreme location spread
        location = (
            random.randint(-50, 50),
            random.randint(-50, 50)
        )

        # Extreme population and resource variation
        population = random.randint(20, 300)  # Very wide range
        resources = {
            "food": random.randint(50, 1000),   # Extreme variation
            "wood": random.randint(25, 800),    # Extreme variation
            "ore": random.randint(10, 600)      # Extreme variation
        }

        tribe_configs.append((f"Tribe{i+1}", location, population, resources))

    tribes_created = []
    for tribe_name, location, population, resources in tribe_configs:
        # Create tribe
        tribal_manager.create_tribe(tribe_name, f"founder_{tribe_name.lower()}", location)

        # Create corresponding faction
        if tribe_name not in world.factions:
            from factions.faction import Faction
            faction = Faction(name=tribe_name)
            faction.territory = [location]
            faction.population = population
            faction.resources = resources
            world.factions[tribe_name] = faction

        tribes_created.append(tribal_manager.tribes[tribe_name])

    return world, tribal_manager, tribes_created


def run_ultra_episode(agent: MilitaryRLAgent, episode_num: int):
    """Run episode with maximum exploration and forced diversity."""
    world, tribal_manager, tribes_created = create_ultra_diverse_scenario(episode_num)

    # Random tribe selection for maximum variety
    player_tribe = random.choice(tribes_created)
    enemy_tribes = [t for t in tribes_created if t != player_tribe]

    # Ultra-short episodes for rapid iteration
    max_ticks = 100
    decision_interval = 10  # Very frequent decisions

    episode_reward = 0
    actions_taken = 0
    combats_initiated = 0
    successful_combats = 0

    last_state = None
    last_action = None

    # Force different random seed for each episode
    random.seed(episode_num * 1000)

    for tick in range(max_ticks):
        try:
            # Advance world state
            world.world_tick()
        except Exception:
            pass  # Continue if world tick fails

        if tick % decision_interval == 0:
            try:
                # Get current state
                current_state_vector = get_military_state_vector(
                    player_tribe, enemy_tribes, tribal_manager, world
                )

                # Convert to discretized state
                current_state = agent.get_military_state(player_tribe, enemy_tribes)

                # Ultra-high exploration
                action_idx = agent.choose_action(current_state)
                action_name = agent.get_action_name(action_idx)

                # Execute action
                action_results = execute_military_action(
                    action_name, player_tribe, enemy_tribes, tribal_manager, world
                )

                # Track statistics
                if action_results.get("combat_initiated", False):
                    combats_initiated += 1
                    if action_results.get("success", False):
                        successful_combats += 1

                # Compute reward
                reward = compute_military_reward(action_results, last_state, current_state_vector)
                episode_reward += reward
                actions_taken += 1

                # Update Q-table
                if last_state is not None and last_action is not None:
                    agent.update_q_table(last_state, last_action, reward, current_state)

                # Store discretized state
                last_state = current_state
                last_action = action_idx

            except Exception:
                pass  # Silent error handling for ultra training

    return {
        "total_reward": episode_reward,
        "actions_taken": actions_taken,
        "avg_reward": episode_reward / max(actions_taken, 1),
        "combats_initiated": combats_initiated,
        "successful_combats": successful_combats,
        "success_rate": successful_combats / max(combats_initiated, 1),
        "states_learned": len(agent.q_table)
    }


def main():
    """Ultra training main function."""
    print("🚀 Starting ULTRA Military RL Agent Training")
    print("=" * 60)

    # Agent with maximum exploration
    agent = MilitaryRLAgent(
        epsilon=0.99,  # Near-pure exploration
        lr=0.3,        # High learning rate
        gamma=0.8      # Lower discount for immediate rewards
    )

    # Ultra training parameters
    num_episodes = 200
    save_interval = 20

    print(f"Training for {num_episodes} episodes...")
    print("Ultra exploration mode (epsilon=0.99)")
    print("Extreme scenario diversity")
    print("Rapid iteration (100 ticks, 10-interval decisions)")
    print(f"Save interval: {save_interval} episodes")
    print("-" * 60)

    Path("artifacts/models").mkdir(parents=True, exist_ok=True)
    save_path = "artifacts/models/military_qtable_ultra.json"

    start_time = time.time()
    total_combats = 0
    total_successful_combats = 0

    for episode in range(num_episodes):
        # Run ultra episode
        episode_stats = run_ultra_episode(agent, episode + 1)

        # Very slow epsilon decay
        agent.epsilon = max(0.5, agent.epsilon * 0.999)

        # Accumulate statistics
        total_combats += episode_stats["combats_initiated"]
        total_successful_combats += episode_stats["successful_combats"]

        # Log every 10 episodes
        if (episode + 1) % 10 == 0:
            elapsed = time.time() - start_time
            overall_success_rate = total_successful_combats / max(total_combats, 1)
            print(f"Episode {episode + 1:3d} | "
                  f"States: {len(agent.q_table):3d} | "
                  f"Avg Reward: {episode_stats['avg_reward']:6.1f} | "
                  f"Combats: {episode_stats['combats_initiated']:2d} | "
                  f"Success: {episode_stats['success_rate']:.1%} | "
                  f"Overall: {overall_success_rate:.1%} | "
                  f"Time: {elapsed:.1f}s")

        # Save periodically
        if (episode + 1) % save_interval == 0:
            agent.save_q_table(save_path)
            print(f"💾 Saved model to {save_path}")

    # Final save
    agent.save_q_table(save_path)

    # Final statistics
    total_time = time.time() - start_time
    overall_success_rate = total_successful_combats / max(total_combats, 1)

    print("\n🎯 ULTRA Training Complete!")
    print(f"Total Episodes: {num_episodes}")
    print(f"Final States Learned: {len(agent.q_table)}")
    print(f"Total Combats: {total_combats}")
    print(f"Overall Success Rate: {overall_success_rate:.1%}")
    print(f"Training Time: {total_time:.1f}s")
    print(f"Final Epsilon: {agent.epsilon:.3f}")
    print(f"Model saved to: {save_path}")

    # Show top learned actions
    if agent.q_table:
        print("\n📊 Top Learned Actions:")
        q_values = list(agent.q_table.values())[0]
        actions = ['aggressive_attack', 'defensive_posture', 'strategic_retreat',
                  'force_reinforcement', 'tech_investment', 'diplomatic_pressure',
                  'siege_preparation', 'peaceful_approach']

        sorted_actions = sorted(zip(actions, q_values), key=lambda x: x[1], reverse=True)
        for i, (action, q_val) in enumerate(sorted_actions[:3]):
            print(f"  {i+1}. {action}: {q_val:.1f}")


if __name__ == "__main__":
    main()