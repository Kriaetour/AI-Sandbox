#!/usr/bin/env python3
"""
Train Military RL Agent: Train an agent to learn optimal military strategies.

This script trains a Military RL Agent to make strategic military decisions
in tribal warfare scenarios, learning from combat outcomes and strategic positioning.
"""

import argparse
import random
import time
from pathlib import Path
from typing import Dict

from world.engine import WorldEngine
from tribes.tribal_manager import TribalManager
from rl_military_agent import MilitaryRLAgent
from rl_military_interface import (
    get_military_actions,
    execute_military_action,
    get_military_state_vector,
    compute_military_reward
)


def run_military_training_episode(
    agent: MilitaryRLAgent,
    max_ticks: int = 1000,
    intervention_interval: int = 50
) -> Dict:
    """
    Run a single training episode for military RL.

    Args:
        agent: The military RL agent to train
        max_ticks: Maximum ticks per episode
        intervention_interval: How often the agent makes decisions

    Returns:
        Dict containing episode statistics
    """
    # Set fast mode for training
    import os
    os.environ["SANDBOX_WORLD_FAST"] = "1"

    # Initialize world with tribal system
    world = WorldEngine(seed=random.randint(0, 10000), disable_faction_saving=True)
    tribal_manager = TribalManager()
    world._tribal_manager = tribal_manager  # Attach tribal manager to world

    # Create multiple tribes for interesting military scenarios - INCREASED DIVERSITY
    num_tribes = random.randint(4, 8)  # Increased from 3-6 to 4-8 tribes
    tribes_created = []

    for i in range(num_tribes):
        # Add more variation in starting locations and sizes
        location = (random.randint(-30, 30), random.randint(-30, 30))
        tribe_name = f"Tribe{i+1}"

        # Create tribe
        tribal_manager.create_tribe(tribe_name, f"founder_{tribe_name.lower()}", location)

        # Create corresponding faction with more variation
        if tribe_name not in world.factions:
            from factions.faction import Faction
            faction = Faction(name=tribe_name)
            faction.territory = [location]
            # More variation in population and resources
            faction.population = random.randint(30, 200)  # Wider range
            faction.resources = {
                "food": random.randint(100, 800),   # Wider range
                "wood": random.randint(50, 600),    # Wider range
                "ore": random.randint(25, 400)      # Wider range
            }
            world.factions[tribe_name] = faction

        tribes_created.append(tribal_manager.tribes[tribe_name])

    # Select one tribe as the "player" tribe for the agent
    player_tribe = random.choice(tribes_created)
    enemy_tribes = [t for t in tribes_created if t != player_tribe]

    episode_stats = {
        "ticks": 0,
        "total_reward": 0.0,
        "actions_taken": 0,
        "combats_initiated": 0,
        "successful_combats": 0,
        "territory_gained": 0,
        "casualties": 0,
        "action_distribution": {action: 0 for action in get_military_actions()}
    }

    # Training loop
    tick = 0
    last_state = None
    last_action = None

    while tick < max_ticks:
        # Advance world state
        world.world_tick()

        # Agent decision point
        if tick % intervention_interval == 0:
            # Get current military state
            current_state_vector = get_military_state_vector(
                player_tribe, enemy_tribes, tribal_manager, world
            )

            # Convert to discretized state for Q-learning
            current_state = agent.get_military_state(player_tribe, enemy_tribes)

            # Choose action
            action_idx = agent.choose_action(current_state)
            action_name = agent.get_action_name(action_idx)

            # Execute action
            action_results = execute_military_action(
                action_name, player_tribe, enemy_tribes, tribal_manager, world
            )

            # Compute reward
            reward = compute_military_reward(action_results, last_state, current_state_vector)

            # Update Q-table if we have previous state/action
            if last_state is not None and last_action is not None:
                agent.update_q_table(last_state, last_action, reward, current_state)

            # Update episode statistics
            episode_stats["total_reward"] += reward
            episode_stats["actions_taken"] += 1
            episode_stats["action_distribution"][action_name] += 1

            if action_results.get("combat_initiated", False):
                episode_stats["combats_initiated"] += 1
                if action_results.get("success", False):
                    episode_stats["successful_combats"] += 1

            episode_stats["territory_gained"] += action_results.get("territory_gained", 0)
            episode_stats["casualties"] += action_results.get("casualties", 0)

            # Store for next iteration
            last_state = current_state
            last_action = action_idx

        tick += 1

    episode_stats["ticks"] = tick
    return episode_stats


