#!/usr/bin/env python3
"""
Military RL Integration Test
Quick test to validate the military RL integration works correctly.
"""

def test_integration():
    """Test the military RL integration."""
    print("🧪 MILITARY RL INTEGRATION TEST")
    print("="*50)
    
    try:
        # Test imports
        from military_rl_integration import MilitaryRLController, run_simulation_with_military_rl
        print("✅ Military RL imports successful")
        
        # Test controller initialization
        controller = MilitaryRLController(epsilon=0.0)
        print(f"✅ Controller initialized with {len(controller.agent.q_table)} states")
        
        # Test short simulation
        print("🚀 Running 100-tick test simulation...")
        results = run_simulation_with_military_rl(
            num_ticks=100,
            epsilon=0.0,
            decision_interval=10,
            num_tribes=4,
            verbose=False
        )
        
        print("✅ Test simulation completed successfully!")
        print(f"   Military actions: {results['military_actions']}")
        print(f"   Final tribes: {results['final_tribes']}")
        print(f"   Duration: {results['duration']:.2f}s")
        
        # Performance stats
        stats = results['military_stats']
        print(f"   Avg reward/action: {stats['avg_reward_per_action']:.3f}")
        print(f"   States visited: {stats['states_visited']}")
        
        print("\n🎯 INTEGRATION TEST PASSED!")
        print("✅ Ready for deployment in main application")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_integration()