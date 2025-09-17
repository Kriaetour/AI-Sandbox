# AI Sandbox Simulation

An autonomous, procedurally generated world simulation where NPCs form tribal societies, engage in diplomacy, and create emergent behaviors and narratives over time.

## 🌟 Key Features

### World Generation & Management
- **Infinite Chunk-Based World**: Virtually unlimited world size with efficient memory management
- **20 Diverse Biomes**: Procedural terrain using Perlin noise including Plains, Forest, Mountains, Desert, Water, Swamp, Tundra, Jungle, Hills, Valley, Canyon, Coastal, Island, Volcanic, Savanna, Taiga, Steppe, Badlands, Glacier, and Oasis
- **Deterministic Generation**: Reproducible worlds from seeds with seamless chunk transitions
- **Persistent Evolution**: Automatic saving/loading of world state across sessions
- **Global Clock System**: Hierarchical time tracking with minutes, hours, days, seasons, and years
- **Seasonal Resource System**: Four seasons (Spring/Summer/Autumn/Winter) with different resource yields affecting tribal economics

### Seasonal Dynamics
- **Spring**: Growth season with increased plant resources (×1.2 multiplier)
- **Summer**: Abundance season with peak resource production (plant ×1.5, animal ×1.3)
- **Autumn**: Harvest season with moderate yields (plant ×1.1, animal ×1.2)
- **Winter**: Scarcity season with severely reduced resources (plant ×0.3, animal ×0.7)

### Cultural Development System 🆕
- **Multi-Dimensional Culture**: Language evolution, artistic traditions, culinary innovation, architectural development, social structure evolution
- **Cultural Exchange**: Geographic proximity-based knowledge sharing between tribes
- **Tribal Identity**: Each tribe develops unique cultural characteristics and traditions
- **Cultural Persistence**: Cultural data saved/loaded across simulation sessions

### Individual NPC Ambition System 🆕
- **Personal Goals**: NPCs develop ambitions beyond basic survival (leadership, resource hoarding, exploration, social status, alliance building)
- **Internal Conflicts**: Rivalries, alliances, and betrayals create tribal politics
- **Social Dynamics**: Individual agency creates emergent power struggles within tribes
- **Progress Tracking**: NPCs advance toward their personal goals over time

### Advanced AI Systems
- **Reinforcement Learning**: Q-learning agents for population control and tribal diplomacy
- **Optimal Model Selection**: Systematic comparison of 11 trained models for best performance
- **Real-Time Integration**: AI agents make decisions during live simulation
- **Adaptive Behavior**: NPCs learn optimal strategies through experience

### Social & Diplomatic Systems
- **Tribal Societies**: NPCs form complex social groups with leadership hierarchies
- **Diplomatic Relations**: Trust-based relationships with negotiation and alliance systems
- **Cultural Exchange**: Tribes share knowledge, traditions, and innovations
- **Memory Systems**: NPCs maintain grudges and collective faction memories
- **Emergent Behavior**: Complex social dynamics arise from individual NPC interactions

### Technical Excellence
- **Population Stability**: Conservative reproduction preventing exponential growth
- **Resource Balance**: Sustainable economics with linear growth patterns
- **Performance**: ~95-115 ticks/second simulation speed
- **Scalability**: Tested with 300+ NPCs across multiple factions
- **Reliability**: Comprehensive error handling and optional parallelism

## 📚 Documentation

### Technical Reports
- **[Latest Technical Report (v3.0)](docs/AI_Sandbox_Technical_Report_v3.md)**: Comprehensive overview of cultural development and ambition systems
- **[Version History](CHANGELOG.md)**: Complete changelog showing project evolution
- **[Technical Report v2.0](docs/AI_Sandbox_Technical_Report_v2.md)**: Population stability and RL optimization details
- **[Original Technical Report](docs/AI_Sandbox_Technical_Report.md)**: Foundation systems and architecture

### Key Documents
- **[Project Requirements](PROJECT_REQUIREMENTS.md)**: Detailed technical and functional specifications
- **[Configuration Guide](CONFIG.md)**: Environment variables and customization options
- **[Core Simulation Updates](CORE_SIM_BALANCE_UPDATES.md)**: Balance parameter documentation

## 🚀 Quick Start

### Web Visualization
```bash
# Method 1: Run API server separately (recommended)
python run_api_server.py &

# Then start simulation in another terminal
python core_sim.py 1000

# Method 2: Run simulation with integrated API (may have threading issues)
python core_sim.py 1000

# Open visualization
# Open index.html in any modern web browser
```

