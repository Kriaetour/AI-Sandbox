#!/usr/bin/env python3
"""
Military RL Model Comparison Demo
Showcases different trained models in optimal inference mode.
"""

import json
import os
from optimal_military_runner import OptimalMilitaryRunner

def compare_models():
    """Compare different trained models on the same scenario."""

    models_to_test = [
        {
            'name': 'Ultra V2 (1501 eps)',
            'path': 'artifacts/models/military_qtable_ultra_v2_final_ep1501.json',
            'description': 'Most comprehensive - 71,954 states'
        },
        {
            'name': 'Ultra V2 (501 eps)',
            'path': 'artifacts/models/military_qtable_ultra_v2_final_ep501.json',
            'description': 'Strong performer - 41,679 states'
        },
        {
            'name': 'Ultra V2 (21 eps)',
            'path': 'artifacts/models/military_qtable_ultra_v2_final_ep21.json',
            'description': 'Fast training - 3,302 states'
        },
        {
            'name': '100% Coverage (5 eps)',
            'path': 'artifacts/models/military_100p_final_ep5.json',
            'description': 'Balanced approach - 2,340 states'
        }
    ]

    # Filter to only existing models
    available_models = []
    for model in models_to_test:
        if os.path.exists(model['path']):
            available_models.append(model)
        else:
            print(f"⚠️  Model not found: {model['path']}")

    if not available_models:
        print("❌ No trained models found!")
        return

    print(f"🎯 Comparing {len(available_models)} trained models...")
    print("="*80)

    results = {}

    for model_info in available_models:
        print(f"\n🚀 Testing: {model_info['name']}")
        print(f"📝 {model_info['description']}")

        try:
            runner = OptimalMilitaryRunner(model_info['path'], epsilon=0.0)

            # Skip models with no learned states
            if len(runner.agent.q_table) == 0:
                print(f"⚠️  Skipping {model_info['name']} - no learned states")
                continue

            # Quick test with same seed for fair comparison - REDUCED for demo
            result = runner.run_optimal_simulation(
                num_episodes=1,  # Reduced from 3
                max_ticks=200,   # Reduced from 500
                num_tribes=4,    # Reduced from 6
                world_seed=12345,
                verbose=False
            )

            results[model_info['name']] = result

            print(f"✅ Actions: {result['total_actions']}")
            print(f"✅ Total Reward: {result['total_reward']:.2f}")
            print(f"✅ Avg Reward/Action: {result['avg_reward_per_action']:.3f}")
            print(f"✅ States Visited: {result['unique_states_visited']}")

        except Exception as e:
            print(f"❌ Failed to test {model_info['name']}: {str(e)[:100]}...")
            # Don't add to results if failed

    # Summary comparison
    if results:
        print("\n" + "="*80)
        print("🏆 MODEL COMPARISON SUMMARY")
        print("="*80)

        print(f"{'Model':<15} {'Actions':<8} {'Reward':<10} {'States':<8}")
        print("-" * 60)

        for name, result in results.items():
            print(f"{name:<15} {result['total_actions']:<8} {result['total_reward']:<10.2f} {result['unique_states_visited']:<8}")

        # Find best model
        best_model = max(results.items(), key=lambda x: x[1]['avg_reward_per_action'])
        print(f"\n🎯 Best performing model: {best_model[0]}")
        print(f"Avg Reward/Action: {best_model[1]['avg_reward_per_action']:.3f}")


if __name__ == "__main__":
    compare_models()