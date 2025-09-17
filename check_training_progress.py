#!/usr/bin/env python3
"""
Check training progress from checkpoints.
"""

import os
import json

def check_progress():
    checkpoint_dir = 'artifacts/checkpoints'
    if os.path.exists(checkpoint_dir):
        checkpoints = [f for f in os.listdir(checkpoint_dir) if f.startswith('checkpoint_metadata')]
        if checkpoints:
            # Sort by episode number
            checkpoints.sort(key=lambda x: int(x.split('ep')[1].split('.')[0]))
            latest = checkpoints[-1]

            with open(f'{checkpoint_dir}/{latest}', 'r') as f:
                data = json.load(f)

            # Handle different checkpoint formats
            coverage_key = "state_coverage_percent" if "state_coverage_percent" in data else "coverage_percent"
            coverage = data.get(coverage_key, (data["total_states"] / 645120) * 100)

            print('Latest Checkpoint Found:')
            print(f'Episode: {data["episode"]}')
            print(f'Total States Learned: {data["total_states"]}')
            print(f'State Coverage: {coverage:.4f}%')
            print(f'Training Time: {data["training_time"]:.1f} seconds')
            print(f'Timestamp: {data["timestamp"]}')

            # Calculate progress towards goals
            target_10pct = 64512
            target_20pct = 129024
            current = data['total_states']

            print(f'\nProgress to 10% target: {current/target_10pct*100:.1f}% ({current}/{target_10pct})')
            print(f'Progress to 20% target: {current/target_20pct*100:.1f}% ({current}/{target_20pct})')

            # Check if model file exists
            model_file = f'{checkpoint_dir}/military_qtable_checkpoint_ep{data["episode"]}.json'
            if os.path.exists(model_file):
                model_size = os.path.getsize(model_file) / (1024 * 1024)  # MB
                print(f'Model file size: {model_size:.2f} MB')
        else:
            print('No checkpoints found')
    else:
        print('Checkpoint directory not found')

if __name__ == "__main__":
    check_progress()