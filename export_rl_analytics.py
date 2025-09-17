"""
RL Analytics Export Script for AI Sandbox

Exports and summarizes:
- Average and variance of population over time
- Ratio of allies to hostiles per faction
- Frequency/context of betrayal/hostility events in logs
- Reward curves and RL action logs

Usage:
    python export_rl_analytics.py --logfile rl_actions.log --rewardfile rewards.csv --outfile analytics_summary.json
"""

import argparse
import re
import json
import numpy as np
from collections import defaultdict

# Helper to parse RL action log lines
RL_ACTION_RE = re.compile(r"RL_ACTION: (\w+).*source=(\w+).*target=(\w+|None).*result=(True|False)")

# Helper to parse reward log lines (if available)
REWARD_RE = re.compile(r"RL_REWARD: ([\d\.-]+)")


def parse_population_history(rewardfile):
    pops = []
    rewards = []
    try:
        with open(rewardfile, "r") as f:
            lines = f.readlines()
            for line in lines[1:]:  # Skip header line
                line = line.strip()
                if line and "," in line:
                    parts = line.split(",")
                    if len(parts) >= 3:
                        try:
                            pop = int(parts[1])
                            reward = float(parts[2])
                            pops.append(pop)
                            rewards.append(reward)
                        except (ValueError, IndexError):
                            continue
    except Exception:
        pass
    return pops, rewards


def parse_rl_actions(logfile):
    action_counts = defaultdict(int)
    hostilities = []
    betrayals = []
    context_events = []
    try:
        with open(logfile, "r") as f:
            for line in f:
                m = RL_ACTION_RE.search(line)
                if m:
                    action, source, target, result = m.groups()
                    action_counts[action] += 1
                    if action in ("insult", "suppress_rumor", "spread_rumor"):
                        hostilities.append((source, target, action))
                        context_events.append(
                            {
                                "type": "hostility",
                                "source": source,
                                "target": target,
                                "action": action,
                                "line": line.strip(),
                            }
                        )
                    if action == "betrayal":
                        betrayals.append((source, target))
                        context_events.append(
                            {
                                "type": "betrayal",
                                "source": source,
                                "target": target,
                                "line": line.strip(),
                            }
                        )
    except Exception:
        pass
    return action_counts, hostilities, betrayals, context_events


def summarize_allies_hostiles(world_state_file):
    # Expects a JSON dump of opinion stats per tick: {tick: {faction: {allies: int, hostiles: int}}}
    try:
        with open(world_state_file, "r") as f:
            data = json.load(f)
        ratios = {}
        for tick, stats in data.items():
            for fac, s in stats.items():
                a = s.get("allies", 0)
                h = s.get("hostiles", 0)
                ratios.setdefault(fac, []).append((a, h))
        summary = {
            fac: {
                "avg_allies": float(np.mean([x[0] for x in vals])),
                "avg_hostiles": float(np.mean([x[1] for x in vals])),
                "ratio": float(np.mean([(x[0] + 1) / (x[1] + 1) for x in vals])),
            }
            for fac, vals in ratios.items()
        }
        return summary
    except Exception:
        return {}


def main():
    parser = argparse.ArgumentParser(description="Export RL analytics from logs and reward files.")
    parser.add_argument("--logfile", type=str, default="rl_actions.log")
    parser.add_argument("--rewardfile", type=str, default="rewards.csv")
    parser.add_argument(
        "--worldstate",
        type=str,
        default=None,
        help="Optional: JSON dump of opinion stats per tick",
    )
    parser.add_argument("--outfile", type=str, default="analytics_summary.json")
    args = parser.parse_args()

    pops, rewards = parse_population_history(args.rewardfile)
    action_counts, hostilities, betrayals, context_events = parse_rl_actions(args.logfile)
    allies_hostiles = summarize_allies_hostiles(args.worldstate) if args.worldstate else {}

    summary = {
        "population": {
            "average": float(np.mean(pops)) if pops else None,
            "variance": float(np.var(pops)) if pops else None,
            "history": pops[:1000],  # truncate for preview
        },
        "reward_curve": rewards,
        "action_counts": dict(action_counts),
        "hostility_events": hostilities,
        "betrayal_events": betrayals,
        "context_events": context_events[:100],
        "allies_hostiles": allies_hostiles,
    }
    with open(args.outfile, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Analytics summary written to {args.outfile}")


if __name__ == "__main__":
    main()