### Cultural Development
```bash
# Run cultural evolution simulation
python cultural_development.py --tribes 6 --generations 30 --cultural-exchange-rate 0.4

# Test ambition system
python test_ambition_system.py
```

### RL Training
```bash
# Train population control agent
python train_rl_agent.py

# Compare trained models
python compare_qtable_models.py
```

## 📊 Performance Benchmarks

- **Simulation Speed**: ~95-115 ticks/second
- **Population Stability**: 330-350 NPCs over 5000+ ticks
- **Resource Balance**: 2.4x production-to-consumption ratio
- **Cultural Evolution**: 30 generations with 6 tribes

## 🌐 Web Visualization API 🆕

### Real-Time Data Access
The AI Sandbox now includes a Flask-based REST API for real-time web visualization:

- **Live Simulation Data**: Access current tick, season, population, and resource statistics
- **NPC Information**: Get detailed data about all active NPCs including position, faction, health, age, and ambitions
- **Faction Overview**: Retrieve faction territories, resources, relationships, and cultural data
- **Chunk Terrain**: Access terrain and resource data for active world chunks

### API Endpoints
```bash
# Get current world state
GET http://localhost:5000/world_state

# Returns JSON with:
{
  "tick": 100,
  "season": "Spring",
  "population": 57,
  "total_food": 119.4,
  "npcs": [...],      // Array of NPC data
  "factions": [...],  // Array of faction data
  "chunks": [...]     // Array of chunk data
}
```

### Integration
The API runs automatically with the core simulation:
```bash
# API starts on port 5000 alongside simulation
python core_sim.py 1000
```

### Data Structure
- **NPCs**: ID, name, coordinates, faction, health, age, ambition type/progress, traits
- **Factions**: ID, name, population, territory count, resources, relationships
- **Chunks**: Coordinates, terrain type, resources, settlement status, active NPCs

### Use Cases
- **Web Dashboards**: Build real-time monitoring interfaces
- **Data Visualization**: Create charts and graphs of simulation metrics
- **External Tools**: Integrate with analysis software or other applications
- **Debugging**: Monitor simulation state during development
- **RL Performance**: 81% population growth improvement
- **Memory Usage**: <100MB for large-scale simulations

## 🏗️ Architecture

### Core Systems
- **World Engine**: Infinite chunk-based world with procedural generation
- **Population System**: Stable demographics with wave cycles
- **Cultural System**: Multi-dimensional tribal development
- **Ambition System**: Individual NPC goal pursuit
- **RL Integration**: Q-learning agents for optimization
- **Persistence**: JSON-based world and cultural data storage

### Key Technologies
- **Python 3.8+**: Core simulation engine
- **Reinforcement Learning**: Q-learning for population control
- **Procedural Generation**: Perlin noise for terrain
- **Parallel Processing**: Optional ThreadPoolExecutor
- **JSON Persistence**: Cross-session data continuity

## 🎯 Use Cases

- **AI Research**: Emergent behavior and social simulation studies
- **Game Development**: Procedural world generation and NPC AI
- **Academic Research**: Population dynamics and cultural evolution
- **Entertainment**: Interactive world simulation and storytelling
- **Technical Demonstration**: Advanced AI and simulation capabilities

## 📈 Version History

### v3.0 (Current) - Cultural & Ambition Enhancement
- ✅ Multi-dimensional cultural development system
- ✅ Individual NPC ambition and internal conflicts
- ✅ Cultural exchange networks
- ✅ Enhanced tribal social dynamics

### v2.1 - AI Optimization
- ✅ Advanced RL with optimal model selection
- ✅ 81% population growth improvement
- ✅ Multi-range training system

### v2.0 - Population Stability
- ✅ Conservative reproduction parameters
- ✅ Resource balance stabilization
- ✅ 5000+ tick stability validation

### v1.0 - Foundation
- ✅ RL integration and tribal diplomacy
- ✅ Project restructuring and documentation
- ✅ VS Code development environment

---

*AI Sandbox v3.0 - Where individual ambitions shape tribal destinies through cultural evolution and emergent social complexity.*

### NPC & AI Systems
- **Autonomous NPCs**: AI-driven characters with decision-making, movement, and social behaviors
- **Terrain-Influenced Activities**: NPCs adapt behaviors to biome types (fishing in water, hunting in forests, etc.)
- **Memory Systems**: Personal and faction memories influencing decisions and relationships
- **Social Interactions**: Context-aware dialogue based on faction relationships and history

