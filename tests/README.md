# AI Sandbox Test Suite Organization

This directory contains all test files and demo scripts organized by category for better maintainability and easier navigation.

## Directory Structure

```
tests/
├── README.md                 # This file
├── balance/                  # Balance and economy tests
│   ├── test_capacity.py
│   ├── test_consumption.py
│   ├── test_controlled_waves.py
│   ├── test_food_balance.py
│   └── test_wave_multipliers.py
├── demos/                    # Demonstration scripts
│   ├── combat_demo.py
│   ├── databank_demo.py
│   ├── dialogue_persistence_demo.py
│   ├── dialogue_sample_run.py
│   ├── pathfinding_demo.py
│   ├── persistence_demo.py
│   ├── run_tribal_test.py
│   └── tribal_demo.py
├── environmental/           # Environmental AI and weather tests
│   ├── test_daynight.py
│   ├── test_environmental_ai.py
│   └── test_environmental_ai_simple.py
├── integration/             # System integration tests
│   ├── test_complete_markov_integration.py
│   ├── test_integration_verification.py
│   └── test_markov_integration.py
├── markov/                  # Markov chain and dialogue tests
│   ├── test_markov.py
│   ├── test_markov_dialogue.py
│   ├── test_markov_dialogue_integration.py
│   └── test_markov_persistence.py
├── population/              # Population dynamics and stability tests
│   ├── test_long_term_population.py
│   ├── test_population_decline.py
│   ├── test_population_waves.py
│   └── test_simple_population.py
├── specialized/             # Specialized feature tests
│   ├── adaptive_learning_test.py
│   ├── auto_seed_test.py
│   ├── dialogue_persistence_reload_test.py
│   ├── frequency_persistence_test.py
│   ├── logger_test.py
│   ├── repopulate_test.py
│   ├── variation_bigram_test.py
│   └── variation_test.py
└── system/                  # Core system functionality tests
    ├── test_actions.py
    ├── test_demographics.py
    ├── test_npc_safety_bug.py
    └── test_tribal.py
```

## Test Categories

### 🔀 Balance Tests (`balance/`)
Tests related to resource balance, population control, and economic stability:
- **test_food_balance.py**: Validates sustainable food production vs consumption
- **test_capacity.py**: Tests resource capacity and regeneration limits
- **test_consumption.py**: Validates NPC consumption patterns
- **test_controlled_waves.py**: Tests population wave system stability
- **test_wave_multipliers.py**: Validates wave multiplier calculations

### 🎯 Population Tests (`population/`)
Tests focused on population dynamics and long-term stability:
- **test_population_decline.py**: Prevents population collapse scenarios
- **test_long_term_population.py**: Extended stability validation (5000+ ticks)
- **test_simple_population.py**: Basic population growth validation
- **test_population_waves.py**: Population wave system testing

### 🤖 Markov Tests (`markov/`)
Tests for Markov chain dialogue and behavior systems:
- **test_markov.py**: Basic Markov chain functionality
- **test_markov_dialogue.py**: Markov-based dialogue generation
- **test_markov_dialogue_integration.py**: Integration with simulation
- **test_markov_persistence.py**: Persistence of Markov state

### 🔗 Integration Tests (`integration/`)
Tests that validate system-wide integration and interoperability:
- **test_integration_verification.py**: Overall system integration validation
- **test_complete_markov_integration.py**: Full Markov system integration
- **test_markov_integration.py**: Markov chain integration testing

### 🌍 Environmental Tests (`environmental/`)
Tests for environmental AI, weather, and time-based systems:
- **test_environmental_ai.py**: Advanced environmental AI behavior
- **test_environmental_ai_simple.py**: Basic environmental AI testing
- **test_daynight.py**: Day/night cycle functionality

### ⚙️ System Tests (`system/`)
Core system functionality and safety tests:
- **test_tribal.py**: Tribal system functionality
- **test_demographics.py**: Population demographics calculations
- **test_actions.py**: NPC action system validation
- **test_npc_safety_bug.py**: NPC safety and crash prevention

### 🎭 Demo Scripts (`demos/`)
Demonstration scripts for showcasing specific features:
- **tribal_demo.py**: Tribal society system demonstration
- **combat_demo.py**: Combat system demonstration
- **dialogue_sample_run.py**: Dialogue system showcase
- **pathfinding_demo.py**: Pathfinding algorithm demonstration
- **persistence_demo.py**: Data persistence system demo

### 🔬 Specialized Tests (`specialized/`)
Specialized feature tests and experimental functionality:
- **adaptive_learning_test.py**: Adaptive learning system validation
- **variation_test.py**: Text variation system testing
- **logger_test.py**: Logging system validation
- **frequency_persistence_test.py**: Frequency-based persistence testing

## Running Tests

### From Project Root Directory
All tests should be run from the main AI Sandbox directory (one level up from tests/):

```bash
# Run individual test categories
python -m tests.balance.test_food_balance
python -m tests.population.test_long_term_population
python -m tests.integration.test_integration_verification

# Run specific tests
python tests/balance/test_food_balance.py
python tests/population/test_population_decline.py
python tests/demos/tribal_demo.py
```

### Batch Testing
To run multiple tests in a category, use the following commands:

```bash
# Run all balance tests (Windows PowerShell)
Get-ChildItem tests\balance\*.py | ForEach-Object { python $_.FullName }

# Run all population tests
Get-ChildItem tests\population\*.py | ForEach-Object { python $_.FullName }

# Run all demos
Get-ChildItem tests\demos\*.py | ForEach-Object { python $_.FullName }
```

## Test Dependencies

Most tests require the main simulation modules to be available in the parent directory:
- `core_sim.py` - Main simulation engine
- `world/` - World engine and terrain system
- `factions/` - Faction management
- `npcs/` - NPC behavior system
- `tribes/` - Tribal society system

## Important Notes

### Import Path Requirements
⚠️ **Important**: All tests must be run from the main AI Sandbox directory (parent of tests/) to ensure proper import paths. The test files may need import path adjustments if moved.

### Environment Variables
Some tests rely on environment variables for configuration:
- `SANDBOX_USE_PARALLELISM` - Controls ThreadPoolExecutor usage
- `SANDBOX_FEATURES` - Controls which simulation features are enabled
- `DIALOGUE_PRINT_LIMIT` - Limits dialogue output in tests

### Data Files
Tests may create temporary data files in:
- `world_data/` - World chunk persistence
- `persistence/` - Faction and simulation state
- Log files (dialogue.log, log.txt)

## Test Maintenance

### Adding New Tests
1. Place new tests in the appropriate category directory
2. Follow the naming convention: `test_[feature_name].py`
3. Update this README with test descriptions
4. Ensure tests can be run from the project root directory

### Updating Existing Tests
When modifying tests, ensure:
1. Import paths remain valid
2. Test documentation is updated
3. Dependencies are documented
4. Tests continue to work from the project root

## Recommended Test Execution Order

For comprehensive system validation, run tests in this order:

1. **System Tests** - Validate core functionality
2. **Balance Tests** - Ensure economic stability
3. **Population Tests** - Verify population dynamics
4. **Integration Tests** - Test system interoperability
5. **Specialized Tests** - Validate specific features
6. **Demos** - Showcase working features

This organization ensures that fundamental systems are validated before testing more complex integrated behaviors.