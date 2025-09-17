#!/usr/bin/env python3
"""Diagnose Q-table plateau and state diversity.

Parses the latest military Q-table checkpoint, normalizes tuple keys,
and reports uniqueness and per-dimension coverage to understand why
state growth may have plateaued.
"""

import os
import json
import re
from collections import Counter

CKPT_DIR = "artifacts/checkpoints"


def load_latest():
    files = [
        f for f in os.listdir(CKPT_DIR)
        if f.startswith("military_qtable_checkpoint_ep")
    ]
    if not files:
        print("No checkpoint files found")
        return None, None
    files.sort(key=lambda x: int(re.search(r"ep(\d+)", x).group(1)))
    latest = files[-1]
    with open(os.path.join(CKPT_DIR, latest), "r") as f:
        data = json.load(f)
    return latest, data


def parse_state_keys(raw_keys):
    parsed = []
    for k in raw_keys:
        inner = k.strip().strip("()")
        parts = [p for p in inner.split(",") if p.strip() != ""]
        vals = []
        ok = True
        for p in parts:
            m = re.search(r"(-?\d+)", p)
            if m:
                vals.append(int(m.group(1)))
            else:
                ok = False
                break
        if ok and len(vals) == 6:
            parsed.append(tuple(vals))
    return parsed


def analyze():
    latest, data = load_latest()
    if data is None:
        return
    print(f"Latest file: {latest}")
    print(f"Raw entries: {len(data)}")
    parsed = parse_state_keys(data.keys())
    print(f"Parsed state tuples: {len(parsed)}")
    unique = set(parsed)
    print(f"Unique states: {len(unique)}")
    if not unique:
        print("NO PARSED STATES -> serialization format issue")
        return
    dims = list(zip(*unique))
    for i, d in enumerate(dims):
        c = Counter(d)
        print(
            f"Dim {i}: unique={len(c)} min={min(d)} max={max(d)} "
            f"top5={c.most_common(5)}"
        )
    print("Sample states:", list(unique)[:10])


if __name__ == "__main__":
    analyze()