### Tribal Society System
- **Cultural Evolution**: Dynamic traditions, music styles, totems, and spiritual beliefs
- **Role-Based Structures**: Leaders, shamans, warriors, and other specialized roles
- **Economic Specialization**: Tribes focus on fishing, farming, gathering, or trade
- **Population Management**: Birth/death cycles with recruitment and spawning systems

### Diplomacy & Social Dynamics
- **Proactive Negotiations**: Tribes autonomously initiate diplomacy based on needs
- **Reputation System**: Trust levels evolve through interactions affecting future relations
- **Complex Alliances**: Trade agreements, military alliances, peace treaties, and territorial disputes
- **Memory-Driven Behavior**: Grudges and historical events influence diplomatic decisions

### Advanced Features
- **Dual Logging System**: Comprehensive event tracking in `log.txt` and `communication_log.txt`
- **Performance Profiling**: cProfile integration for optimization analysis
- **Multiple Simulation Modes**: Fixed-tick batch processing or continuous interactive mode
- **Faction Territory Management**: Dynamic claims, resource control, and conflict resolution
- **Gemini AI Integration**: Optional LLM-powered narrative generation (requires `GOOGLE_API_KEY`)

## 🧠 Reinforcement Learning Systems

The AI Sandbox features sophisticated RL agents that learn optimal strategies for tribal management and diplomacy.

### Population Control RL
**Q-Learning Agent** for maintaining stable tribal populations through birth/death rate optimization.

- **State Space**: Current population, target population, resource levels, seasonal factors
- **Actions**: Adjust birth rates, death rates, recruitment policies
- **Reward Function**: Population stability, resource efficiency, growth sustainability
- **Training**: Multiple population targets (50, 100, 300, 500, 1000+ members)
- **Performance**: 95%+ success rate in maintaining target populations

### Tribal Diplomacy RL
**Advanced Q-Learning Agent** for strategic tribal diplomatic decision-making.

- **State Space**: Tribal relationships, population sizes, resource distributions, diplomatic history
- **Actions**: 
  - `propose_alliance` - Form cooperative partnerships (+1.0 reward)
  - `declare_rivalry` - Express hostility (-0.4 penalty)
  - `mediate_conflict` - Resolve disputes (+0.15 reward when successful)
  - `form_trade_agreement` - Establish economic cooperation (+0.25 reward)
  - `diplomacy_noop` - Maintain status quo (0.0 reward)
- **Reward Function**: Overall diplomatic stability and cooperation across all tribes
- **Training Results**: 98.5% success rate, 1.79 average reward per episode
- **Learned Strategy**: Prioritizes trade agreements and alliances over conflict

### RL Training & Usage

#### Training Population RL
```bash
# Train for specific population target
python train_rl_agent.py --target-pop 300 --episodes 200

# Train with custom parameters
python train_rl_agent.py --episodes 500 --epsilon-decay 0.99 --save_path artifacts/models/qtable_custom.json
```

#### Training Diplomacy RL
```bash
# Basic training
python train_diplomacy_rl.py --episodes 100 --max-ticks 300

# Advanced training with custom parameters
python train_diplomacy_rl.py --episodes 200 --epsilon-start 0.5 --save-q artifacts/models/qtable_diplomacy_custom.json
```

#### Interactive Training Menu
```bash
python main.py
# Select option 3: "Population RL Training"
# Select option 4: "Diplomacy RL Training"
```

### RL Model Files
- **`artifacts/models/qtable.json`**: Primary population control model
- **`artifacts/models/qtable_combined.json`**: Multi-target population model
- **`artifacts/models/qtable_diplomacy_complete.json`**: Trained diplomacy model
- **`artifacts/models/qtable_pop_*.json`**: Population-specific models (50, 100, 300, 500, 1000 targets)

### RL Architecture
- **Algorithm**: Q-Learning with ε-greedy exploration
- **State Discretization**: Continuous → Discrete state mapping
- **Experience Replay**: Memory buffer for stable learning
- **Hyperparameters**: 
  - Learning Rate: 0.1
  - Discount Factor: 0.95
  - Exploration Decay: 0.995
- **Performance Monitoring**: Real-time metrics and training statistics

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Dependencies: `noise`, `tqdm`

### Installation
```bash
# Clone or download the project
cd "AI Sandbox"

# (Optional) Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Unix/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Simulation (Unified CLI + Interactive Menu)
Running with no arguments launches an interactive menu:
```bash
python main.py
```
You can still use explicit subcommands for automation:
```bash
# Core balanced long-run simulation (default 1000 ticks)
python main.py core 1500

