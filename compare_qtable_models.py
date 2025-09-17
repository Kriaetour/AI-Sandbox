#!/usr/bin/env python3
"""
Q-Table Model Comparison Script

Tests different trained Q-table models in live simulation to determine
which performs best for population control.
"""

import json
import time
import random
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse

from world.engine import WorldEngine
from tribes.tribal_manager import TribalManager
from tribes.tribe import TribalRole
from world import WeatherManager
from rl_live_integration import RLAgentManager
from core_sim import setup_dialogue_logger
from factions.faction import Faction


class QTableComparator:
    """Compares performance of different Q-table models in live simulation."""

    def __init__(self, model_dir: str = "artifacts/models"):
        self.model_dir = Path(model_dir)
        self.results = {}

        # Setup logging
        self.logger = logging.getLogger(__name__)
        setup_dialogue_logger()

    def get_available_qtables(self) -> List[Path]:
        """Get list of available Q-table files."""
        qtable_files = list(self.model_dir.glob("qtable_pop_*.json"))
        qtable_files.append(self.model_dir / "population_qtable.json")  # Include main one
        return [f for f in qtable_files if f.exists()]

    def load_qtable_info(self, qtable_path: Path) -> Dict[str, Any]:
        """Load Q-table and extract metadata."""
        try:
            with open(qtable_path, 'r') as f:
                qtable = json.load(f)

            states = len(qtable)
            max_q = 0
            min_q = float('inf')
            unexplored = 0

            for state_key, q_values in qtable.items():
                if isinstance(q_values, list):
                    state_max = max(q_values) if q_values else 0
                    state_min = min(q_values) if q_values else 0
                    if all(q == 0 for q in q_values):
                        unexplored += 1
                else:
                    state_max = q_values
                    state_min = q_values

                max_q = max(max_q, state_max)
                min_q = min(min_q, state_min)

            return {
                'path': qtable_path,
                'states': states,
                'max_q': max_q,
                'min_q': min_q,
                'unexplored_actions': unexplored,
                'explored_ratio': (states - unexplored) / states if states > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"Error loading {qtable_path}: {e}")
            return None

    def run_simulation_with_model(self, qtable_path: Path, num_ticks: int = 500) -> Dict[str, Any]:
        """Run live simulation with specific Q-table model."""
        self.logger.info(f"🧪 Testing model: {qtable_path.name}")

        # Clear any existing persistence
        from main import clear_persistence
        clear_persistence()

        # Initialize world
        world_seed = 42  # Use fixed seed for fair comparison
        world = WorldEngine(seed=world_seed)

        # Initialize tribal system
        tribal_manager = TribalManager()
        weather_manager = WeatherManager(world)

        # Create initial tribes and NPCs
        from main import TribeGenerator
        tribe_generator = TribeGenerator()

        # Create 3-4 tribes with moderate population
        num_tribes = 3
        all_npcs = []

        for i in range(num_tribes):
            location = (random.randint(-10, 10), random.randint(-10, 10))
            tribe_config = tribe_generator.generate_tribe_config(location)
            tribe_name = tribe_config["name"]
            founder_id = f"founder_{tribe_name.lower().replace(' ', '_')}"

            # Create tribe
            tribe = tribal_manager.create_tribe(tribe_name, founder_id, location)
            tribe.economic_specialization = tribe_config["specialization"]

            # Create faction
            if tribe_name not in world.factions:
                world.factions[tribe_name] = Faction(name=tribe_name, territory=[location])

            # Add 3-5 NPCs per tribe
            num_members = random.randint(3, 5)
            for j in range(num_members):
                member_id = f"{tribe_name.lower().replace(' ', '_')}_member_{j}"
                npc_name = f"{tribe_name[:3]}{j}"

                from npcs.npc import NPC
                npc = NPC(name=npc_name, coordinates=location, faction_id=tribe_name)

                # Add to systems
                role = random.choice(list(TribalRole))
                tribal_manager.tribes[tribe_name].add_member(member_id, role)
                world.factions[tribe_name].add_member(npc.name)

                # Add to world
                chunk = world.get_chunk(location[0], location[1])
                chunk.npcs.append(npc)
                all_npcs.append(npc)

            # Activate chunks
            world.activate_chunk(location[0], location[1])
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    world.activate_chunk(location[0] + dx, location[1] + dy)

        # Initialize RL with specific model
        rl_manager = RLAgentManager()
        success = rl_manager.load_population_agent(qtable_path)

        if not success:
            self.logger.error(f"Failed to load model {qtable_path}")
            return None

        # Attach to world
        world.rl_agent_manager = rl_manager

        # Track metrics
        population_history = []
        food_history = []
        rl_actions = []
        stability_score = 0

        # Run simulation
        start_time = time.time()

        for tick in range(num_ticks):
            # Process systems
            tribal_manager.process_tribal_dynamics(world)
            world.world_tick()
            weather_manager.update_weather(world.current_hour)

            # RL decisions
            if rl_manager.should_make_decision(tick):
                actions = rl_manager.make_rl_decisions(world)
                rl_actions.extend(actions)

            # Track metrics every 10 ticks
            if tick % 10 == 0:
                current_pop = sum(len(ch.npcs) for ch in world.active_chunks.values())
                total_food = sum(ch.resources.get("food", 0) for ch in world.active_chunks.values())

                population_history.append(current_pop)
                food_history.append(total_food)

                # Calculate stability (lower variance = higher stability)
                if len(population_history) > 5:
                    recent_pop = population_history[-5:]
                    variance = sum((x - sum(recent_pop)/len(recent_pop))**2 for x in recent_pop) / len(recent_pop)
                    stability_score += (1000 / (1 + variance))  # Higher score for lower variance

        end_time = time.time()

        # Calculate final metrics
        avg_population = sum(population_history) / len(population_history) if population_history else 0
        avg_food = sum(food_history) / len(food_history) if food_history else 0
        final_population = population_history[-1] if population_history else 0
        final_food = food_history[-1] if food_history else 0

        # Population stability (coefficient of variation)
        if len(population_history) > 1:
            pop_mean = sum(population_history) / len(population_history)
            pop_variance = sum((x - pop_mean)**2 for x in population_history) / len(population_history)
            pop_stability = (pop_variance ** 0.5) / pop_mean if pop_mean > 0 else float('inf')
        else:
            pop_stability = float('inf')

        # Performance score (higher is better)
        performance_score = (
            (avg_population * 0.3) +           # Population size
            ((1000 / (1 + pop_stability)) * 0.4) +  # Stability
            (len(rl_actions) * 0.2) +          # Decision activity
            ((num_ticks / (end_time - start_time)) * 0.1)  # Speed
        )

        result = {
            'model_name': qtable_path.name,
            'ticks': num_ticks,
            'duration': end_time - start_time,
            'avg_population': avg_population,
            'final_population': final_population,
            'avg_food': avg_food,
            'final_food': final_food,
            'population_stability': pop_stability,
            'rl_actions_count': len(rl_actions),
            'performance_score': performance_score,
            'population_history': population_history,
            'rl_actions': rl_actions[:10]  # First 10 actions as sample
        }

        self.logger.info(f"✅ Model {qtable_path.name} test complete")
        self.logger.info(f"   Performance Score: {performance_score:.1f}")
        self.logger.info(f"   Avg Population: {avg_population:.1f}")
        self.logger.info(f"   Stability: {pop_stability:.3f}")
        self.logger.info(f"   RL Actions: {len(rl_actions)}")

        return result

    def compare_models(self, num_ticks: int = 500) -> Dict[str, Any]:
        """Compare all available Q-table models."""
        self.logger.info("🔍 Starting Q-table model comparison...")

        available_models = self.get_available_qtables()
        self.logger.info(f"Found {len(available_models)} Q-table models to test")

        # Load model metadata
        model_info = {}
        for model_path in available_models:
            info = self.load_qtable_info(model_path)
            if info:
                model_info[model_path.name] = info

        # Test each model
        results = {}
        for model_path in available_models:
            result = self.run_simulation_with_model(model_path, num_ticks)
            if result:
                results[model_path.name] = result

        # Generate comparison report
        comparison = self._generate_comparison_report(results, model_info)

        return {
            'results': results,
            'model_info': model_info,
            'comparison': comparison
        }

    def _generate_comparison_report(self, results: Dict, model_info: Dict) -> Dict[str, Any]:
        """Generate detailed comparison report."""
        if not results:
            return {'error': 'No results to compare'}

        # Sort by performance score
        sorted_results = sorted(results.items(), key=lambda x: x[1]['performance_score'], reverse=True)

        best_model = sorted_results[0][0]
        best_score = sorted_results[0][1]['performance_score']

        # Calculate averages
        avg_scores = {}
        metrics = ['avg_population', 'population_stability', 'rl_actions_count', 'performance_score']

        for metric in metrics:
            values = [r[metric] for r in results.values() if r[metric] != float('inf')]
            avg_scores[metric] = sum(values) / len(values) if values else 0

        return {
            'best_model': best_model,
            'best_score': best_score,
            'ranked_models': [name for name, _ in sorted_results],
            'averages': avg_scores,
            'total_models_tested': len(results)
        }


