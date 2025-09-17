#!/usr/bin/env python3
"""
Monitor Military RL Training Progress
"""

import time
import os
import json
from datetime import datetime

def monitor_training():
    """Monitor training progress and provide updates."""
    print("Monitoring Military RL Training Progress...")
    print("=" * 60)

    checkpoint_dir = "artifacts/checkpoints"
    last_episode = 0
    last_states = 0

    while True:
        try:
            if os.path.exists(checkpoint_dir):
                checkpoints = [f for f in os.listdir(checkpoint_dir)
                             if f.startswith('checkpoint_metadata')]

                if checkpoints:
                    # Get latest checkpoint
                    checkpoints.sort(key=lambda x: int(x.split('ep')[1].split('.')[0]))
                    latest_meta = checkpoints[-1]
                    episode_num = int(latest_meta.split('ep')[1].split('.')[0])

                    # Load metadata
                    with open(f'{checkpoint_dir}/{latest_meta}', 'r') as f:
                        metadata = json.load(f)

                    total_states = metadata['total_states']
                    coverage = (total_states / 645120) * 100

                    if episode_num != last_episode or total_states != last_states:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] Episode {episode_num:5d} | States: {total_states:6d} | Coverage: {coverage:6.2f}%")

                        if coverage >= 10.0:
                            print(f"\n🎉 ACHIEVED 10% STATE COVERAGE! ({total_states} states)")
                        if coverage >= 20.0:
                            print(f"\n🏆 ACHIEVED 20% STATE COVERAGE! ({total_states} states)")

                        last_episode = episode_num
                        last_states = total_states

            time.sleep(30)  # Check every 30 seconds

        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
            break
        except Exception as e:
            print(f"Error monitoring: {e}")
            time.sleep(10)

if __name__ == "__main__":
    monitor_training()