def train_military_agent(
    episodes: int = 50,
    max_ticks_per_episode: int = 1000,
    intervention_interval: int = 50,
    epsilon_start: float = 0.3,
    epsilon_min: float = 0.05,
    epsilon_decay: float = 0.95,
    save_path: str = "artifacts/models/military_qtable.json",
    load_path: str = None,
    log_interval: int = 10
) -> MilitaryRLAgent:
    """
    Train the military RL agent over multiple episodes.

    Args:
        episodes: Number of training episodes
        max_ticks_per_episode: Maximum ticks per episode
        intervention_interval: Decision frequency
        epsilon_start: Initial exploration rate
        epsilon_min: Minimum exploration rate
        epsilon_decay: Exploration decay rate
        save_path: Path to save trained model
        load_path: Path to load existing model
        log_interval: How often to log progress

    Returns:
        Trained MilitaryRLAgent
    """
    # Initialize agent
    agent = MilitaryRLAgent(
        epsilon=epsilon_start,
        lr=0.1,
        gamma=0.95
    )

    # Load existing model if provided
    if load_path and Path(load_path).exists():
        agent.load_q_table(load_path)
        print(f"Loaded existing model from {load_path}")

    print("🎖️  Starting Military RL Agent Training")
    print(f"Training for {episodes} episodes...")
    print(f"Max ticks per episode: {max_ticks_per_episode}")
    print(f"Decision interval: {intervention_interval}")
    print("-" * 60)

    training_stats = {
        "episodes": [],
        "total_rewards": [],
        "avg_rewards": [],
        "successful_combats": [],
        "combats_initiated": []
    }

    start_time = time.time()

    for episode in range(episodes):
        # Decay epsilon
        agent.epsilon = max(epsilon_min, agent.epsilon * epsilon_decay)

        # Run episode
        episode_stats = run_military_training_episode(
            agent, max_ticks_per_episode, intervention_interval
        )

        # Store statistics
        training_stats["episodes"].append(episode + 1)
        training_stats["total_rewards"].append(episode_stats["total_reward"])
        training_stats["avg_rewards"].append(episode_stats["total_reward"] / episode_stats["actions_taken"] if episode_stats["actions_taken"] > 0 else 0)
        training_stats["successful_combats"].append(episode_stats["successful_combats"])
        training_stats["combats_initiated"].append(episode_stats["combats_initiated"])

        # Log progress
        if (episode + 1) % log_interval == 0:
            avg_reward = sum(training_stats["total_rewards"][-log_interval:]) / log_interval
            success_rate = sum(training_stats["successful_combats"][-log_interval:]) / max(1, sum(training_stats["combats_initiated"][-log_interval:]))
            elapsed = time.time() - start_time

            print(f"Episode {episode + 1:2d} | "
                  f"Avg Reward: {avg_reward:4.1f} | "
                  f"Combat Success: {success_rate:.1%} | "
                  f"Time: {elapsed:.2f}s")

    # Save trained model
    agent.save_q_table(save_path)
    print(f"\n💾 Saved trained model to {save_path}")

    # Final statistics
    total_episodes = len(training_stats["episodes"])
    avg_final_reward = sum(training_stats["total_rewards"][-10:]) / 10 if total_episodes >= 10 else sum(training_stats["total_rewards"]) / total_episodes
    total_combats = sum(training_stats["combats_initiated"])
    successful_combats = sum(training_stats["successful_combats"])
    success_rate = successful_combats / max(1, total_combats)

    print("\n🏆 Training Complete!")
    print(f"Total Episodes: {total_episodes}")
    print(f"Average Final Reward: {avg_final_reward:.1f}")
    print(f"Combat Success Rate: {success_rate:.1%}")
    print(f"Total Training Time: {time.time() - start_time:.1f}s")
    print(f"Final Epsilon: {agent.epsilon:.3f}")

    return agent


def main():
    parser = argparse.ArgumentParser(description="Train Military RL Agent")
    parser.add_argument("--episodes", type=int, default=100, help="Number of training episodes")
    parser.add_argument("--max-ticks", type=int, default=500, help="Max ticks per episode (reduced)")
    parser.add_argument("--intervention-interval", type=int, default=25, help="Decision frequency (increased)")
    parser.add_argument("--epsilon-start", type=float, default=0.9, help="Initial exploration rate (very high)")
    parser.add_argument("--epsilon-min", type=float, default=0.2, help="Minimum exploration rate")
    parser.add_argument("--epsilon-decay", type=float, default=0.998, help="Epsilon decay rate (very slow)")
    parser.add_argument("--save-path", type=str, default="artifacts/models/military_qtable_fast.json", help="Path to save model")
    parser.add_argument("--load-path", type=str, default=None, help="Path to load existing model")
    parser.add_argument("--log-interval", type=int, default=5, help="Logging interval (more frequent)")

    args = parser.parse_args()

    # Ensure artifacts directory exists
    Path("artifacts/models").mkdir(parents=True, exist_ok=True)

    # Train the agent
    trained_agent = train_military_agent(
        episodes=args.episodes,
        max_ticks_per_episode=args.max_ticks,
        intervention_interval=args.intervention_interval,
        epsilon_start=args.epsilon_start,
        epsilon_min=args.epsilon_min,
        epsilon_decay=args.epsilon_decay,
        save_path=args.save_path,
        load_path=args.load_path,
        log_interval=args.log_interval
    )

    print("\n🎖️  Military RL Agent training completed!")
    print(f"Model saved to: {args.save_path}")
    print(f"Agent has learned {len(trained_agent.q_table)} state-action pairs")


if __name__ == "__main__":
    main()