import os
import sys

sys.path.append(os.path.dirname(__file__))
import markov_dialogue as md

# Clear in-memory strict models
md._STRICT_HOSTILE_MODEL = None
md._STRICT_NEUTRAL_MODEL = None
h, n = md._build_strict_models()
print("=== Reload Test ===")
print("Idle samples after reload:")
for _ in range(5):
    print(" ", md.generate_markov_dialogue("idle", trait="peaceful"))
print("=== End Reload Test ===")
