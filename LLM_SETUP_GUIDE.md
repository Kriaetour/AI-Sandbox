# LLM Setup Guide

This guide explains how to set up real LLM APIs for the Chronicler narrative system.

## Supported Providers

The system supports:
- **Google Gemini** (Recommended - Free tier available)
- **OpenAI** (GPT-4, GPT-3.5-turbo)
- **Anthropic** (Claude)
- **Mock** (for testing without API keys)

## Installation

Install the required packages:

```bash
# For Google Gemini (Recommended)
pip install google-generativeai python-dotenv

# For OpenAI
pip install openai

# For Anthropic
pip install anthropic

# All providers (recommended)
pip install google-generativeai python-dotenv openai anthropic
```

## API Key Setup

Set your API keys as environment variables:

### Windows (PowerShell)
```powershell
# Google Gemini (Recommended)
$env:GOOGLE_API_KEY = "your-google-api-key-here"

# OpenAI
$env:OPENAI_API_KEY = "your-openai-api-key-here"

# Anthropic
$env:ANTHROPIC_API_KEY = "your-anthropic-api-key-here"
```

### Windows (Command Prompt)
```cmd
set GOOGLE_API_KEY=your-google-api-key-here
set OPENAI_API_KEY=your-openai-api-key-here
set ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

### Linux/macOS
```bash
export GOOGLE_API_KEY="your-google-api-key-here"
export OPENAI_API_KEY="your-openai-api-key-here"
export ANTHROPIC_API_KEY="your-anthropic-api-key-here"
```

### Permanent Setup (Windows)
1. Search for "Environment Variables" in Windows search
2. Click "Edit the system environment variables"
3. Click "Environment Variables"
4. Under "User variables", click "New"
5. Variable name: `GOOGLE_API_KEY` (or `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)
6. Variable value: `your-api-key-here`
7. Click OK

## Testing Setup

Test that your API keys are working:

```bash
# This will use real LLM if keys are set, mock otherwise
# Priority: Google Gemini → OpenAI → Anthropic → Mock
python generate_chapters_example.py

# Force specific provider
python -c "from llm_config import get_llm_client; client = get_llm_client('google'); print('Google Gemini client ready' if hasattr(client, 'model') else 'Failed')"
python -c "from llm_config import get_llm_client; client = get_llm_client('openai'); print('OpenAI client ready' if hasattr(client, 'client') else 'Failed')"
```

## Usage Examples

### With Google Gemini (Recommended)
```bash
# Set API key
$env:GOOGLE_API_KEY = "AIza..."

# Run pipeline
python historian_chronicler_pipeline.py
```

### With OpenAI
```bash
# Set API key
$env:OPENAI_API_KEY = "sk-..."

# Run pipeline
python historian_chronicler_pipeline.py
```

### With Anthropic
```bash
# Set API key
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# Run with specific model
python generate_chapters_example.py briefing.json
```

## Configuration Options

You can customize the LLM behavior by modifying `llm_config.py`:

```python
# Change model
DEFAULT_MODEL = {
    "google": "gemini-1.5-flash",  # or "gemini-1.5-pro"
    "openai": "gpt-4-turbo",  # or "gpt-3.5-turbo"
    "anthropic": "claude-3-sonnet-20240229"
}

# Adjust parameters
DEFAULT_TEMPERATURE = 0.8  # Higher = more creative
DEFAULT_MAX_TOKENS = 1500  # Longer responses
```

## Troubleshooting

### "No API keys found" Warning
- Make sure you've set the environment variables correctly
- Restart your terminal/command prompt after setting variables
- Check variable names: `GOOGLE_API_KEY`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY`

### Import Errors
- Install required packages: `pip install google-generativeai python-dotenv openai anthropic`
- Make sure you're using Python 3.7+

### API Errors
- Check your API key is valid and has credits
- Verify your internet connection
- Check API rate limits
- For Google Gemini: Ensure your API key has Gemini API enabled in Google AI Studio

### Fallback Behavior
If API keys are not available, the system automatically uses the mock client for testing.

## Security Notes

- Never commit API keys to version control
- Use environment variables or secure key management
- Rotate keys regularly
- Monitor API usage and costs

## Cost Estimation

Approximate costs per chapter (based on current pricing):

- **Google Gemini 1.5 Flash**: Free tier available, ~$0.0005-0.001 per chapter after
- **Google Gemini 1.5 Pro**: ~$0.01-0.02 per chapter
- **OpenAI GPT-4**: ~$0.03-0.06 per chapter
- **OpenAI GPT-3.5**: ~$0.002-0.004 per chapter
- **Anthropic Claude**: ~$0.015-0.03 per chapter

Costs vary based on chapter length and model settings.