# Tribal-only dynamics
python main.py tribal --ticks 300

# Combined tribal + social (profiling integrated)
python main.py combined --ticks 400

# Territory persistence demo
python main.py territory

# Social interaction showcase (dialogue focus)
python main.py social --ticks 80

# Legacy interactive menu (deprecated)
python main.py menu
```

Use `--log DEBUG|INFO|WARNING|ERROR` to control console verbosity (file logging always captures DEBUG). Example:
```bash
python main.py --log DEBUG core 500
```

If no subcommand is provided, the interactive menu starts (use `menu` subcommand explicitly if desired).

### Notes
- Interactive menu is now the default launch path.
- Direct execution of `core_sim.py` is deprecated; use `python main.py core` instead.
- Persistence artifacts and adaptation exports retain previous locations.
- See `ARCHIVE.md` for legacy file removals and rationale.

## 📁 Project Structure

```
AI Sandbox/
├── main.py                 # Main entry point with profiling
├── core_sim.py            # Core simulation engine
├── train_rl_agent.py      # Population RL training script
├── train_diplomacy_rl.py  # Diplomacy RL training script
├── rl_agent.py            # Population RL agent implementation
├── rl_diplomacy_agent.py  # Diplomacy RL agent implementation
├── rl_diplomacy_interface.py # Diplomacy RL state/action interface
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Modern Python project configuration
├── .gitignore            # Git ignore rules
├── PROJECT_REQUIREMENTS.md # Detailed project requirements
├── README.md             # This file
├── artifacts/            # Generated artifacts (not in git)
│   ├── plots/           # Visualization outputs
│   ├── models/          # Trained RL models
│   └── data/            # Analysis data files
├── docs/                # Documentation
│   ├── AI_Sandbox_Technical_Report.md
│   ├── RL_DESIGN.md
│   └── ARCHIVE.md
├── world/               # World generation system
│   ├── engine.py       # Core world engine
│   ├── chunk.py        # Chunk management
│   └── terrain.py      # 20 biome definitions
├── npcs/                # NPC system
│   └── npc.py          # NPC behavior & AI
├── factions/           # Faction system
│   └── faction.py      # Faction management
├── tribes/             # Tribal society system
│   ├── tribal_manager.py # Main tribal coordinator
│   ├── tribe.py        # Individual tribe management
│   ├── tribal_communication.py
│   ├── tribal_conflict.py
│   ├── tribal_diplomacy.py
```

### Web Visualization Advanced Usage

Two deployment modes exist for the experimental web viewer:

1. External API server (recommended for stability):
```powershell
python run_api_server.py
# New terminal
$env:SANDBOX_NO_INTERNAL_API=1; python core_sim.py 1000
```
Open `index.html` in a browser (no server required for the static file). When finished, clear the variable:
```powershell
Remove-Item Env:SANDBOX_NO_INTERNAL_API
```

2. Internal thread mode (legacy / quick test):
```powershell
python core_sim.py 500
```
The simulation starts the API automatically unless `SANDBOX_NO_INTERNAL_API` is set.

Health & diagnostics:
- `/health` returns JSON with `last_updated` timestamp and age.
- Viewer marks `Connected (stale Xs)` if no update within 3s.
- World state saved atomically to `world_state.json` every 10 ticks.

If you see stats updating but status shows Disconnected:
1. Multiple Python processes may be fighting for port 5000. Run:
```powershell
netstat -ano | findstr 5000
```
Terminate stray PIDs with Task Manager or:
```powershell
taskkill /PID <pid> /F
```
2. Browser caching: Hard refresh (Ctrl+F5) to reload `visualizer.js`.
3. Stale file writes: Ensure simulation still running; `tick` should advance. If finished, status may go stale after 3s.

NPC overlap note: Early ticks spawn everyone in a single chunk. Jitter rendering prevents total overlap; once movement / multi-chunk activation expands, spatial distribution improves.

Optional visual-only movement (does not affect simulation logic):
```powershell
$env:SANDBOX_VISUAL_MOVEMENT=1; python core_sim.py 400
```
This applies a lightweight random walk to serialized NPC coordinates prior to saving `world_state.json` so the map shows dispersion. Remove afterward with:
```powershell
Remove-Item Env:SANDBOX_VISUAL_MOVEMENT
```

│   ├── tribal_politics.py
│   ├── tribal_roles.py
│   ├── tribal_structures.py
│   └── __pycache__/
├── persistence/        # Data persistence
│   ├── factions.json   # Faction state
│   └── chunks/         # World chunk data
└── world_data/         # Generated world data
    └── chunks/         # Chunk files
```

