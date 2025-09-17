#!/usr/bin/env python3
"""Analyze dimension coverage from unique states to optimize feature diversity."""

import json
import os
from collections import Counter

def analyze_dimension_coverage():
    """Analyze the distribution of values in each state dimension."""

    states_file = "artifacts/checkpoints/military_unique_states.json"

    if not os.path.exists(states_file):
        print("No unique states file found")
        return

    with open(states_file, "r") as f:
        data = json.load(f)

    states = data["states"]
    print(f"Analyzing {len(states)} unique states")

    # State dimension names and max bins
    dim_names = [
        "power_ratio",
        "tech_advantage",
        "diplomatic_status",
        "resource_availability",
        "force_readiness",
        "territory_control"
    ]

    max_bins = [15, 12, 8, 8, 7, 8]

    # Extract dimensions
    dimensions = list(zip(*states))

    print("\n" + "="*80)
    print("DIMENSION COVERAGE ANALYSIS")
    print("="*80)

    for i, (name, max_bin, values) in enumerate(zip(dim_names, max_bins, dimensions)):
        counter = Counter(values)
        unique_vals = len(counter)
        coverage_pct = (unique_vals / max_bin) * 100

        # Find min/max values
        min_val = min(values)
        max_val = max(values)

        # Most/least common values
        most_common = counter.most_common(3)
        least_common = counter.most_common()[-3:]

        print(f"\n{name.upper()} (Dim {i})")
        print(f"  Max bins: {max_bin}")
        print(f"  Unique values: {unique_vals} ({coverage_pct:.1f}%)")
        print(f"  Value range: {min_val} to {max_val}")
        print(f"  Most common: {most_common}")
        print(f"  Least common: {least_common}")

        # Check for clustering
        if unique_vals < max_bin * 0.5:
            print(f"  ⚠️  LOW COVERAGE - Only {unique_vals}/{max_bin} bins used")

        # Check for extreme clustering
        if most_common[0][1] > len(values) * 0.3:
            print(f"  ⚠️  HIGH CLUSTERING - {most_common[0][0]} appears {most_common[0][1]} times ({most_common[0][1]/len(values)*100:.1f}%)")

    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)

    # Analyze patterns and suggest improvements
    resource_dim = dimensions[3]
    readiness_dim = dimensions[4]
    territory_dim = dimensions[5]

    if len(set(resource_dim)) < 5:
        print("• RESOURCE_AVAILABILITY: Low diversity - consider increasing resource variance in tribe creation")
        print("  Current: mostly value 7 - tribes may have similar resource levels")

    if len(set(readiness_dim)) < 4:
        print("• FORCE_READINESS: Low diversity - force readiness calculation may be too static")
        print("  Current: mostly value 3 - check technology and population impact on readiness")

    if len(set(territory_dim)) < 5:
        print("• TERRITORY_CONTROL: Low diversity - territory assignment may be too uniform")
        print("  Current: values 0-4 - consider more varied territory sizes")

    # Check for correlations
    power_dim = dimensions[0]
    tech_dim = dimensions[1]

    # Simple correlation check
    power_counter = Counter(power_dim)
    tech_counter = Counter(tech_dim)

    if power_counter[0] > len(power_dim) * 0.2 and tech_counter[0] > len(tech_dim) * 0.2:
        print("• POWER_RATIO & TECH_ADVANTAGE: Both heavily clustered at low values")
        print("  May indicate tribes are too similar in power/tech - increase diversity in creation")

if __name__ == "__main__":
    analyze_dimension_coverage()