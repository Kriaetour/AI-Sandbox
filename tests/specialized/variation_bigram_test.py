import os
import sys

from markov_dialogue import generate_markov_dialogue
from collections import Counter

sys.path.append(os.path.dirname(__file__))


def bigrams(text):
    toks = text.split()
    return list(zip(toks, toks[1:]))


lines = []
for i in range(30):
    line = generate_markov_dialogue("idle", trait="peaceful")
    lines.append(line)

print("=== Bigram Diversity Test (idle, 30 lines) ===")
for i, line in enumerate(lines, 1):
    print(f"{i:02d}: {line}")

# Compute consecutive overlap ratios
print("\nConsecutive bigram overlap ratios:")
prev = None
for line in lines:
    if prev is None:
        print(" - (first)")
    else:
        b_prev = set(bigrams(prev))
        b_curr = set(bigrams(line))
        if b_prev:
            overlap = len(b_prev & b_curr) / len(b_prev)
        else:
            overlap = 0.0
        print(f" {overlap:.2f}")
    prev = line

# Top recurring lines count
print("\nLine frequency counts:")
for line, cnt in Counter(lines).most_common():
    print(f" {cnt}x  {line}")
