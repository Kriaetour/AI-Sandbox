def test_population_rl_agent_load():
    from rl_agent import TabularQLearningAgent, ACTION_NAMES
    agent = TabularQLearningAgent(num_actions=len(ACTION_NAMES), epsilon=0.0, lr=0.0, gamma=0.95)
    # Should be able to select an action from a dummy state
    state = {'population': 10, 'food': 1000, 'births': 1, 'deaths_starv': 0, 'deaths_nat': 0}
    action = agent.select_action(state)
    assert isinstance(action, int)