## 🎮 Simulation Modes

### Fixed-Tick Mode
Runs for a predetermined number of ticks with progress tracking and comprehensive logging.

### Continuous Mode
Runs indefinitely with real-time controls for interactive monitoring and experimentation.

## 📊 Emergent Behaviors

The simulation creates complex emergent narratives through:
- **Faction Wars & Alliances**: Memory-driven conflicts and diplomatic relationships
- **Cultural Evolution**: Tribes develop unique traditions and beliefs
- **Economic Networks**: Inter-tribal trade and resource specialization
- **Social Dynamics**: Trust, grudges, and relationship evolution
- **Population Cycles**: Birth, death, recruitment, and migration patterns

## 🔧 Technical Details

- **Architecture**: Modular, object-oriented design
- **Performance**: Efficient chunk loading with bounded memory usage
- **Persistence**: JSON-based serialization for cross-session continuity
- **Logging**: Dual-log system for comprehensive event analysis
- **Profiling**: cProfile integration for performance optimization

## 📈 Development Status

### ✅ Completed Features
- 20-biome procedural terrain generation
- Autonomous NPC behavior with terrain adaptation
- Full tribal society system with cultural evolution
- Advanced multi-faction diplomacy
- Reputation and memory-driven social interactions
- Comprehensive logging and analytics
- Performance profiling and optimization
- Persistence layer with JSON serialization
- Multiple simulation modes
- Global Clock System with time tracking
- Seasonal Resource System with economic challenges

### 🔄 Planned Enhancements
- Advanced AI decision-making algorithms
- Resource management and economics
- Combat and conflict resolution systems
- Technology progression mechanics
- Multi-threaded simulation processing
- Web-based visualization interface

## 📚 Documentation

- **[PROJECT_REQUIREMENTS.md](PROJECT_REQUIREMENTS.md)** - Detailed project requirements and objectives
- **[CONFIG.md](CONFIG.md)** - Configuration options and environment variables
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and recent changes
- **[docs/AI_Sandbox_Technical_Report.md](docs/AI_Sandbox_Technical_Report.md)** - Comprehensive technical documentation
- **[docs/](docs/)** - Additional technical reports and archived documentation

## 🤝 Contributing

This project is in active development. Contributions are welcome! Please ensure code follows the established patterns and includes appropriate documentation.

## 📄 License

This project is open-source. See individual files for license information.

---

## 📚 Databank Module (Cultural Pools)

Centralized `databank.py` provides up to 100 pre-seeded entries per category (names, sayings, spirit guides, titles, epithets) with runtime extension.

### Newly Added Categories
The databank now also seeds and tracks:
- `music_styles` – Performative cultural sound patterns (used for tribe flavor)
- `rumors` – Ambient world speculation pool powering `generate_rumor`
- `seasonal_rituals` – Operational / ceremonial maintenance and symbolic cycle rites
- `creation_myths` – Deep identity narratives selectable during tribe generation
- `tribe_prefixes` / `tribe_suffixes` – Modular components for dynamic tribe naming

All of these are persisted and modifiable just like existing pools. If a category is empty or removed, generation code falls back to minimal legacy defaults to stay resilient.

Features:
- JSON persistence at `persistence/databank.json` (auto-saves on mutation)
- Weighted rarity tiers (see table below) influencing random selection probability
- Tagging and predicate-filtered retrieval for contextual selection
- Tribe-biased name mutation using emerging lexicon syllables
- Optional epithet attachment during recruit generation
- Modular expansion without code edits (categories are auto-created on first `add_entry`)

### Rarity Weighting
When calling `get_random`, entries are internally normalized and weights applied:

| Rarity     | Weight Multiplier | Approx. Relative Chance* |
|------------|-------------------|---------------------------|
| common     | 1.0               | Baseline (reference)      |
| uncommon   | 2.0               | ~2× common                |
| rare       | 4.0               | ~4× common                |
| legendary  | 7.0               | ~7× common                |

*Relative chance is proportional within the sampled pool after predicate filtering.

Example rarity assignment:
```python
db.set_rarity('creation_myths', 'cast from reflection of inverted dawn', 'rare')
db.set_rarity('rumors', 'An envoy returned speaking in borrowed dialect.', 'uncommon')
```

