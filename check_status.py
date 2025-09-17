try:
    with open('artifacts/checkpoints/military_unique_states_100p.json', 'r') as f:
        import json
        data = json.load(f)
        coverage = data['count'] / 647280 * 100
        print(f'Current coverage: {coverage:.2f}% ({data["count"]:,} states)')
except Exception as e:
    print(f'No training data: {e}')

import glob
checkpoints = glob.glob('artifacts/checkpoints/military_100p_checkpoint_ep*.json')
if checkpoints:
    # Find the one with highest episode number
    latest = max(checkpoints, key=lambda x: int(x.split('ep')[-1].split('.')[0]))
    print(f'Latest checkpoint: {latest.split("/")[-1].split("\\\\")[-1]}')
else:
    print('No checkpoints found')