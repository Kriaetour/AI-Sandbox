#!/usr/bin/env python3
"""
Simple Batch Training: Multiple episodes with shared learning for Military RL Agent.
"""

import time
import random

from world.engine import WorldEngine
from tribes.tribal_manager import TribalManager
from rl_military_agent import MilitaryRLAgent
from rl_military_interface import (
    execute_military_action,
    compute_military_reward
)


def create_batch_scenario(seed_offset=0):
    """Create scenario for batch training."""
    world_seed = random.randint(0, 100000) + seed_offset * 1000
    world = WorldEngine(seed=world_seed, disable_faction_saving=True)
    tribal_manager = TribalManager()
    world._tribal_manager = tribal_manager

    # Create tribes
    num_tribes = random.randint(4, 7)
    tribes_created = []

    for i in range(num_tribes):
        tribe_name = f"BatchTribe_{i+1}"
        founder_id = f"founder_{tribe_name.lower()}"
        location = (random.randint(-25, 25), random.randint(-25, 25))
        population = random.randint(50, 150)
        resources = {
            "food": random.randint(100, 300),
            "wood": random.randint(50, 200),
            "ore": random.randint(25, 100)
        }

        # Create tribe
        tribal_manager.create_tribe(tribe_name, founder_id, location)

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


def run_batch_episodes(num_episodes=20, episodes_per_batch=5):
    """Run episodes in batches with shared learning."""
    print("🔄 Starting Batch Training")
    print(f"Total Episodes: {num_episodes} | Batch Size: {episodes_per_batch}")
    print("=" * 60)

    start_time = time.time()

    # Master agent that accumulates learning across batches
    master_agent = MilitaryRLAgent(epsilon=0.95, lr=0.2, gamma=0.9)

    total_combats = 0
    total_successful = 0
    total_reward = 0

    num_batches = (num_episodes + episodes_per_batch - 1) // episodes_per_batch

    for batch in range(num_batches):
        print(f"\n📦 Batch {batch + 1}/{num_batches}")

        batch_start_time = time.time()
        batch_combats = 0
        batch_successful = 0
        batch_reward = 0
        batch_states = 0

        # Run episodes in this batch
        episodes_in_batch = min(episodes_per_batch, num_episodes - batch * episodes_per_batch)

        for episode_in_batch in range(episodes_in_batch):
            episode_num = batch * episodes_per_batch + episode_in_batch + 1

            try:
                # Create scenario
                world, tribal_manager, tribes_created = create_batch_scenario(episode_num)

                # Run episode
                episode_combats = 0
                episode_successful = 0
                episode_reward = 0
                episode_states = 0

                # Run for 80 ticks with decisions every 10 ticks
                for tick in range(0, 80, 10):
                    world.world_tick()

                    active_tribes = list(tribal_manager.tribes.values())
                    if len(active_tribes) < 2:
                        continue

                    # Select random tribe for military action
                    actor_tribe = random.choice(active_tribes)
                    target_tribes = [t for t in active_tribes if t != actor_tribe]

                    if not target_tribes:
                        continue

                    target_tribe = random.choice(target_tribes)

                    # Get military state (discretized)
                    state = master_agent.get_military_state(actor_tribe, [target_tribe])

                    # Agent chooses action
                    action_idx = master_agent.choose_action(state)
                    action_name = master_agent.get_action_name(action_idx)

                    # Execute action
                    action_results = execute_military_action(action_name, actor_tribe, [target_tribe], tribal_manager, world)

                    # Get next state (discretized)
                    next_state = master_agent.get_military_state(actor_tribe, [target_tribe])

                    # Get reward
                    reward = compute_military_reward(action_results, state, next_state)
                    episode_reward += reward

                    if next_state is not None:
                        master_agent.update_q_table(state, action_idx, reward, next_state)
                        episode_states += 1

                # Update batch stats
                batch_combats += episode_combats
                batch_successful += episode_successful
                batch_reward += episode_reward
                batch_states += episode_states

                print(f"  Episode {episode_num:2d} | States: {episode_states:2d} | "
                      f"Combats: {episode_combats:2d} | Success: {episode_successful/max(episode_combats,1):.1%} | "
                      f"Reward: {episode_reward:6.1f}")

            except Exception as e:
                print(f"  Episode {episode_num:2d} | ERROR: {e}")

        # Batch summary
        batch_time = time.time() - batch_start_time
        batch_success_rate = batch_successful / max(batch_combats, 1)
        print(f"  Batch Complete | Combats: {batch_combats} | Success: {batch_success_rate:.1%} | "
              f"States: {batch_states} | Time: {batch_time:.1f}s")

        # Update totals
        total_combats += batch_combats
        total_successful += batch_successful
        total_reward += batch_reward

        # Save checkpoint every 5 batches
        if (batch + 1) % 5 == 0:
            checkpoint_path = f"artifacts/models/military_qtable_batch_checkpoint_{batch + 1}.json"
            master_agent.save_q_table(checkpoint_path)
            print(f"  💾 Checkpoint saved: {checkpoint_path}")

    # Final save
    final_path = "artifacts/models/military_qtable_batch_final.json"
    master_agent.save_q_table(final_path)

    elapsed = time.time() - start_time
    overall_success = total_successful / max(total_combats, 1)

    print("\n🎯 Batch Training Complete!")
    print(f"Total Episodes: {num_episodes}")
    print(f"Total Combats: {total_combats}")
    print(f"Overall Success Rate: {overall_success:.1%}")
    print(f"Total Reward: {total_reward:.1f}")
    print(f"States Learned: {len(master_agent.q_table)}")
    print(f"Training Time: {elapsed:.1f}s")
    print(f"Model saved to: {final_path}")

    # Show top actions
    if master_agent.q_table:
        print("\n📊 Top Learned Actions:")
        q_values = list(master_agent.q_table.values())[0]
        actions = ['aggressive_attack', 'defensive_posture', 'strategic_retreat',
                  'force_reinforcement', 'tech_investment', 'diplomatic_pressure',
                  'siege_preparation', 'peaceful_approach']

        sorted_actions = sorted(zip(actions, q_values), key=lambda x: x[1], reverse=True)
        for i, (action, q_val) in enumerate(sorted_actions[:3]):
            print(f"  {i+1}. {action}: {q_val:.1f}")


def main():
    """Main function."""
    print("🎖️  Military RL Agent - Batch Training")
    print("=" * 60)

    try:
        num_episodes = int(input("Number of episodes (default 20): ") or "20")
        episodes_per_batch = int(input("Episodes per batch (default 5): ") or "5")

        run_batch_episodes(num_episodes, episodes_per_batch)

    except KeyboardInterrupt:
        print("\n⏹️  Training interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()