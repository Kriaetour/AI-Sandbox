"""
RL Analytics Multi-Panel Plotting Script for AI Sandbox

Loads analytics_summary.json and saves all key metrics as a single PNG with subplots.

Usage:
    python plot_rl_analytics_allinone.py --infile analytics_summary.json --outfile analytics_summary.png
"""

import argparse
import json
import matplotlib.pyplot as plt


def plot_all_metrics(data, outfile):
    fig, axs = plt.subplots(3, 2, figsize=(14, 12))
    fig.suptitle("AI Sandbox RL Analytics Summary", fontsize=16)

    # Population history
    if "population" in data and "history" in data["population"]:
        axs[0, 0].plot(data["population"]["history"])
        axs[0, 0].set_title("Population Over Time")
        axs[0, 0].set_xlabel("Tick")
        axs[0, 0].set_ylabel("Population")
    else:
        axs[0, 0].set_visible(False)

    # Reward curve
    if "reward_curve" in data and data["reward_curve"]:
        axs[0, 1].plot(data["reward_curve"])
        axs[0, 1].set_title("Reward Curve")
        axs[0, 1].set_xlabel("Tick")
        axs[0, 1].set_ylabel("Reward")
    else:
        axs[0, 1].set_visible(False)

    # Action counts
    if "action_counts" in data and data["action_counts"]:
        actions = list(data["action_counts"].keys())
        counts = [data["action_counts"][a] for a in actions]
        axs[1, 0].bar(actions, counts)
        axs[1, 0].set_title("RL Action Counts")
        axs[1, 0].set_xlabel("Action")
        axs[1, 0].set_ylabel("Count")
        axs[1, 0].tick_params(axis="x", rotation=45)
    else:
        axs[1, 0].set_visible(False)

    # Hostility/betrayal event counts
    labels = []
    values = []
    if "hostility_events" in data:
        labels.append("Hostility Events")
        values.append(len(data["hostility_events"]))
    if "betrayal_events" in data:
        labels.append("Betrayal Events")
        values.append(len(data["betrayal_events"]))
    if labels:
        axs[1, 1].bar(labels, values)
        axs[1, 1].set_title("Hostility and Betrayal Events")
        axs[1, 1].set_ylabel("Count")
    else:
        axs[1, 1].set_visible(False)

    # Allies/hostiles ratio per faction
    if "allies_hostiles" in data and data["allies_hostiles"]:
        factions = list(data["allies_hostiles"].keys())
        ratios = [data["allies_hostiles"][f]["ratio"] for f in factions]
        axs[2, 0].bar(factions, ratios)
        axs[2, 0].set_title("Allies/Hostiles Ratio per Faction")
        axs[2, 0].set_xlabel("Faction")
        axs[2, 0].set_ylabel("Allies/Hostiles Ratio")
        axs[2, 0].tick_params(axis="x", rotation=45)
    else:
        axs[2, 0].set_visible(False)

    # Hide unused subplot (bottom right)
    axs[2, 1].axis("off")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(outfile)
    print(f"Saved analytics summary plot to {outfile}")


def main():
    parser = argparse.ArgumentParser(description="Plot all RL analytics as a single PNG.")
    parser.add_argument("--infile", type=str, default="analytics_summary.json")
    parser.add_argument("--outfile", type=str, default="analytics_summary.png")
    args = parser.parse_args()
    with open(args.infile, "r") as f:
        data = json.load(f)
    plot_all_metrics(data, args.outfile)


if __name__ == "__main__":
    main()
