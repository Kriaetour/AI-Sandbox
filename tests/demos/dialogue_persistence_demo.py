import os
import sys

sys.path.append(os.path.dirname(__file__))
from markov_dialogue import (
    learn_dialogue,
    generate_markov_dialogue,
    flush_dialogue_state,
    STRICT_NEUTRAL_STATE,
    STRICT_HOSTILE_STATE,
)

print("=== Dialogue Strict Persistence Demo ===")
print("Initial idle samples:")
for _ in range(3):
    print(" ", generate_markov_dialogue("idle", trait="peaceful"))

new_lines = [
    "Quiet rivers reflect patient stories tonight",
    "Calm sharing builds accord among wanderers",
]
for ln in new_lines:
    learn_dialogue("idle", ln)

flush_dialogue_state()
print("\nAfter learning + flush (idle samples):")
for _ in range(5):
    print(" ", generate_markov_dialogue("idle", trait="peaceful"))

print("\nState files:")
print(" Neutral exists:", os.path.exists(STRICT_NEUTRAL_STATE), STRICT_NEUTRAL_STATE)
print(" Hostile exists:", os.path.exists(STRICT_HOSTILE_STATE), STRICT_HOSTILE_STATE)
print("=== End Demo ===")
