#!/usr/bin/env python3
"""
Quick Model Inspection Script
Shows basic statistics about trained models without running simulations.
"""

import json
import os
from collections import defaultdict

def inspect_models():
    """Inspect trained models and show basic statistics."""

    models_dir = "artifacts/models"
    if not os.path.exists(models_dir):
        print("❌ Models directory not found!")
        return

    model_files = [f for f in os.listdir(models_dir) if f.endswith('.json')]
    if not model_files:
        print("❌ No model files found!")
        return

    print(f"🔍 Inspecting {len(model_files)} model files...")
    print("="*80)

    model_stats = []

    for model_file in model_files:
        model_path = os.path.join(models_dir, model_file)

        try:
            with open(model_path, 'r') as f:
                data = json.load(f)

            if isinstance(data, dict):
                num_states = len(data)
                total_q_values = 0
                action_counts = defaultdict(int)

                for state_key, q_values in data.items():
                    if isinstance(q_values, list):
                        total_q_values += len(q_values)
                        # Count which actions have been learned (non-zero Q-values)
                        for i, q_val in enumerate(q_values):
                            if abs(q_val) > 0.001:  # Small threshold for "learned"
                                action_counts[i] += 1

                model_stats.append({
                    'name': model_file.replace('.json', '').replace('military_', ''),
                    'states': num_states,
                    'total_q': total_q_values,
                    'action_distribution': dict(action_counts)
                })

                print(f"📊 {model_file}:")
                print(f"   States: {num_states}")
                print(f"   Total Q-values: {total_q_values}")
                if action_counts:
                    print(f"   Learned Actions: {dict(action_counts)}")
                print()

        except Exception as e:
            print(f"❌ Failed to load {model_file}: {e}")

    # Summary
    if model_stats:
        print("="*80)
        print("🏆 MODEL SUMMARY")
        print("="*80)

        print(f"{'Model':<25} {'States':<8} {'Q-Values':<12}")
        print("-" * 50)

        for stat in sorted(model_stats, key=lambda x: x['states'], reverse=True):
            print(f"{stat['name']:<25} {stat['states']:<8} {stat['total_q']:<12}")

        # Find best model
        best_model = max(model_stats, key=lambda x: x['states'])
        print(f"\n🎯 Model with most states: {best_model['name']} ({best_model['states']} states)")


if __name__ == "__main__":
    inspect_models()