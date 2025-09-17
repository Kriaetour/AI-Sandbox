from __future__ import annotations
"""Chronicler prompt assembly utilities.

Provides:
- build_system_prompt(): Persona definition for the LLM.
- build_chapter_prompt(): Builds the user prompt for a chapter using prior summary + era events.
- summarize_chapter(): Helper to request / perform a concise summary (3 bullet key points) of a narrative.
- assemble_llm_payload(): Returns the messages list for an OpenAI/Anthropic-style chat completion call.

Designed to be stateless: caller supplies previous summary text explicitly.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import json

CHRONICLER_SYSTEM_PROMPT = (
    "You are the Chronicler, a master historian and storyteller. Your task is to interpret a structured log of events from a complex world simulation and weave it into a compelling, chapter-based historical narrative.\n\n"
    "Tone: Epic, somber, insightful – like a historical saga.\n\n"
    "Rules:\n"
    "1. Do NOT just list the events; infer plausible causality and consequences.\n"
    "2. Emphasize rise and fall of factions, turning points, resource pressures, conflict catalysts.\n"
    "3. Preserve factual anchors (names, ticks, outcomes) but you may embellish texture (atmosphere, mood).\n"
    "4. Avoid anachronism or meta commentary.\n"
    "5. Output a single chapter – no epilogues, no future speculation beyond hints.\n"
    "6. Maintain an elevated register without purple excess.\n"
    "7. If data seems sparse, extrapolate cautiously rather than listing gaps.\n"
)

@dataclass
class EraEvents:
    start_tick: int
    end_tick: int
    era_title: str
    key_events: List[Dict[str, Any]]

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EraEvents":
        return cls(
            start_tick=d["start_tick"],
            end_tick=d["end_tick"],
            era_title=d.get("era_title", "Untitled Era"),
            key_events=d.get("key_events", []),
        )


def build_system_prompt() -> str:
    """Return the static Chronicler system persona."""
    return CHRONICLER_SYSTEM_PROMPT


def _format_events_json(era: EraEvents) -> str:
    # Compact but stable ordering for reproducibility
    payload = {
        "start_tick": era.start_tick,
        "end_tick": era.end_tick,
        "era_title": era.era_title,
        "key_events": era.key_events,
    }
    return json.dumps(payload, indent=2, sort_keys=False)


def build_chapter_prompt(
    era: EraEvents,
    previous_summary: Optional[str] = None,
    chapter_number: Optional[int] = None,
) -> str:
    """Build the user-facing chapter prompt incorporating prior summary if present."""
    header = "You will now write the next chapter of the saga." if previous_summary else "Begin the saga's first chapter." \

    chapter_line = (
        f"This is Chapter {chapter_number}.\n" if chapter_number is not None else ""
    )
    memory_block = (
        f"Previously in this history (concise recap):\n{previous_summary.strip()}\n\n" if previous_summary else ""
    )
    events_block = _format_events_json(era)
    return (
        f"{header}\n{chapter_line}{memory_block}Interpret the following structured era event data as narrative source material.\n\nJSON SOURCE\n{events_block}\n\nWrite the chapter now."  # Final instruction
    )


def summarize_chapter(narrative_text: str) -> str:
    """Produce a deterministic local summary heuristic (fallback) returning three bullet points.

    Caller may instead send the narrative to an LLM with a summarization prompt; this is a simple backup.
    """
    # Naive heuristic: extract first sentence, midpoint sentence, concluding sentence.
    # Split conservatively on periods; keep short.
    sentences = [s.strip() for s in narrative_text.replace("\n", " ").split('.') if s.strip()]
    if not sentences:
        return "(No content to summarize)"
    picks = []
    picks.append(sentences[0])
    if len(sentences) > 2:
        picks.append(sentences[len(sentences)//2])
    if len(sentences) > 1:
        picks.append(sentences[-1])
    bullets = [f"- {s[:200]}" for s in picks[:3]]
    return "\n".join(bullets)


def assemble_llm_payload(
    era: EraEvents,
    previous_summary: Optional[str],
    chapter_number: Optional[int],
    model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    """Assemble a messages payload for a chat completion style API."""
    system = build_system_prompt()
    user = build_chapter_prompt(era, previous_summary, chapter_number)
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.85,
        "presence_penalty": 0.3,
        "frequency_penalty": 0.1,
    }

# Example utility for sequential chapter generation (pseudo usage):
# prev_summary = None
# for idx, era_dict in enumerate(eras):
#     era = EraEvents.from_dict(era_dict)
#     payload = assemble_llm_payload(era, prev_summary, idx+1)
#     response = call_llm(payload)  # user-defined
#     narrative = response['choices'][0]['message']['content']
#     prev_summary = summarize_chapter(narrative)  # or use LLM summarization
