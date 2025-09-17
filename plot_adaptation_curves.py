import json
import sys
from pathlib import Path
import argparse
from typing import List, Tuple, Optional, Any
import matplotlib.pyplot as plt

"""Plot adaptation parameter curves over time.

Usage examples:
  python plot_adaptation_curves.py artifacts/data/adaptation_history.json
  python plot_adaptation_curves.py artifacts/data/adaptation_history.json
  --window 5000 --out curves.png
  python plot_adaptation_curves.py --kind-filter reproduction --show

ADAPTIVE R_BASE OVERLAY:
    When the history JSON includes 'adaptive_r_history' and
    'population_history', an extra panel plots the controller intrinsic
    growth rate (r_base) against total population with target band lines.

CLI Options:
  --out PATH          Output image filename (default: adaptation_curves.png)
  --window N          Only include entries with tick >= (max_tick - N)
  --backend NAME      Matplotlib backend to force (default: Agg headless)
  --show              Display window (if backend interactive)
  --kind-filter K     Only plot entries whose 'kind' matches (can repeat)
  --title TEXT        Custom overall figure title
"""


# Force safe backend unless user overrides (before pyplot import)
def _select_backend(backend_arg: Optional[str]) -> None:
    if backend_arg:
        import matplotlib

        matplotlib.use(backend_arg, force=True)
    else:
        # Default to Agg for headless environments
        import matplotlib

        if "agg" not in matplotlib.get_backend().lower():
            try:
                matplotlib.use("Agg", force=True)
            except (ImportError, ValueError, RuntimeError):
                pass