def main():
    parser = argparse.ArgumentParser(description="Compare Q-table models in live simulation")
    parser.add_argument('--ticks', type=int, default=500, help='Number of ticks per simulation')
    parser.add_argument('--output', type=str, default='qtable_comparison.json', help='Output file for results')
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Run comparison
    comparator = QTableComparator()
    comparison_results = comparator.compare_models(args.ticks)

    # Save results
    with open(args.output, 'w') as f:
        # Convert WindowsPath objects to strings for JSON serialization
        def convert_paths(obj):
            if isinstance(obj, dict):
                return {k: convert_paths(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_paths(item) for item in obj]
            elif hasattr(obj, '__class__') and 'Path' in obj.__class__.__name__:
                return str(obj)
            else:
                return obj

        json.dump(convert_paths(comparison_results), f, indent=2)

    # Print summary
    print("\n" + "="*60)
    print("Q-TABLE MODEL COMPARISON RESULTS")
    print("="*60)

    if 'comparison' in comparison_results:
        comp = comparison_results['comparison']
        print(f"Best Model: {comp['best_model']}")
        print(".1f")
        print(f"Models Tested: {comp['total_models_tested']}")
        print("\nTop 3 Models:")
        for i, model in enumerate(comp['ranked_models'][:3], 1):
            if model in comparison_results['results']:
                score = comparison_results['results'][model]['performance_score']
                print(f"{i}. {model}: {score:.1f}")

    print(f"\nDetailed results saved to: {args.output}")


if __name__ == "__main__":
    main()