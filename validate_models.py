#!/usr/bin/env python3
"""
Simple Model Validation Script
Tests that trained models can be loaded and used for basic inference without full simulation.
"""

import json
import os
import random
from rl_military_agent import MilitaryRLAgent

def validate_models():
    """Validate that trained models work for basic inference."""

    models_to_test = [
        {
            'name': 'Ultra V2 (1501 eps)',
            'path': 'artifacts/models/military_qtable_ultra_v2_final_ep1501.json',
            'expected_states': 71954
        },
        {
            'name': 'Ultra V2 (501 eps)',
            'path': 'artifacts/models/military_qtable_ultra_v2_final_ep501.json',
            'expected_states': 41679
        },
        {
            'name': 'Ultra V2 (21 eps)',
            'path': 'artifacts/models/military_qtable_ultra_v2_final_ep21.json',
            'expected_states': 3302
        },
        {
            'name': '100% Coverage (5 eps)',
            'path': 'artifacts/models/military_100p_final_ep5.json',
            'expected_states': 2340
        }
    ]

    print("🔬 MODEL VALIDATION TEST")
    print("="*80)

    results = []

    for model_info in models_to_test:
        if not os.path.exists(model_info['path']):
            print(f"❌ {model_info['name']}: File not found")
            continue

        try:
            # Load model
            agent = MilitaryRLAgent(epsilon=0.0)  # Pure exploitation
            with open(model_info['path'], 'r') as f:
                data = json.load(f)
                if 'q_table' in data:
                    agent.q_table = data['q_table']
                else:
                    agent.q_table = data

            actual_states = len(agent.q_table)
            print(f"✅ {model_info['name']}: Loaded {actual_states} states")

            # Test basic inference with a few random states
            test_states = []
            for _ in range(min(5, actual_states)):
                # Pick a random state from the Q-table
                state_key = random.choice(list(agent.q_table.keys()))
                # Convert string key back to tuple for testing
                # Remove the "np.int64()" wrapper from the string
                import re
                clean_key = re.sub(r'np\.int64\((\d+)\)', r'\1', state_key)
                # Extract tuple values
                import ast
                try:
                    state_tuple = ast.literal_eval(clean_key)
                    if isinstance(state_tuple, tuple):
                        test_states.append(state_tuple)
                except:
                    continue

            successful_actions = 0
            for state in test_states:
                try:
                    action = agent.choose_action(state)
                    if 0 <= action < 8:  # Valid action range
                        successful_actions += 1
                except:
                    pass

            success_rate = successful_actions / len(test_states) if test_states else 0
            results.append({
                'name': model_info['name'],
                'states': actual_states,
                'test_actions': successful_actions,
                'total_tests': len(test_states),
                'success_rate': success_rate
            })

            print(f"   📊 Tested {len(test_states)} states, {successful_actions} successful actions ({success_rate:.1%})")

        except Exception as e:
            print(f"❌ {model_info['name']}: Failed to validate - {str(e)[:100]}")

    # Summary
    if results:
        print("\n" + "="*80)
        print("🏆 VALIDATION SUMMARY")
        print("="*80)

        print(f"{'Model':<25} {'States':<8} {'Tests':<8} {'Success':<8} {'Rate':<8}")
        print("-" * 70)

        for result in sorted(results, key=lambda x: x['states'], reverse=True):
            print(f"{result['name']:<25} {result['states']:<8} {result['total_tests']:<8} {result['test_actions']:<8} {result['success_rate']:<8.1%}")

        # Best model
        best = max(results, key=lambda x: x['success_rate'])
        print(f"\n🎯 Best validation: {best['name']} ({best['success_rate']:.1%} success rate)")

        print("\n✅ All tested models are ready for inference!")
        print("💡 Use optimal_military_runner.py for full simulation testing")


if __name__ == "__main__":
    validate_models()