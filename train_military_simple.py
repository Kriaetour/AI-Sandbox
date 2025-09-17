#!/usr/bin/env python3
"""
Simple Military RL Agent Training: Clean, focused training approach.

This script provides a simplified, robust training approach for the Military RL Agent
that avoids threading issues and focuses on steady learning progress.
"""

import time
import os
from pathlib import Path

from world.engine import WorldEngine
from tribes.tribal_manager import TribalManager
from rl_military_agent import MilitaryRLAgent
from rl_military_interface import (
    execute_military_action,
    get_military_state_vector,
    compute_military_reward
)


def create_stable_training_scenario():
    """Create a stable, predictable training scenario."""
    # Disable threading for stability
    os.environ["SANDBOX_WORLD_FAST"] = "1"
    os.environ["SANDBOX_DISABLE_PARALLELISM"] = "1"

    # Initialize world with fixed seed for reproducibility
    world = WorldEngine(seed=12345, disable_faction_saving=True)
    tribal_manager = TribalManager()
    world._tribal_manager = tribal_manager

    # Create 3 tribes with fixed configurations for consistent scenarios
    tribe_configs = [
        ("Tribe1", (0, 0), 80, {"food": 300, "wood": 200, "ore": 100}),
        ("Tribe2", (15, 15), 60, {"food": 250, "wood": 150, "ore": 80}),
        ("Tribe3", (30, 30), 100, {"food": 400, "wood": 250, "ore": 120})
    ]

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


def run_simple_training_episode(agent: MilitaryRLAgent, episode_num: int):
    """Run a single training episode with simplified logic."""
    world, tribal_manager, tribes_created = create_stable_training_scenario()

    player_tribe = tribes_created[0]  # Tribe1 as player
    enemy_tribes = tribes_created[1:]  # Tribe2 and Tribe3 as enemies

    # Episode parameters
    max_ticks = 200  # Shorter episodes
    decision_interval = 20  # More frequent decisions
    episode_reward = 0
    actions_taken = 0
    combats_initiated = 0
    successful_combats = 0

    last_state = None
    last_action = None

    # Training loop
    for tick in range(max_ticks):
        try:
            # Advance world state
            world.world_tick()
        except Exception as e:
            print(f"Warning: World tick failed at tick {tick}: {e}")
            continue

        # Agent decision point
        if tick % decision_interval == 0:
            try:
                # Get current state
                current_state_vector = get_military_state_vector(
                    player_tribe, enemy_tribes, tribal_manager, world
                )

                # Convert to discretized state
                current_state = agent.get_military_state(player_tribe, enemy_tribes)

                # Choose action (with high exploration)
                action_idx = agent.choose_action(current_state)
                action_name = agent.get_action_name(action_idx)

                # Execute action
                action_results = execute_military_action(
                    action_name, player_tribe, enemy_tribes, tribal_manager, world
                )

                # Track combat statistics
                if action_results.get("combat_initiated", False):
                    combats_initiated += 1
                    if action_results.get("success", False):
                        successful_combats += 1

                # Compute reward
                reward = compute_military_reward(action_results, last_state, current_state_vector)
                episode_reward += reward
                actions_taken += 1

                # Update Q-table if we have previous state/action
                if last_state is not None and last_action is not None:
                    agent.update_q_table(last_state, last_action, reward, current_state)

                # Store discretized state for next iteration (not the vector)
                last_state = current_state
                last_action = action_idx

            except Exception as e:
                print(f"Warning: Agent decision failed at tick {tick}: {e}")
                continue

    # Return episode statistics
    return {
        "total_reward": episode_reward,
        "actions_taken": actions_taken,
        "avg_reward": episode_reward / max(actions_taken, 1),
        "combats_initiated": combats_initiated,
        "successful_combats": successful_combats,
        "success_rate": successful_combats / max(combats_initiated, 1)
    }


def main():
    """Main training function."""
    print("🎖️ Starting Simple Military RL Agent Training")
    print("=" * 50)

    # Create agent with high exploration
    agent = MilitaryRLAgent(
        epsilon=0.9,  # Very high exploration
        lr=0.1,
        gamma=0.95
    )

    # Training parameters
    num_episodes = 50
    save_interval = 5  # Save every 5 episodes

    print(f"Training for {num_episodes} episodes...")
    print("High exploration mode (epsilon=0.9)")
    print(f"Save interval: {save_interval} episodes")
    print("-" * 50)

    # Ensure save directory exists
    Path("artifacts/models").mkdir(parents=True, exist_ok=True)
    save_path = "artifacts/models/military_qtable_simple.json"

    start_time = time.time()

    for episode in range(num_episodes):
        # Run episode
        episode_stats = run_simple_training_episode(agent, episode + 1)

        # Decay epsilon slowly
        agent.epsilon = max(0.3, agent.epsilon * 0.995)

        # Log progress
        if (episode + 1) % 2 == 0:  # Log every 2 episodes
            elapsed = time.time() - start_time
            print(f"Episode {episode + 1:2d} | "
                  f"States: {len(agent.q_table):3d} | "
                  f"Avg Reward: {episode_stats['avg_reward']:6.1f} | "
                  f"Combats: {episode_stats['combats_initiated']:2d} | "
                  f"Success: {episode_stats['success_rate']:.1%} | "
                  f"Time: {elapsed:.1f}s")

        # Save model periodically
        if (episode + 1) % save_interval == 0:
            agent.save_q_table(save_path)
            print(f"💾 Saved model to {save_path}")

    # Final save
    agent.save_q_table(save_path)

    # Final statistics
    total_time = time.time() - start_time
    print("\n🏆 Training Complete!")
    print(f"Total Episodes: {num_episodes}")
    print(f"Final States Learned: {len(agent.q_table)}")
    print(f"Training Time: {total_time:.1f}s")
    print(f"Final Epsilon: {agent.epsilon:.3f}")
    print(f"Model saved to: {save_path}")


if __name__ == "__main__":
    main()