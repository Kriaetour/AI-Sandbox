# Historian-Chronicler Narrative Pipeline

This system transforms AI Sandbox simulation logs into structured historical narratives through a two-stage process with **real LLM integration**.

## Overview

1. **Historian Briefing** (`historian_briefing.py`): Parses raw simulation logs and extracts significant events into structured JSON eras
2. **Chronicler Narrative** (`generate_chapters_example.py`): Uses **OpenAI GPT-4, Anthropic Claude, or mock** to transform briefing data into compelling chapter-based historical narratives

## Quick Start

### Complete Pipeline (Recommended)
Run the full pipeline in one command:
```bash
python historian_chronicler_pipeline.py
```

This generates:
- `briefing.json` - Structured event data by era
- `chapters.json` - Narrative chapters with summaries

### With Real LLMs
Set your API keys and run:
```bash
# OpenAI
export OPENAI_API_KEY="your-key-here"
python historian_chronicler_pipeline.py

# Anthropic
export ANTHROPIC_API_KEY="your-key-here"
python historian_chronicler_pipeline.py
```

### Custom Files
```bash
python historian_chronicler_pipeline.py log.txt my_briefing.json my_chapters.json
```

## Individual Components

### Generate Briefing Only
```bash
python historian_briefing.py --output briefing.json
```

Options:
- `--log-file FILE` - Input log file (default: log.txt)
- `--output FILE` - Output JSON file (default: stdout)
- `--ticks-per-era N` - Era size in ticks (default: 500)

### Generate Chapters Only
```bash
python generate_chapters_example.py briefing.json
```

## LLM Integration

The system supports multiple LLM providers with automatic fallback:

### Supported Providers
- **OpenAI GPT-4** (recommended for quality)
- **Anthropic Claude** (alternative high-quality option)
- **Mock Client** (automatic fallback for testing)

### Setup
```bash
# Install dependencies
pip install openai anthropic

# Set API keys (choose one)
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Test setup
python generate_chapters_example.py
```

See `LLM_SETUP_GUIDE.md` for detailed setup instructions.

### Automatic Fallback
If no API keys are found, the system automatically uses mock responses for testing.

## Output Format

### Briefing JSON Structure
```json
[
  {
    "era_index": 0,
    "start_tick": 0,
    "end_tick": 499,
    "era_title": "Era of Conflict",
    "summary": ["TERRITORY_CONFLICT at tick 24", "..."],
    "key_events": [
      {
        "tick": 24,
        "type": "TERRITORY_CONFLICT",
        "factions": ["seed_11", "seed_8"],
        "damage": 5
      }
    ]
  }
]
```

### Chapters JSON Structure
```json
[
  {
    "chapter": 1,
    "era_title": "Era of Conflict",
    "narrative": "Epic historical narrative...",
    "summary": "Key points from the chapter",
    "tick_range": [0, 499],
    "event_count": 25
  }
]
```

## Integration with Real LLMs

The current implementation uses mock LLM functions. To integrate with real APIs:

1. Replace `mock_llm_call()` in `generate_chapters_example.py` with your LLM API
2. Replace `mock_llm_summarize()` with summarization API calls
3. Update `CHRONICLER_SYSTEM_PROMPT` in `chronicler_prompts.py` if needed

## Features

- **Era-based Segmentation**: Groups events into meaningful time periods
- **Narrative Memory**: Each chapter builds on previous summaries
- **Deterministic Output**: Events sorted by tick for consistent results
- **Flexible Configuration**: Adjustable era sizes and file paths
- **Clean Separation**: Debug output to stderr, clean JSON to files
- **Extensible Events**: Easy to add new event types and patterns

## Dependencies

- Python 3.7+
- Standard library only (json, re, argparse, subprocess)

## Files

- `historian_briefing.py` - Event extraction and briefing generation
- `generate_chapters_example.py` - Narrative chapter generation
- `historian_chronicler_pipeline.py` - Complete end-to-end pipeline
- `chronicler_prompts.py` - Prompt assembly utilities
- `briefing.json` - Generated briefing data
- `chapters.json` - Generated narrative chapters