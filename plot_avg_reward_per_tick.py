"""
Plot average reward per tick across episodes from reward_components.csv

Usage:
    python plot_avg_reward_per_tick.py --csv reward_components.csv
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def plot_avg_reward(csvfile):
    df = pd.read_csv(csvfile)
    df["tick"] = pd.to_numeric(df["tick"], errors="coerce")
    df["reward"] = pd.to_numeric(df["reward"], errors="coerce")
    # Drop rows where reward is NaN (e.g., header repeats)
    df = df.dropna(subset=["reward"])
    # Detect episode boundaries: tick resets to 1
    episode_starts = df.index[df["tick"] == 1].tolist()
    episode_starts.append(len(df))  # add end for last episode

    # Find the maximum episode length
    max_len = 0
    episodes = []
    for i in range(len(episode_starts) - 1):
        ep = df.iloc[episode_starts[i] : episode_starts[i + 1]]
        rewards = ep["reward"].values
        episodes.append(rewards)
        if len(rewards) > max_len:
            max_len = len(rewards)

    # Ignore incomplete episodes (shorter than max_len)
    complete_episodes = [rewards for rewards in episodes if len(rewards) == max_len]
    if not complete_episodes:
        print("No complete episodes found. Plotting all episodes. (Interrupted run?)")
        complete_episodes = episodes
    reward_matrix = []
    for rewards in complete_episodes:
        reward_matrix.append(rewards)
    reward_matrix = np.vstack(reward_matrix)
    avg_reward = np.nanmean(reward_matrix, axis=0)

    plt.figure(figsize=(10, 5))
    plt.plot(np.arange(1, max_len + 1), avg_reward, label="Average Reward")
    plt.title("Average Reward per Tick Across Episodes")
    plt.xlabel("Tick")
    plt.ylabel("Average Reward")
    plt.legend()
    plt.tight_layout()
    plt.savefig("avg_reward_per_tick.png")
    plt.show()
    print("Saved plot as avg_reward_per_tick.png")


def main():
    parser = argparse.ArgumentParser(description="Plot average reward per tick across episodes.")
    parser.add_argument("--csv", type=str, default="reward_components.csv")
    args = parser.parse_args()
    plot_avg_reward(args.csv)


if __name__ == "__main__":
    main()