def load_history(path: Path) -> Tuple[List[dict], List[dict], List[dict], List[Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return (
        data.get("entries", []),
        data.get("adaptive_r_history", []),
        data.get("population_history", []),
        data.get("pop_target_band", [None, None]),
    )


def filter_entries(
    entries: List[dict], window: Optional[int], kind_filter: Optional[List[str]]
) -> List[dict]:
    if not entries:
        return entries
    if window:
        max_tick = max(e.get("tick", 0) for e in entries)
        cutoff = max_tick - window
        entries = [e for e in entries if e.get("tick", 0) >= cutoff]
    if kind_filter:
        kinds = set(kind_filter)
        entries = [e for e in entries if e.get("kind") in kinds]
    return entries


def plot(
    entries: List[dict],
    out_path: Path,
    title: Optional[str] = None,
    annotate_last: bool = True,
    show: bool = False,
    adaptive_r: Optional[List[dict]] = None,
    pop_hist: Optional[List[dict]] = None,
    pop_band: Optional[List[Any]] = None,
) -> int:
    if not entries and not adaptive_r:
        print("No adaptation entries to plot.")
        return 1
    ticks = [e["tick"] for e in entries]
    death_rate = [e.get("STARV_DEATH_RATE") for e in entries]
    cap_slope = [e.get("CAP_OVER_PENALTY_SLOPE") for e in entries]
    threshold = [e.get("STARV_THRESHOLD") for e in entries]
    repro_base = [e.get("REPRO_BASE_CHANCE") for e in entries]
    repro_cd = [e.get("REPRO_COOLDOWN") for e in entries]
    kinds = [e.get("kind") for e in entries]

    # If adaptive_r history present, add extra row
    has_adaptive = bool(adaptive_r)
    rows = 4 if has_adaptive else 3
    fig, axes = plt.subplots(rows, 2, figsize=(12, 13 if has_adaptive else 10))
    ax = axes.flat

    ax[0].plot(ticks, death_rate, label="STARV_DEATH_RATE", color="crimson")
    ax[0].set_title("Mortality Rate")

    ax[1].plot(ticks, cap_slope, label="CAP_OVER_PENALTY_SLOPE", color="darkorange")
    ax[1].set_title("Capacity Penalty Slope")

    ax[2].plot(ticks, threshold, label="STARV_THRESHOLD", color="slateblue")
    ax[2].set_title("Starvation Threshold")

    ax[3].plot(ticks, repro_base, label="REPRO_BASE_CHANCE", color="seagreen")
    ax[3].set_title("Reproduction Base Chance")

    ax[4].plot(ticks, repro_cd, label="REPRO_COOLDOWN", color="teal")
    ax[4].invert_yaxis()  # Lower is faster reproduction; invert for intuition
    ax[4].set_title("Reproduction Cooldown (lower=faster)")

    # Kind timeline scatter
    color_map = {"reproduction": "green", "mortality_capacity": "red"}
    idx_last_row = (rows - 1) * 2
    ax[idx_last_row + 1].scatter(
        ticks,
        [1] * len(ticks),
        c=[color_map.get(k or "unknown", "gray") for k in kinds],
        s=20,
    )
    ax[idx_last_row + 1].set_yticks([])
    ax[idx_last_row + 1].set_title("Adaptation Events (type by color)")

    if has_adaptive:
        assert adaptive_r is not None
        assert pop_hist is not None
        # Plot r_base and population on shared x; population scaled
        # separately (secondary axis)
        r_ticks = [e["tick"] for e in adaptive_r]
        r_vals = [e["r_base_new"] for e in adaptive_r]
        pop_ticks = [t for (t, p) in pop_hist]
        pop_vals = [p for (t, p) in pop_hist]
        ax[idx_last_row].plot(r_ticks, r_vals, color="purple", label="adaptive r_base")
        ax2 = ax[idx_last_row].twinx()
        ax2.plot(pop_ticks, pop_vals, color="gray", alpha=0.5, label="population")
        if pop_band and pop_band[0] is not None:
            ax2.axhline(pop_band[0], color="green", linestyle="--", linewidth=1, alpha=0.6)
        if pop_band and pop_band[1] is not None:
            ax2.axhline(pop_band[1], color="red", linestyle="--", linewidth=1, alpha=0.6)
        ax[idx_last_row].set_title("Adaptive r_base (purple) & Population (gray)")
        # Combine legends
        lines1, labels1 = ax[idx_last_row].get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax[idx_last_row].legend(lines1 + lines2, labels1 + labels2, fontsize=8)
        ax[idx_last_row].grid(alpha=0.3)

    for a in ax[:idx_last_row]:
        a.grid(alpha=0.3)
        a.legend(fontsize=8)
        if annotate_last and ticks:
            # Annotate last value
            try:
                ydata = a.lines[0].get_ydata()
                a.annotate(
                    f"{ydata[-1]:.4g}",
                    xy=(ticks[-1], ydata[-1]),
                    xytext=(5, 0),
                    textcoords="offset points",
                    fontsize=8,
                )
            except (ImportError, ValueError, RuntimeError):
                pass

    if title:
        fig.suptitle(title, fontsize=14)

    plt.tight_layout(rect=(0, 0, 1, 0.97) if title else None)
    plt.savefig(out_path, dpi=150)
    print(f"Saved plot to {out_path}")
    if show:
        try:
            plt.show()
        except (ImportError, ValueError, RuntimeError):
            print("Show failed (likely headless). Image saved.")
    return 0


def parse_args(argv: List[str]) -> Any:
    p = argparse.ArgumentParser(description="Plot adaptation parameter curves over time.")
    p.add_argument(
        "history",
        nargs="?",
        default="artifacts/data/adaptation_history.json",
        help="Path to adaptation_history.json",
    )
    p.add_argument("--out", default="adaptation_curves.png", help="Output image file path.")
    p.add_argument("--window", type=int, default=None, help="Plot only last N ticks.")
    p.add_argument("--backend", default=None, help="Matplotlib backend override (default Agg).")
    p.add_argument("--show", action="store_true", help="Display the plot window if possible.")
    p.add_argument(
        "--kind-filter",
        action="append",
        help="Only include entries whose kind matches (can repeat).",
    )
    p.add_argument("--title", default=None, help="Optional figure title.")
    return p.parse_args(argv)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    _select_backend(args.backend)
    path = Path(args.history)
    if not path.exists():
        print(f"History file not found: {path}")
        sys.exit(1)
    entries, adaptive_r, pop_hist, pop_band = load_history(path)
    entries = filter_entries(entries, args.window, args.kind_filter)
    code = plot(
        entries,
        Path(args.out),
        title=args.title,
        show=args.show,
        adaptive_r=adaptive_r,
        pop_hist=pop_hist,
        pop_band=pop_band,
    )
    sys.exit(code)
