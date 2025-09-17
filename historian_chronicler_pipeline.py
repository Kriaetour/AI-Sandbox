#!/usr/bin/env python3
"""
Complete Historian-to-Chronicler Pipeline

This script demonstrates the full workflow:
1. Generate historian briefing from simulation logs
2. Use briefing to generate narrative chapters

Usage:
    python historian_chronicler_pipeline.py [log_file] [briefing_output] [chapters_output]

Example:
    python historian_chronicler_pipeline.py log.txt briefing.json chapters.json
"""
import json
import sys
import subprocess
from typing import List, Dict, Any
from dotenv import load_dotenv
from chronicler_prompts import EraEvents, assemble_llm_payload, summarize_chapter
from llm_config import get_llm_client, call_llm, summarize_text

# Load environment variables from .env file
load_dotenv()


def mock_llm_call(payload: Dict[str, Any]) -> str:
    """Mock LLM call for demonstration - replace with real API integration."""
    user_prompt = next(m['content'] for m in payload['messages'] if m['role'] == 'user')
    lines = [line for line in user_prompt.splitlines() if '"era_title"' in line or 'start_tick' in line or 'end_tick' in line]
    return (
        "In these days the chronicles speak of struggle and muted hope. "
        + " | ".join(lines[:3])
        + " ... The factions maneuvered, resources thinned, and destinies converged."
    )


def mock_llm_summarize(narrative: str) -> str:
    """Mock summarization - replace with real LLM call."""
    return summarize_chapter(narrative)


def generate_chapters_from_briefing(briefing_file: str) -> List[Dict[str, Any]]:
    """Generate narrative chapters from historian briefing."""
    with open(briefing_file, "r", encoding="utf-8") as f:
        eras = json.load(f)
    
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
        
        chapters.append({
            "chapter": idx,
            "era_title": era.era_title,
            "narrative": narrative,
            "summary": summary,
            "tick_range": [era.start_tick, era.end_tick],
            "event_count": len(era.key_events)
        })
        
        prev_summary = summary
    
    return chapters


def main():
    # Default arguments
    log_file = "log.txt"
    briefing_file = "briefing.json"
    chapters_file = "chapters.json"
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    if len(sys.argv) > 2:
        briefing_file = sys.argv[2]
    if len(sys.argv) > 3:
        chapters_file = sys.argv[3]
    
    print("=== Historian-Chronicler Pipeline ===")
    print(f"Log file: {log_file}")
    print(f"Briefing output: {briefing_file}")
    print(f"Chapters output: {chapters_file}")
    print()
    
    # Step 1: Generate historian briefing
    print("Step 1: Generating historian briefing...")
    try:
        subprocess.run([
            sys.executable, "historian_briefing.py",
            "--log-file", log_file,
            "--output", briefing_file
        ], capture_output=True, text=True, check=True)
        print("✓ Briefing generated successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to generate briefing: {e}")
        print(f"Error output: {e.stderr}")
        return
    
    # Step 2: Generate narrative chapters
    print("Step 2: Generating narrative chapters...")
    try:
        chapters = generate_chapters_from_briefing(briefing_file)
        print(f"✓ Generated {len(chapters)} chapters")
        
        # Save chapters to file
        with open(chapters_file, "w", encoding="utf-8") as f:
            json.dump(chapters, f, indent=2, ensure_ascii=False)
        print(f"✓ Chapters saved to {chapters_file}")
        
        # Print summary
        print("\n=== Chapter Summary ===")
        for ch in chapters:
            print(f"Chapter {ch['chapter']}: {ch['era_title']} "
                  f"({ch['tick_range'][0]}-{ch['tick_range'][1]}) - "
                  f"{ch['event_count']} events")
        
    except Exception as e:
        print(f"✗ Failed to generate chapters: {e}")
        return
    
    print("\n=== Pipeline Complete ===")
    print("Files generated:")
    print(f"  - {briefing_file} (historian briefing)")
    print(f"  - {chapters_file} (narrative chapters)")


if __name__ == "__main__":
    main()