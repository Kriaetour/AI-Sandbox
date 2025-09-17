import random
from types import SimpleNamespace

from npcs.npc import NPC
from markov_dialogue import (
    learn_dialogue,
    flush_dialogue_state,
)


class DummyNPC(SimpleNamespace):
    pass


def build_stub_npc(name, faction_id, traits=None):
    npc = NPC(
        name=name,
        coordinates=(0, 0),
        age=25,
        faction_id=faction_id,
        traits=traits or ["curious"],
    )
    return npc


def run_dialogue_matrix():
    random.seed(42)
    npc_a = build_stub_npc("Ael", "TribeAlpha", traits=["aggressive"])
    npc_b = build_stub_npc("Bea", "TribeBeta", traits=["peaceful"])

    tribal_diplomacy = {
        (npc_a.faction_id, npc_b.faction_id): 0.7,  # friendly
        (npc_b.faction_id, npc_a.faction_id): -0.8,  # hostile (asymmetric example)
    }

    contexts = ["encounter", "trade", "idle", "hostility"]
    results = []
    for ctx in contexts:
        line_ab = npc_a.generate_dialogue(npc_b, ctx, tribal_diplomacy, tribe_lookup=None)
        line_ba = npc_b.generate_dialogue(npc_a, ctx, tribal_diplomacy, tribe_lookup=None)
        results.append((ctx, line_ab, line_ba))

    print("=== Markov Dialogue Integration Test (Phase 1 Baseline) ===")
    for ctx, ab, ba in results:
        print(f"Context: {ctx}\n  A->B: {ab}\n  B->A: {ba}")

    # Learning phase: inject new lines emphasizing peace and warning
    learn_dialogue("encounter", "We come in peace let our tribes prosper together")
    learn_dialogue("hostility", "Stand down now this conflict helps no one")
    learn_dialogue("trade", "Fair exchange strengthens the path between our fires")
    learn_dialogue("idle", "Stories bind memory to the living moment")
    flush_dialogue_state()

    # Phase 2: standard generation after learning
    results2 = []
    for ctx in contexts:
        results2.append(
            (
                ctx,
                npc_a.generate_dialogue(npc_b, ctx, tribal_diplomacy, tribe_lookup=None),
                npc_b.generate_dialogue(npc_a, ctx, tribal_diplomacy, tribe_lookup=None),
            )
        )
    print("\n=== Markov Dialogue Integration Test (Phase 2 After Learning Standard Config) ===")
    for ctx, ab, ba in results2:
        print(f"Context: {ctx}\n  A->B: {ab}\n  B->A: {ba}")

    # Phase 3 & 4: Skipped (update_dialogue_generation_config not available)
    # Style guard validation: generate multiple hostility vs encounter lines
    hostility_samples = []
    encounter_samples = []
    for _ in range(6):
        hostility_samples.append(
            npc_a.generate_dialogue(npc_b, "hostility", tribal_diplomacy, tribe_lookup=None)
        )
        encounter_samples.append(
            npc_a.generate_dialogue(npc_b, "encounter", tribal_diplomacy, tribe_lookup=None)
        )
    print("\n=== Style Guard Samples (Hostility) ===")
    for sample in hostility_samples:
        print(sample)
    print("\n=== Style Guard Samples (Encounter) ===")
    for sample in encounter_samples:
        print(sample)

    hostile_tokens = [
        "back",
        "leave",
        "challenge",
        "threat",
        "force",
        "stand",
        "caution",
    ]
    hostility_hits = sum(any(t in s.lower() for t in hostile_tokens) for s in hostility_samples)
    encounter_hits = sum(any(t in s.lower() for t in hostile_tokens) for s in encounter_samples)
    print(f"\nHostility lines with hostile token: {hostility_hits}/{len(hostility_samples)}")
    print(
        f"Encounter lines with hostile token (should be lower): {encounter_hits}/{len(encounter_samples)}"
    )


if __name__ == "__main__":
    run_dialogue_matrix()
