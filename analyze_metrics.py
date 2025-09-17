import csv

with open('artifacts/military_training_metrics.csv', 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

if rows:
    total_new = sum(int(r['new_states']) for r in rows)
    total_time = sum(float(r['batch_seconds']) for r in rows)
    avg_states_sec = total_new / total_time if total_time > 0 else 0
    print(f'Avg states/sec: {avg_states_sec:.4f}')
    print(f'Total new states: {total_new}')
    print('Coverage growth (last 5 batches):')
    for r in rows[-5:]:
        print(f'  Ep {r["batch_end_ep"]}: {float(r["coverage_percent"]):.4f}%')
else:
    print('CSV is empty - no training batches completed yet')