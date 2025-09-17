#!/usr/bin/env python3
"""
Optimized Military RL Agent Training: Final version with maximum exploration.

This script provides the most aggressive training approach to break the agent
out of local optima and achieve diverse state learning.
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


def create_diverse_scenario(seed_offset=0):
    """Create a diverse training scenario with random elements."""
    # Disable all threading for stability
    os.environ["SANDBOX_WORLD_FAST"] = "1"
    os.environ["SANDBOX_DISABLE_PARALLELISM"] = "1"

    # Use different seeds for variety
    world = WorldEngine(seed=12345 + seed_offset, disable_faction_saving=True)
    tribal_manager = TribalManager()
    world._tribal_manager = tribal_manager

    # Create 4 tribes with random but controlled parameters
    import random
    random.seed(54321 + seed_offset)  # Different seed for tribe generation

    tribe_configs = []
    for i in range(4):
        # Random locations within a reasonable spread
        location = (
            random.randint(-20, 20),
            random.randint(-20, 20)
        )

        # Random but balanced populations and resources
        population = random.randint(40, 120)
        resources = {
            "food": random.randint(150, 400),
            "wood": random.randint(100, 300),
            "ore": random.randint(50, 200)
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


def run_optimized_episode(agent: MilitaryRLAgent, episode_num: int):
    """Run an episode with maximum exploration and error handling."""
    world, tribal_manager, tribes_created = create_diverse_scenario(episode_num)

    # Randomly select player tribe for variety
    import random
    player_tribe = random.choice(tribes_created)
    enemy_tribes = [t for t in tribes_created if t != player_tribe]

    # Episode parameters - optimized for learning
    max_ticks = 150  # Shorter episodes
    decision_interval = 15  # More frequent decisions
    episode_reward = 0
    actions_taken = 0
    combats_initiated = 0
    successful_combats = 0

    last_state = None  # Start with None, will be set to tuple on first iteration
    last_action = None

    # Training loop with comprehensive error handling
    for tick in range(max_ticks):
        try:
            # Advance world state
            world.world_tick()
        except Exception:
            # If world tick fails, continue without it
            pass

        # Agent decision point
        if tick % decision_interval == 0:
            try:
                # Get current state
                current_state_vector = get_military_state_vector(
                    player_tribe, enemy_tribes, tribal_manager, world
                )

                # Convert to discretized state for Q-learning
                current_state = agent.get_military_state(player_tribe, enemy_tribes)

                # Choose action (maximum exploration)
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

            except Exception:
                # Silently handle agent errors to keep training going
                pass

    # Return episode statistics
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
    """Main optimized training function."""
    print("🎖️ Starting OPTIMIZED Military RL Agent Training")
    print("=" * 60)

    # Create agent with MAXIMUM exploration
    agent = MilitaryRLAgent(
        epsilon=0.95,  # Maximum exploration
        lr=0.2,        # Higher learning rate
        gamma=0.9      # Slightly lower discount for immediate rewards
    )

    # Training parameters - optimized for breakthrough
    num_episodes = 100
    save_interval = 10  # Save every 10 episodes

    print(f"Training for {num_episodes} episodes...")
    print("Maximum exploration mode (epsilon=0.95)")
    print("Diverse scenarios with random tribe selection")
    print("Higher learning rate (0.2) for faster adaptation")
    print(f"Save interval: {save_interval} episodes")
    print("-" * 60)

    # Ensure save directory exists
    Path("artifacts/models").mkdir(parents=True, exist_ok=True)
    save_path = "artifacts/models/military_qtable_optimized.json"

    start_time = time.time()
    total_combats = 0
    total_successful_combats = 0

    for episode in range(num_episodes):
        # Run episode
        episode_stats = run_optimized_episode(agent, episode + 1)

        # Decay epsilon very slowly
        agent.epsilon = max(0.4, agent.epsilon * 0.998)  # Keep exploring longer

        # Accumulate statistics
        total_combats += episode_stats["combats_initiated"]
        total_successful_combats += episode_stats["successful_combats"]

        # Log progress every 5 episodes
        if (episode + 1) % 5 == 0:
            elapsed = time.time() - start_time
            overall_success_rate = total_successful_combats / max(total_combats, 1)
            print(f"Episode {episode + 1:3d} | "
                  f"States: {len(agent.q_table):3d} | "
                  f"Avg Reward: {episode_stats['avg_reward']:6.1f} | "
                  f"Combats: {episode_stats['combats_initiated']:2d} | "
                  f"Success: {episode_stats['success_rate']:.1%} | "
                  f"Overall: {overall_success_rate:.1%} | "
                  f"Time: {elapsed:.1f}s")

        # Save model periodically
        if (episode + 1) % save_interval == 0:
            agent.save_q_table(save_path)
            print(f"💾 Saved model to {save_path}")

    # Final save
    agent.save_q_table(save_path)

    # Final statistics
    total_time = time.time() - start_time
    overall_success_rate = total_successful_combats / max(total_combats, 1)

    print("\n🏆 OPTIMIZED Training Complete!")
    print(f"Total Episodes: {num_episodes}")
    print(f"Final States Learned: {len(agent.q_table)}")
    print(f"Total Combats: {total_combats}")
    print(f"Overall Success Rate: {overall_success_rate:.1%}")
    print(f"Training Time: {total_time:.1f}s")
    print(f"Final Epsilon: {agent.epsilon:.3f}")
    print(f"Model saved to: {save_path}")

    # Show best learned actions if any states were learned
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