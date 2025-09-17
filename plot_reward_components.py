"""
Plot reward components from reward_components.csv

Usage:
    python plot_reward_components.py --csv reward_components.csv
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt


def plot_components(csvfile):
    df = pd.read_csv(csvfile)
    plt.figure(figsize=(14, 8))
    for col in df.columns:
        if col != "tick":
            plt.plot(df["tick"], df[col], label=col)
    plt.title("RL Reward Components Over Time")
    plt.xlabel("Tick")
    plt.ylabel("Value")
    plt.legend()
    plt.tight_layout()
    plt.savefig("reward_components.png")
    plt.show()
    print("Saved plot as reward_components.png")


def main():
    parser = argparse.ArgumentParser(description="Plot reward components from CSV.")
    parser.add_argument("--csv", type=str, default="reward_components.csv")
    args = parser.parse_args()
    plot_components(args.csv)


if __name__ == "__main__":
    main()
