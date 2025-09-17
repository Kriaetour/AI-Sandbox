import sys
import os

sys.path.append(os.path.dirname(__file__))
from markov_dialogue import (
    learn_dialogue,
    generate_markov_dialogue,
    USE_STRICT_CONDITIONAL,
)

print("Strict conditional:", USE_STRICT_CONDITIONAL)
# Provide new neutral lines containing hostile tokens that should be stripped
samples = [
    "Greetings traveler stay back we bring peace",
    "We share stories not challenge or threat here",
    "Leave hostility behind and share goods calmly",
]
for s in samples:
    learn_dialogue("idle", s)
print("\nGenerated idle after learning:")
for _ in range(6):
    print(generate_markov_dialogue("idle", trait="peaceful"))
print("\nGenerated encounter after learning:")
for _ in range(6):
    print(generate_markov_dialogue("encounter", trait="peaceful"))
print("\nGenerated hostility (should remain unchanged style):")
for _ in range(3):
    print(generate_markov_dialogue("hostility", trait="aggressive"))
