import sys
import os

sys.path.append(os.path.dirname(__file__))
from markov_dialogue import generate_markov_dialogue, USE_STRICT_CONDITIONAL

print("STRICT", USE_STRICT_CONDITIONAL)
print("Neutral idle:")
for _ in range(6):
    print(generate_markov_dialogue("idle", trait="peaceful"))
print("\nEncounter peaceful (maps to idle):")
for _ in range(6):
    print(generate_markov_dialogue("encounter", trait="peaceful"))
print("\nHostile:")
for _ in range(6):
    print(generate_markov_dialogue("hostility", trait="aggressive"))
