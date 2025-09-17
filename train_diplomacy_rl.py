#!/usr/bin/env python3
"""
Train RL Diplomacy Agent: Train an agent to learn optimal tribal diplomacy strategies.
"""
import argparse
import random
import time
import json
from pathlib import Path
from typing import Dict

from world.engine import WorldEngine
from tribes.tribal_manager import TribalManager
from rl_diplomacy_agent import DiplomacyRLAgent
from rl_diplomacy_interface import get_diplomacy_state_vector, compute_diplomacy_reward


def run_diplomacy_training_episode(
    agent: DiplomacyRLAgent, max_ticks: int = 1000, intervention_interval: int = 50
) -> Dict:
    """Run a single training episode for diplomacy RL."""
    # Set fast mode for training
    import os

    os.environ["SANDBOX_WORLD_FAST"] = "1"

    # Initialize world with tribal system
    world = WorldEngine(seed=random.randint(0, 10000), disable_faction_saving=True)
    tribal_manager = TribalManager()
    world._tribal_manager = tribal_manager  # Attach tribal manager to world

    # Create some initial tribes
    num_tribes = random.randint(3, 5)
    tribes_created = []

    for i in range(num_tribes):
        location = (random.randint(-10, 10), random.randint(-10, 10))
        tribe_name = f"Tribe{i+1}"

        # Create tribe
        tribal_manager.create_tribe(tribe_name, f"founder_{tribe_name.lower()}", location)

        # Create corresponding faction
        if tribe_name not in world.factions:
            world.factions[tribe_name] = type(
                "Faction",
                (),
                {
                    "name": tribe_name,
                    "territory": [location],
                    "members": [],
                    "resources": {"food": 100, "ore": 50, "wood": 50},
                    "memory": {},
                },
            )()

        tribes_created.append(tribe_name)

    print(f"[DIPLOMACY] Created {len(tribes_created)} tribes: {tribes_created}")

    # Initialize diplomacy matrix
    for tribe_a in tribes_created:
        for tribe_b in tribes_created:
            if tribe_a != tribe_b:
                # Start with neutral diplomacy
                tribal_manager.tribal_diplomacy.set_trust_level(tribe_a, tribe_b, 0.0)

    episode_reward = 0.0
    actions_taken = 0
    successful_actions = 0

    prev_state = get_diplomacy_state_vector(world)
    prev_reward = compute_diplomacy_reward(world)

    # Run simulation with RL interventions
    for tick in range(max_ticks):
        # World tick - run actual simulation
        world.world_tick()

        # RL intervention
        if tick % intervention_interval == 0:
            # Select and execute action
            action_idx = agent.select_action(prev_state)

            # Execute diplomatic action
            success = agent.execute_action(world, action_idx)
            actions_taken += 1
            if success:
                successful_actions += 1

            # Get new state and reward
            new_state = get_diplomacy_state_vector(world)
            new_reward = compute_diplomacy_reward(world)

            # Compute reward delta (improvement in diplomacy)
            reward_delta = new_reward - prev_reward

            # Update agent
            agent.update_q_table(prev_state, action_idx, reward_delta, new_state)

            # Accumulate episode reward
            episode_reward += reward_delta

            # Update for next iteration
            prev_state = new_state
            prev_reward = new_reward

            if tick % 200 == 0:
                print(
                    f"[DIPLOMACY] Tick {tick}: Action {agent.action_names[action_idx]}, "
                    f"Reward {reward_delta:.2f}, Success {success}"
                )

    # Final statistics
    final_reward = compute_diplomacy_reward(world)
    diplomacy_stats = {}
    for tribe_a in tribes_created:
        diplomacy_stats[tribe_a] = {}
        for tribe_b in tribes_created:
            if tribe_a != tribe_b:
                level = tribal_manager.tribal_diplomacy.get_trust_level(tribe_a, tribe_b)
                diplomacy_stats[tribe_a][tribe_b] = level

    return {
        "episode_reward": episode_reward,
        "final_diplomacy_reward": final_reward,
        "actions_taken": actions_taken,
        "successful_actions": successful_actions,
        "success_rate": successful_actions / max(actions_taken, 1),
        "tribes": len(tribes_created),
        "diplomacy_matrix": diplomacy_stats,
    }


