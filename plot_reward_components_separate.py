"""
Plot each reward component as a separate graph from reward_components.csv

Usage:
    python plot_reward_components_separate.py --csv reward_components.csv
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import os


def plot_components_separate(csvfile):
    df = pd.read_csv(csvfile)
    outdir = "reward_component_plots"
    os.makedirs(outdir, exist_ok=True)
    for col in df.columns:
        if col != "tick":
            plt.figure(figsize=(10, 5))
            plt.plot(df["tick"], df[col], label=col)
            plt.title(f"{col.capitalize()} Over Time")
            plt.xlabel("Tick")
            plt.ylabel(col.capitalize())
            plt.legend()
            plt.tight_layout()
            fname = os.path.join(outdir, f"{col}_over_time.png")
            plt.savefig(fname)
            plt.close()
            print(f"Saved {fname}")


def main():
    parser = argparse.ArgumentParser(description="Plot each reward component as a separate graph.")
    parser.add_argument("--csv", type=str, default="reward_components.csv")
    args = parser.parse_args()
    plot_components_separate(args.csv)


if __name__ == "__main__":
    main()