### Tagging & Filtering
Tags allow semantic grouping:
```python
db.tag_entry('rumors', 'Stone listeners heard hollow thunder underground.', 'geologic')
db.tag_entry('creation_myths', 'forged from alloy of eight sworn pacts', 'foundational')

# Fetch only foundational myths
myths = db.get_random('creation_myths', count=3, predicate=lambda e: 'foundational' in e['tags'])
```

### New Integration Points
- Tribe generation pulls: `music_styles`, `seasonal_rituals`, `creation_myths`, `tribe_prefixes`, `tribe_suffixes`, `spirit_guides`
- `generate_rumor` now sources weighted entries from `rumors`
- `generate_saying` unified through `sayings` pool

### Custom Mod / Modding Notes
1. Stop the simulation before editing `persistence/databank.json` manually.
2. Maintain structure: each entry object requires at least `text`. Optional: `rarity`, `tags`.
3. To add a brand-new category via code:
    ```python
    db.add_entry('beacon_patterns', 'triple ascending pulse', rarity='uncommon', tags=['signal'])
    ```
4. To purge a category, remove its key from the JSON; it will recreate empty on next access.

Usage Examples:
```python
from databank import get_databank
db = get_databank()

# Get one random weighted name
name = db.get_random('names')[0]  # rarity influences probability

# Get 5 unique sayings
sayings = db.get_random('sayings', count=5)

# Add a new ritual epithet (if capacity not exceeded)
db.add_entry('epithets', 'the Storm-Forged', rarity='rare', tags=['ceremony'])

# List categories
print(db.list_categories())
```
Integration Points:
- Recruitment uses weighted names + optional epithet
- `generate_saying` uses sayings pool (centralized)
- `generate_rumor` uses `rumors` pool
- Prophecy expands spirit guide roster if thin
- Lexicon-derived syllables influence new tribal names
- Tribe generation draws music style, seasonal ritual, creation myth, and guide

Extending:
```python
db.add_entry('spirit_guides', 'Crystal Lynx')
```
Entries are capped by `max_entries_per_category` (default 100) and duplicates are ignored.

**Date**: September 13, 2025  
**Version**: Development Build  
**Maintainer**: AI Sandbox Development Team
---

## 🤖 RL API & Training Integration

The AI Sandbox provides a modular RL (Reinforcement Learning) API for research and experimentation. RL agents can observe world state, take high-level social actions, and receive shaped rewards for guiding emergent social, demographic, and cultural outcomes.

### RL State Features
- **Opinion Matrix/Stats**: Faction-faction opinions, mean/min/max, allies/hostiles counts
- **Rumor Stats**: Per-faction rumor count, age, diversity, spread
- **Saying Stats**: Per-faction saying count, diversity, recency
- **Demographics**: Population, births, deaths, event rates

Access via:
```python
from rl_env_state import get_rl_env_state
state = get_rl_env_state(world)
```

### RL Actions
- **Opinion Actions**: `gift`, `insult`, `mediate`, `propaganda`, `multi_mediation`
- **Rumor Actions**: `inject_rumor`, `suppress_rumor`, `spread_rumor`, `targeted_rumor_campaign`
- **Saying Actions**: `inject_saying`, `suppress_saying`

Example:
```python
from rl_opinion_interface import rl_social_action
rl_social_action(world, 'gift', source='TribeA', target='TribeB')

from rl_rumor_interface import inject_rumor
inject_rumor(world, 'TribeA', text='A new star appeared.')
```

All RL actions are logged to `rl_actions.log` for analytics/debugging.

### RL Reward Shaping
Combine social, rumor, saying, and demographic metrics with custom weights:
```python
from rl_reward_shaping import compute_shaped_reward
reward = compute_shaped_reward(world, weights={
    'cohesion': 1.0, 'allies': 0.5, 'hostiles': -0.5, 'rumor': 0.3, 'saying': 0.3,
    'pop_stability': 0.2, 'deaths': -0.2, 'births': 0.1
})
```

### RL Analytics
- All RL actions are logged to `rl_actions.log` (see Python logging setup in `rl_opinion_interface.py` and `rl_rumor_interface.py`).
- Reward components can be tracked per tick for debugging and analysis.

### RL Training Script
To train a simple Q-learning agent on population stability:
```bash
python rl_agent.py
```
Or, for multi-episode training with epsilon decay and Q-table saving:
```python
from rl_agent import run_rl_training
run_rl_training(episodes=20, max_ticks=500, save_path='qtable.json')
```
See `rl_agent.py` for agent and environment details. You can extend the agent to use richer RL state, actions, and reward signals as needed.

---