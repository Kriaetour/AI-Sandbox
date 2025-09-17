"""
RL Analytics Plotting Script for AI Sandbox

Plots all key metrics from analytics_summary.json:
- Population history
- Reward curve
- Action counts (bar chart)
- Hostility/betrayal event counts
- Allies/hostiles ratio per faction (if available)

Usage:
    python plot_rl_analytics.py --infile analytics_summary.json
"""

import argparse
import json
import matplotlib.pyplot as plt


def plot_metrics(data):
    plot_count = 0

    # Population history
    if "population" in data and "history" in data["population"]:
        plt.figure()
        plt.plot(data["population"]["history"])
        plt.title("Population Over Time")
        plt.xlabel("Tick")
        plt.ylabel("Population")
        plt.savefig("population_history.png")
        plt.close()
        plot_count += 1

    # Reward curve
    if "reward_curve" in data:
        plt.figure()
        plt.plot(data["reward_curve"])
        plt.title("Reward Curve")
        plt.xlabel("Tick")
        plt.ylabel("Reward")
        plt.savefig("reward_curve.png")
        plt.close()
        plot_count += 1

    # Action counts
    if "action_counts" in data:
        plt.figure()
        actions = list(data["action_counts"].keys())
        counts = [data["action_counts"][a] for a in actions]
        plt.bar(actions, counts)
        plt.title("RL Action Counts")
        plt.xlabel("Action")
        plt.ylabel("Count")
        plt.xticks(rotation=45)
        plt.savefig("action_counts.png")
        plt.close()
        plot_count += 1

    # Hostility/betrayal event counts
    if "hostility_events" in data or "betrayal_events" in data:
        plt.figure()
        labels = []
        values = []
        if "hostility_events" in data:
            labels.append("Hostility Events")
            values.append(len(data["hostility_events"]))
        if "betrayal_events" in data:
            labels.append("Betrayal Events")
            values.append(len(data["betrayal_events"]))
        if labels:
            plt.bar(labels, values)
            plt.title("Hostility and Betrayal Events")
            plt.ylabel("Count")
            plt.savefig("hostility_betrayal_events.png")
            plt.close()
            plot_count += 1

    # Allies/hostiles ratio per faction
    if "allies_hostiles" in data and data["allies_hostiles"]:
        plt.figure()
        factions = list(data["allies_hostiles"].keys())
        ratios = [data["allies_hostiles"][f]["ratio"] for f in factions]
        plt.bar(factions, ratios)
        plt.title("Allies/Hostiles Ratio per Faction")
        plt.xlabel("Faction")
        plt.ylabel("Allies/Hostiles Ratio")
        plt.xticks(rotation=45)
        plt.savefig("allies_hostiles_ratio.png")
        plt.close()
        plot_count += 1

    print(f"Generated {plot_count} plot files")
    # plt.show()  # Commented out for headless operation


def main():
    parser = argparse.ArgumentParser(description="Plot RL analytics from summary JSON.")
    parser.add_argument("--infile", type=str, default="analytics_summary.json")
    args = parser.parse_args()
    with open(args.infile, "r") as f:
        data = json.load(f)
    plot_metrics(data)


if __name__ == "__main__":
    main()
