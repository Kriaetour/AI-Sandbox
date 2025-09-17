# AI Sandbox Configuration Guide

This document describes the environment variables and configuration options available for customizing the AI Sandbox simulation.

## AI Integration Setup

### Google Gemini API
The AI Sandbox supports optional integration with Google's Gemini AI for enhanced narrative generation:

- **Environment Variable**: `GOOGLE_API_KEY=your_api_key_here`
- **Features Enabled**:
  - Dynamic NPC dialogue generation
  - Tribal story creation
  - Cultural concept discovery
  - RL training narratives
- **Fallback**: If no API key is provided, the system uses basic text generation

#### Setup Options:

**Option 1: .env file (Recommended for projects)**
```bash
# Create .env file in project root
echo "GOOGLE_API_KEY="" > .env
```

**Option 2: System Environment Variable (Windows)**
```powershell
# Set permanently in PowerShell profile
$env:GOOGLE_API_KEY = ""
# Or use System Properties > Environment Variables
```

**Option 3: VS Code Workspace Settings**
```json
{
  "terminal.integrated.env.windows": {
    "GOOGLE_API_KEY": ""
  }
}
```

To enable Gemini integration:
```bash
python main.py core 1000
```

## Core Simulation Settings

### Performance & Speed
- `SANDBOX_WORLD_FAST=1` - Enable fast mode: Skip expensive operations, throttle resource distribution
- `SANDBOX_WORLD_ULTRAFAST=1` - Enable ultra-fast mode: Maximum performance optimizations
- `SANDBOX_WORLD_PROFILE=1` - Enable profiling: Collect timing data every 200 ticks
- `SANDBOX_WORLD_RESOURCE_FREQ=N` - Override resource distribution frequency in fast mode (default: 10)
- `SANDBOX_WORLD_RESOURCE_DISABLE=1` - Disable resource distribution entirely
- `SANDBOX_USE_PARALLELISM=0` - Disable parallel processing (default: enabled)
- `SANDBOX_DISABLE_PARALLELISM=1` - Force disable parallelism

### Feature Toggles
- `SANDBOX_ALLOW_REPRO=1` - Enable reproduction mechanics
- `SANDBOX_ALLOW_MORTALITY=1` - Enable death mechanics
- `SANDBOX_ALLOW_COMBAT=1` - Enable combat systems
- `SANDBOX_LLM_DIALOGUE=true` - Enable LLM-powered dialogue generation
- `SANDBOX_LLM_LEXICON=true` - Enable LLM-powered tribal lexicon generation

### Logging & Debugging
- `SANDBOX_LOG_LEVEL=INFO|WARNING|ERROR` - Set logging verbosity (default: DEBUG)
- `AI_SANDBOX_SOCIAL_TICKS=N` - Override social interaction tick frequency

## RL Training Configuration

### Population RL Training
```bash
# Basic training
python train_rl_agent.py --target-pop 300 --episodes 100

# Advanced options
python train_rl_agent.py \
  --target-pop 500 \
  --episodes 200 \
  --epsilon-decay 0.995 \
  --save_path artifacts/models/qtable_custom.json \
  --log-level INFO
```

### Diplomacy RL Training
```bash
# Basic training
python train_diplomacy_rl.py --episodes 50 --max-ticks 200

# Advanced options
python train_diplomacy_rl.py \
  --episodes 100 \
  --max-ticks 500 \
  --epsilon-start 0.8 \
  --save-q artifacts/models/qtable_diplomacy_custom.json
```

## Simulation Modes

### Interactive Mode (Default)
```bash
python main.py
```
Provides menu-driven interface for different simulation types.

### Core Simulation
```bash
python main.py core 1000  # Run 1000 ticks
```

### Tribal Dynamics
```bash
python main.py tribal --ticks 300
```

### Social Interaction Focus
```bash
python main.py social --ticks 80
```

### Territory Management Demo
```bash
python main.py territory
```

## Feature Flag Bundles

The `SANDBOX_FEATURES` environment variable accepts comma-separated bundles:
- `core` - Basic world simulation
- `social` - NPC interactions and dialogue
- `worldfull` - Complete world features
- `all` - Everything enabled

## Performance Tuning

### Memory Management
- World chunks are loaded on-demand and unloaded when inactive
- NPC states are persisted to disk automatically
- Use `SANDBOX_WORLD_FAST=1` for reduced memory footprint

### CPU Optimization
- Parallel processing enabled by default for multi-core systems
- Set `SANDBOX_USE_PARALLELISM=0` to disable if experiencing issues
- Fast mode reduces computational complexity significantly

## Development Settings

### VS Code Integration
- Automatic formatting with Black on save
- Type checking with MyPy
- Linting with Flake8
- Custom tasks for common operations

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test category
python -m pytest tests/population/ -v

# Run with coverage
python -m pytest tests/ --cov=.
```

## File Organization

### Important Directories
- `artifacts/models/` - Trained RL models
- `artifacts/plots/` - Generated visualizations
- `artifacts/data/` - Analysis data and logs
- `docs/` - Documentation files
- `world_data/` - Generated world chunks (auto-created)
- `persistence/` - Saved simulation state (auto-created)

### Key Files
- `main.py` - Main entry point
- `core_sim.py` - Core simulation engine
- `PROJECT_REQUIREMENTS.md` - Detailed requirements
- `pyproject.toml` - Modern Python project configuration
- `requirements.txt` - Python dependencies

## Troubleshooting

### Common Issues
1. **Memory errors**: Enable `SANDBOX_WORLD_FAST=1`
2. **Slow performance**: Check `SANDBOX_USE_PARALLELISM=1`
3. **Import errors**: Ensure dependencies are installed with `pip install -r requirements.txt`
4. **Path issues**: Use absolute paths or ensure working directory is project root

### Debug Mode
Set `SANDBOX_LOG_LEVEL=DEBUG` for detailed logging output.

---
*Last updated: September 16, 2025*