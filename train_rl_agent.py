"""
RL Training Script for AI Sandbox

This script demonstrates how to train a Q-learning agent using the RL API in the AI Sandbox environment.
"""

import argparse
from rl_agent import run_rl_training
from gemini_narrative import generate_rl_training_narrative


def main():
    parser = argparse.ArgumentParser(description="Train RL agent in AI Sandbox.")
    parser.add_argument(
        "--episodes", type=int, default=50, help="Number of training episodes per batch"
    )
    parser.add_argument("--max_ticks", type=int, default=2000, help="Max ticks per episode")
    parser.add_argument("--epsilon_start", type=float, default=0.3, help="Initial exploration rate")
    parser.add_argument("--epsilon_min", type=float, default=0.05, help="Minimum exploration rate")
    parser.add_argument(
        "--epsilon_decay", type=float, default=0.92, help="Epsilon decay per episode"
    )
    parser.add_argument(
        "--save_path",
        type=str,
        default="artifacts/models/qtable.json",
        help="Path to save Q-table",
    )
    parser.add_argument("--load_path", type=str, default=None, help="Path to load Q-table")
    parser.add_argument("--init_pop_min", type=int, default=300, help="Initial min population")
    parser.add_argument("--init_pop_max", type=int, default=370, help="Initial max population")
    parser.add_argument("--lr", type=float, default=0.1, help="Q-learning learning rate")
    parser.add_argument("--gamma", type=float, default=0.95, help="Discount factor")
    parser.add_argument(
        "--pop_bin_size",
        type=int,
        default=10,
        help="Population bin size for discretization",
    )
    parser.add_argument(
        "--food_bin_size",
        type=int,
        default=500,
        help="Food bin size for discretization",
    )
    parser.add_argument(
        "--births_cap",
        type=int,
        default=5,
        help="Cap births count in state to this max",
    )
    parser.add_argument(
        "--starv_cap",
        type=int,
        default=5,
        help="Cap starvation deaths in state to this max",
    )
    parser.add_argument(
        "--intervention_interval",
        type=int,
        default=20,
        help="How often (in ticks) the RL agent makes decisions",
    )
    parser.add_argument(
        "--preset",
        type=str,
        choices=["explore", "balanced", "exploit"],
        default=None,
        help="Quick presets for epsilon/bin sizes and learning hyperparams",
    )
    parser.add_argument(
        "--max_batches",
        type=int,
        default=1000,
        help="Maximum training batches to run per population range",
    )
    parser.add_argument(
        "--ranges",
        type=str,
        default=None,
        help="Comma-separated population ranges like 50-100,300-500,1000-1800",
    )
    parser.add_argument(
        "--enable_llm",
        action="store_true",
        help="Enable LLM-generated reward explanations (does not affect RL decision-making)",
    )
    parser.add_argument(
        "--llm_frequency",
        type=int,
        default=5,
        help="Generate LLM narratives every N batches (0=disabled)",
    )
    parser.add_argument(
        "--llm_reward_freq",
        type=int,
        default=100,
        help="Generate LLM reward explanations every N ticks (0=disabled, explanations only)",
    )
    parser.add_argument(
        "--max_llm_calls",
        type=int,
        default=100,
        help="Maximum LLM API calls per training session",
    )
    parser.add_argument(
        "--llm_batch_only",
        action="store_true",
        help="Only generate LLM narratives at batch end, not during episodes",
    )
    parser.add_argument(
        "--log_level",
        type=str,
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level for training (default: WARNING to reduce log file size)",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="Number of parallel processes for training (default: 1 for sequential)",
    )
    args = parser.parse_args()

    # List of (init_pop_min, init_pop_max) pairs to try - actual ranges for random search
    pop_ranges = [
        (50, 100),  # Small population range
        (100, 300),  # Medium-small population range
        (300, 500),  # Medium population range
        (500, 1000),  # Medium-large population range
        (1000, 1800),  # Large population range
    ]
    # Optional override from CLI like: --ranges 300-300,1000-1000
    if hasattr(args, "ranges") and args.ranges:
        try:
            parsed = []
            for rng in args.ranges.split(","):
                a, b = rng.split("-")
                parsed.append((int(a), int(b)))
            if parsed:
                pop_ranges = parsed
        except Exception:
            print("[WARN] Failed to parse --ranges; using defaults.")

    pop_eq_summary = []

    # Set logging level to reduce log file size during training
    import os

    os.environ["SANDBOX_LOG_LEVEL"] = args.log_level
    print(f"Set logging level to {args.log_level} to control log file size")

    # Initialize analytics collection
    import csv

    rewards_csv_path = "rewards.csv"
    rl_actions_log_path = "rl_actions.log"

    # Clear previous analytics files
    try:
        with open(rewards_csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["tick", "population", "reward"])
        with open(rl_actions_log_path, "w") as f:
            f.write("# RL Action Log\n")
    except Exception as e:
        print(f"Warning: Could not initialize analytics files: {e}")

    for pop_min, pop_max in pop_ranges:
        print(f"\n=== Training with initial population range {pop_min}-{pop_max} ===")
        qtable_path = f"artifacts/models/qtable_pop_{pop_min}_{pop_max}.json"
        plateau_window = 5
        min_improvement = 0.01
        batch_size = args.episodes
        max_batches = args.max_batches
        reward_history = []
        length_history = []
        pop_history = []  # Track average population per episode
        prev_avg_reward = None
        prev_avg_length = None
        plateau_count = 0
        total_episodes = 0
        load_path = None

        # Adaptive bin sizes based on population range for better stability
        pop_center = (pop_min + pop_max) / 2

        # Adaptive population bin size: smaller for low populations, larger for high
        if pop_center < 100:
            adaptive_pop_bin = max(1, pop_center // 10)  # Very fine for small pops
        elif pop_center < 500:
            adaptive_pop_bin = max(5, pop_center // 20)  # Medium for normal ranges
        else:
            adaptive_pop_bin = max(10, pop_center // 50)  # Coarser for large pops

        # Adaptive food bin size scales with population
        adaptive_food_bin = max(50, int(pop_center * 2))  # Food scales roughly with population

        # Adaptive births/starvation caps
        adaptive_births_cap = max(3, min(10, pop_center // 50))  # Scale with population
        adaptive_starv_cap = max(3, min(10, pop_center // 50))

        # Override defaults with adaptive values unless explicitly set via presets
        if not args.preset:
            args.pop_bin_size = adaptive_pop_bin
            args.food_bin_size = adaptive_food_bin
            args.births_cap = adaptive_births_cap
            args.starv_cap = adaptive_starv_cap

        # Adaptive episode length based on population size
        # Smaller populations stabilize faster, larger ones need more time
        if pop_center < 100:
            adaptive_max_ticks = 500  # Small populations stabilize quickly
        elif pop_center < 500:
            adaptive_max_ticks = 1000  # Medium populations need moderate time
        else:
            adaptive_max_ticks = max(2000, int(pop_center * 2))  # Large populations need more time

        # Use adaptive max_ticks unless overridden by preset
        if not args.preset:
            args.max_ticks = adaptive_max_ticks

        print(
            f"Adaptive parameters for {pop_min}-{pop_max}: pop_bin={args.pop_bin_size}, food_bin={args.food_bin_size}, births_cap={args.births_cap}, starv_cap={args.starv_cap}, max_ticks={args.max_ticks}"
        )

        # Apply preset overrides if requested (these override adaptive settings)
        if args.preset:
            if args.preset == "explore":
                args.epsilon_start = 0.5
                args.epsilon_min = 0.1
                args.epsilon_decay = 0.97
                args.lr = 0.2
                args.gamma = 0.90
                args.pop_bin_size = 20
                args.food_bin_size = 1000
                args.births_cap = 4
                args.starv_cap = 4
            elif args.preset == "balanced":
                args.epsilon_start = 0.3
                args.epsilon_min = 0.08
                args.epsilon_decay = 0.94
                args.lr = 0.12
                args.gamma = 0.94
                args.pop_bin_size = 10
                args.food_bin_size = 500
                args.births_cap = 5
                args.starv_cap = 5
            elif args.preset == "exploit":
                args.epsilon_start = 0.15
                args.epsilon_min = 0.05
                args.epsilon_decay = 0.98
                args.lr = 0.08
                args.gamma = 0.98
                args.pop_bin_size = 5
                args.food_bin_size = 250
                args.births_cap = 6
                args.starv_cap = 6

        llm_call_count = 0  # Track total LLM API calls

        for batch in range(max_batches):
            result = run_rl_training(
                episodes=batch_size,
                max_ticks=args.max_ticks,
                epsilon_start=args.epsilon_start,
                epsilon_min=args.epsilon_min,
                epsilon_decay=args.epsilon_decay,
                save_path=qtable_path,
                load_path=load_path,
                init_pop_min=pop_min,
                init_pop_max=pop_max,
                pop_bin_size=args.pop_bin_size,
                food_bin_size=args.food_bin_size,
                births_cap=args.births_cap,
                starv_cap=args.starv_cap,
                lr=args.lr,
                gamma=args.gamma,
                intervention_interval=args.intervention_interval,
                enable_llm=args.enable_llm,
                llm_reward_freq=args.llm_reward_freq,
                max_llm_calls=args.max_llm_calls,
                llm_batch_only=args.llm_batch_only,
                parallel_processes=args.parallel,
            )
            load_path = qtable_path
            reward_history.append(result["avg_reward"])
            length_history.append(result["avg_length"])
            # Compute average population for this batch (if available)
            if "episode_populations" in result:
                pop_history.extend(result["episode_populations"])
            total_episodes += batch_size
            print(
                f"Batch {batch+1}: Avg reward={result['avg_reward']:.2f}, Avg len={result['avg_length']:.1f}, Epsilon={result['final_epsilon']:.3f}, States={result['states']}"
            )

            # Generate LLM training narrative if enabled
            if args.enable_llm and args.llm_frequency > 0 and llm_call_count < args.max_llm_calls:
                if (batch + 1) % args.llm_frequency == 0:
                    episode_summary = {
                        "episode": total_episodes,
                        "avg_reward": result["avg_reward"],
                        "avg_length": result["avg_length"],
                        "final_population": (
                            result["episode_populations"][-1]
                            if result["episode_populations"]
                            else 0
                        ),
                        "total_episodes": total_episodes,
                    }
                    training_context = f"Population range {pop_min}-{pop_max}, batch {batch+1}, epsilon {result['final_epsilon']:.3f}"
                    narrative = generate_rl_training_narrative(episode_summary, training_context)
                    print(f"[LLM-NARRATIVE] {narrative}")
                    print("-" * 80)
                    llm_call_count += 1
                    print(f"[LLM-USAGE] API calls: {llm_call_count}/{args.max_llm_calls}")

            if len(reward_history) >= plateau_window:
                recent_rewards = reward_history[-plateau_window:]
                recent_lengths = length_history[-plateau_window:]
                avg_reward = sum(recent_rewards) / plateau_window
                avg_length = sum(recent_lengths) / plateau_window
                if prev_avg_reward is not None and prev_avg_length is not None:
                    reward_improvement = (avg_reward - prev_avg_reward) / max(
                        abs(prev_avg_reward), 1e-6
                    )
                    length_improvement = (avg_length - prev_avg_length) / max(
                        abs(prev_avg_length), 1e-6
                    )
                    if (
                        abs(reward_improvement) < min_improvement
                        and abs(length_improvement) < min_improvement
                    ):
                        plateau_count += 1
                        print(f"No significant improvement for {plateau_count} batch(es).")
                    else:
                        plateau_count = 0
                prev_avg_reward = avg_reward
                prev_avg_length = avg_length
                if plateau_count >= plateau_window:
                    print("\nPlateau detected. Stopping training for this population range.")
                    break

        # Compute equilibrium population average for this range
        eq_pop = sum(pop_history) / len(pop_history) if pop_history else float("nan")
        pop_eq_summary.append(
            {
                "pop_min": pop_min,
                "pop_max": pop_max,
                "episodes": total_episodes,
                "avg_reward": reward_history[-1] if reward_history else float("nan"),
                "avg_length": length_history[-1] if length_history else float("nan"),
                "equilibrium_population": eq_pop,
            }
        )
        print("\nAutomated training complete for population range.")
        print(f"Total episodes: {total_episodes}")
        print(f"Final average reward: {reward_history[-1]:.2f}")
        print(f"Final average episode length: {length_history[-1]:.1f}")
        print(f"Equilibrium population: {eq_pop:.2f}")
        print(f"Q-table saved to: {qtable_path}")

        if args.enable_llm:
            # Generate and display narrative insights using the LLM
            episode_summary = {
                "episode": total_episodes,
                "avg_reward": reward_history[-1] if reward_history else 0,
                "avg_length": length_history[-1] if length_history else 0,
                "final_population": eq_pop,
                "total_episodes": total_episodes,
            }
            training_context = (
                f"Population range {pop_min}-{pop_max}, final equilibrium population {eq_pop:.1f}"
            )
            narrative = generate_rl_training_narrative(episode_summary, training_context)
            print("\n=== LLM Narrative Insights ===")
            print(narrative)

    # Save summary to file
    import json

    with open("pop_equilibrium_summary.json", "w", encoding="utf-8") as f:
        json.dump(pop_eq_summary, f, indent=2)
    print("\nSaved population equilibrium summary to pop_equilibrium_summary.json")


if __name__ == "__main__":
    main()