def main():
    parser = argparse.ArgumentParser(description="Train RL Diplomacy Agent")
    parser.add_argument("--episodes", type=int, default=100, help="Number of training episodes")
    parser.add_argument("--max-ticks", type=int, default=200, help="Ticks per episode")
    parser.add_argument(
        "--intervention-interval", type=int, default=50, help="RL decision interval"
    )
    parser.add_argument("--epsilon-start", type=float, default=1.0, help="Initial exploration rate")
    parser.add_argument("--epsilon-min", type=float, default=0.01, help="Minimum exploration rate")
    parser.add_argument("--epsilon-decay", type=float, default=0.995, help="Exploration decay rate")
    parser.add_argument(
        "--save-q",
        type=str,
        default="artifacts/models/qtable_diplomacy.json",
        help="Save Q-table to file",
    )
    parser.add_argument("--load-q", type=str, help="Load Q-table from file")
    parser.add_argument(
        "--log-interval", type=int, default=10, help="Log progress every N episodes"
    )

    args = parser.parse_args()

    # Initialize agent
    agent = DiplomacyRLAgent(
        num_actions=5,  # 5 diplomacy actions
        epsilon=args.epsilon_start,
        lr=0.1,
        gamma=0.95,
    )

    # Load existing Q-table if specified
    if args.load_q and Path(args.load_q).exists():
        agent.load_q_table(args.load_q)
        print(f"Loaded existing Q-table from {args.load_q}")

    print("=== Training Diplomacy RL Agent ===")
    print(f"Episodes: {args.episodes}")
    print(f"Ticks per episode: {args.max_ticks}")
    print(f"Intervention interval: {args.intervention_interval}")
    print(f"Epsilon: {args.epsilon_start} -> {args.epsilon_min}")
    print()

    # Training loop
    start_time = time.time()
    episode_stats = []

    for episode in range(args.episodes):
        # Decay epsilon
        agent.epsilon = max(args.epsilon_min, agent.epsilon * args.epsilon_decay)

        # Run episode
        stats = run_diplomacy_training_episode(
            agent,
            max_ticks=args.max_ticks,
            intervention_interval=args.intervention_interval,
        )

        episode_stats.append(stats)

        # Logging
        if (episode + 1) % args.log_interval == 0:
            avg_reward = (
                sum(s["episode_reward"] for s in episode_stats[-args.log_interval :])
                / args.log_interval
            )
            avg_success = (
                sum(s["success_rate"] for s in episode_stats[-args.log_interval :])
                / args.log_interval
            )

            elapsed = time.time() - start_time
            eps_per_sec = (episode + 1) / elapsed

            print(
                f"Episode {episode+1:3d}: Avg Reward {avg_reward:6.2f}, "
                f"Success Rate {avg_success:.2%}, Epsilon {agent.epsilon:.3f}, "
                f"EPS {eps_per_sec:.2f}"
            )

    # Final statistics
    total_time = time.time() - start_time
    all_rewards = [s["episode_reward"] for s in episode_stats]
    all_success_rates = [s["success_rate"] for s in episode_stats]

    print("\n=== Training Complete ===")
    print(f"Total time: {total_time:.1f}s")
    print(f"Average episode reward: {sum(all_rewards)/len(all_rewards):.2f}")
    print(f"Average success rate: {sum(all_success_rates)/len(all_success_rates):.2%}")
    print(f"Final epsilon: {agent.epsilon:.3f}")
    print(f"States learned: {len(agent.q_table)}")

    # Save Q-table
    agent.save_q_table(args.save_q)
    print(f"Saved Q-table to {args.save_q}")

    # Save training statistics
    training_stats = {
        "episodes": args.episodes,
        "max_ticks": args.max_ticks,
        "intervention_interval": args.intervention_interval,
        "epsilon_start": args.epsilon_start,
        "epsilon_min": args.epsilon_min,
        "epsilon_decay": args.epsilon_decay,
        "total_time": total_time,
        "avg_reward": sum(all_rewards) / len(all_rewards),
        "avg_success_rate": sum(all_success_rates) / len(all_success_rates),
        "final_epsilon": agent.epsilon,
        "states_learned": len(agent.q_table),
        "episode_stats": episode_stats[-10:],  # Last 10 episodes
    }

    stats_file = args.save_q.replace(".json", "_training_stats.json")
    with open(stats_file, "w") as f:
        json.dump(training_stats, f, indent=2)

    print(f"Saved training statistics to {stats_file}")


if __name__ == "__main__":
    main()
