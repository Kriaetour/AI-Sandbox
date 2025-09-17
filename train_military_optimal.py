#!/usr/bin/env python3
"""
Optimal Batch Training Runner for Military RL Agent

This script runs the optimal batch training parameters for maximum efficiency.
Based on analysis of 645,120 state space and RL best practices.
"""

import subprocess
import sys
import time

def run_optimal_training():
    """Run optimal batch training sequence."""

    print("🎯 MILITARY RL AGENT - OPTIMAL BATCH TRAINING")
    print("=" * 60)
    print("State Space: 645,120 | Target Coverage: 10% (64,512 states)")
    print()

    # Phase 1: Vectorized Batch for Exploration
    print("🚀 PHASE 1: VECTORIZED BATCH (Broad Exploration)")
    print("Parameters: 100 scenarios × 200 ticks = 20,000 decisions")
    start_time = time.time()

    result = subprocess.run([
        sys.executable, 'train_military_batch.py'
    ], input='3\n100\n200\n', text=True, capture_output=True)

    elapsed = time.time() - start_time
    print(f"Phase 1 completed in {elapsed:.1f}s")
    print("Completion output:", result.stdout.split('\n')[-5:])
    print()

    # Phase 2: Grouped Batch for Stable Learning
    print("⚖️  PHASE 2: GROUPED BATCH (Stable Learning)")
    print("Parameters: 50 episodes × 32 batches = 1,600 total episodes")
    start_time = time.time()

    result = subprocess.run([
        sys.executable, 'train_military_batch.py'
    ], input='2\n50\n32\n', text=True, capture_output=True)

    elapsed = time.time() - start_time
    print(f"Phase 2 completed in {elapsed:.1f}s")
    print("Completion output:", result.stdout.split('\n')[-5:])
    print()

    # Phase 3: Parallel Batch for Speed Optimization
    print("🔥 PHASE 3: PARALLEL BATCH (Speed Optimization)")
    print("Parameters: 1,612 episodes × 4 workers")
    start_time = time.time()

    result = subprocess.run([
        sys.executable, 'train_military_batch.py'
    ], input='1\n1612\n4\n', text=True, capture_output=True)

    elapsed = time.time() - start_time
    print(f"Phase 3 completed in {elapsed:.1f}s")
    print("Completion output:", result.stdout.split('\n')[-5:])
    print()

    print("✅ OPTIMAL TRAINING SEQUENCE COMPLETE!")
    print("Check artifacts/models/ for the trained models")

if __name__ == "__main__":
    run_optimal_training()