import sys
import os

sys.path.append(os.path.dirname(__file__))
from markov_dialogue import generate_markov_dialogue

print("=== Variation Test (idle) ===")
for i in range(12):
    print(f"{i+1:02d}:", generate_markov_dialogue("idle", trait="peaceful"))
print("\n=== Variation Test (encounter->peaceful maps idle) ===")
for i in range(12):
    print(f"{i+1:02d}:", generate_markov_dialogue("encounter", trait="peaceful"))
