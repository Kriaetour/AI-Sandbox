import importlib
import sys
from markov_dialogue import (
    generate_markov_dialogue,
    flush_dialogue_state,
    get_diversity_stats_snapshot,
)

# Generate a batch of lines to build stats
contexts = ["idle", "trade", "encounter"]
for ctx in contexts:
    for _ in range(25):
        generate_markov_dialogue(ctx)

pre_snapshot = get_diversity_stats_snapshot()
print("Pre-save line counts per context:")
for ctx, stats in pre_snapshot["freq_stats"].items():
    print(f"  {ctx}: {sum(stats.values())} lines (unique {len(stats)})")

# Flush to persist
flush_dialogue_state()

# Force module reload (simulating new process) by deleting from sys.modules

if "markov_dialogue" in sys.modules:
    del sys.modules["markov_dialogue"]

md = importlib.import_module("markov_dialogue")
post_snapshot = md.get_diversity_stats_snapshot()
print("\nPost-reload line counts per context:")
for ctx, stats in post_snapshot["freq_stats"].items():
    print(f"  {ctx}: {sum(stats.values())} lines (unique {len(stats)})")

# Simple check
print("\nVerification:")
for ctx in contexts:
    pre_total = sum(pre_snapshot["freq_stats"].get(ctx, {}).values())
    post_total = sum(post_snapshot["freq_stats"].get(ctx, {}).values())
    status = "OK" if pre_total == post_total and pre_total > 0 else "MISMATCH"
    print(f"  {ctx}: pre={pre_total} post={post_total} -> {status}")
