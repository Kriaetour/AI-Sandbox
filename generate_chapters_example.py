"""Example script demonstrating Chronicler chapter generation workflow.
This script now uses real LLM APIs when available, with fallback to mock functions.
Set API keys as environment variables: OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY
"""
from typing import List, Dict, Any
import json
import sys
from dotenv import load_dotenv
from chronicler_prompts import (
    EraEvents,
    assemble_llm_payload,
)
from llm_config import get_llm_client, call_llm, summarize_text

# Load environment variables from .env file
load_dotenv()


def generate_chapters(eras: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Get LLM client (will use mock if no API keys available)
    client = get_llm_client()
    
    chapters = []
    prev_summary = None
    for idx, era_dict in enumerate(eras, start=1):
        era = EraEvents.from_dict(era_dict)
        payload = assemble_llm_payload(era, prev_summary, idx)
        
        # Extract system and user messages for the unified interface
        system_prompt = next((m['content'] for m in payload['messages'] if m['role'] == 'system'), '')
        user_prompt = next((m['content'] for m in payload['messages'] if m['role'] == 'user'), '')
        
        # Generate narrative using real LLM
        narrative = call_llm(client, user_prompt, system_prompt, max_tokens=1000, temperature=0.7)
        
        # Generate summary using real LLM
        summary = summarize_text(client, narrative)
        
        chapters.append(
            {
                "chapter": idx,
                "era_title": era.era_title,
                "narrative": narrative,
                "summary": summary,
                "tick_range": [era.start_tick, era.end_tick],
            }
        )
        prev_summary = summary
    return chapters


if __name__ == "__main__":
    # Load eras from briefing.json instead of hardcoded sample data
    briefing_file = sys.argv[1] if len(sys.argv) > 1 else "briefing.json"
    
    try:
        with open(briefing_file, "r", encoding="utf-8") as f:
            sample_eras = json.load(f)
        print(f"Loaded {len(sample_eras)} eras from {briefing_file}")
    except FileNotFoundError:
        print(f"Error: {briefing_file} not found. Run historian_briefing.py first to generate it.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing {briefing_file}: {e}")
        sys.exit(1)
    
    out = generate_chapters(sample_eras)
    for ch in out:
        print(f"\n=== Chapter {ch['chapter']} | {ch['era_title']} ({ch['tick_range'][0]}-{ch['tick_range'][1]}) ===")
        print(ch['narrative'])
        print("-- Summary --")
        print(ch['summary'])
