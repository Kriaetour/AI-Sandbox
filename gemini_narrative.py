# AI Sandbox Gemini Narrative Module
# Uses Google's Gemini AI for generating narrative content

import os
from typing import Any, Optional

# Try to load optional dependencies
try:
    from dotenv import load_dotenv

    # Load environment variables from .env file
    load_dotenv()
except ImportError:
    # Fallback if dotenv is not available
    pass

GENAI_AVAILABLE = False
genai: Any = None
try:
    import google.generativeai as _genai

    genai = _genai
    GENAI_AVAILABLE = True
except ImportError:
    pass

# Configure Gemini API
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL: Optional[Any] = None
if API_KEY and GENAI_AVAILABLE and genai:
    genai.configure(api_key=API_KEY)
    MODEL = genai.GenerativeModel("gemini-1.5-flash")


def _generate_with_gemini(prompt: str) -> str:
    """Generate content using Gemini AI or return fallback."""
    if not MODEL:
        return f"[Gemini unavailable] {prompt[:50]}..."

    try:
        response = MODEL.generate_content(prompt)
        return str(response.text).strip()
    except Exception as e:  # Broad catch for API fallback
        return f"[Gemini error: {e}] {prompt[:50]}..."


def generate_agent_dialogue(npc: Any, context: str) -> str:
    """Generate dialogue for an NPC agent using Gemini AI."""
    prompt = f"""
    Generate a short, natural dialogue line for an NPC named {npc.name}
    in a tribal society simulation.
    Context: {context}
    The dialogue should be appropriate for a tribal member and fit the
    social context.
    Keep it under 50 words.
    """
    return _generate_with_gemini(prompt)


def generate_narrative(world_state: Any) -> str:
    """Generate a narrative summary of the world state."""
    prompt = f"""
    Summarize the current state of this tribal world simulation in 2-3
    sentences.
    Focus on key events, tribal relationships, and overall societal trends.
    World state: {world_state}
    """
    return _generate_with_gemini(prompt)


def generate_rl_training_narrative(episode: int, reward: float) -> str:
    """Generate narrative for RL training progress."""
    prompt = f"""
    Describe the progress of reinforcement learning training for tribal
    population control.
    Episode {episode} achieved reward {reward:.2f}.
    Write 1-2 sentences about what this means for the simulation.
    """
    return _generate_with_gemini(prompt)


def generate_tribe_story(tribe: Any) -> str:
    """Generate a story about a tribe."""
    prompt = f"""
    Write a brief 2-3 sentence story about the tribe {tribe.name}.
    Include their culture, current status, and notable characteristics.
    Tribe info: {getattr(tribe, 'description', 'A tribal society')}
    """
    return _generate_with_gemini(prompt)


def discover_new_concept(tribe: Any) -> str:
    """Discover a new cultural concept."""
    prompt = f"""
    Generate a single word or short phrase representing a new cultural concept
    that could emerge in a tribal society like {tribe.name}.
    Make it meaningful and fitting for tribal culture.
    """
    result = _generate_with_gemini(prompt)
    return result.strip().split()[0] if result else "harmony"


def generate_cultural_borrowing(from_tribe: Any, to_tribe: Any) -> str:
    """Generate cultural borrowing between tribes."""
    prompt = f"""
    Describe how {to_tribe.name} might adopt a cultural element from
    {from_tribe.name}.
    Write 1-2 sentences about this cultural exchange.
    """
    return _generate_with_gemini(prompt)


def generate_lexical_root() -> str:
    """Generate a lexical root for language."""
    prompt = """
    Generate a single syllable or short sound combination that could serve as
    a lexical root in a constructed tribal language. Keep it simple and
    pronounceable.
    """
    result = _generate_with_gemini(prompt)
    return result.strip()[:4] if result else "nar"


def generate_semantic_derivation(root: str) -> str:
    """Generate semantic derivation from a root."""
    prompt = f"""
    Create a derived word from the root "{root}" that could exist in a
    tribal language.
    Add prefixes, suffixes, or modifications to create a new meaningful word.
    """
    result = _generate_with_gemini(prompt)
    return result.strip() if result else f"{root}-derived"


def explain_rl_reward(reward_components: Any) -> str:
    """Explain RL reward components."""
    prompt = f"""
    Explain what these reinforcement learning reward components mean for
    tribal AI:
    {reward_components}
    Write 2-3 sentences interpreting the reward structure.
    """
    return _generate_with_gemini(prompt)


def generate_rl_state_description(state: Any) -> str:
    """Generate description of RL state."""
    prompt = f"""
    Describe this reinforcement learning state in natural language:
    {state}
    Explain what the AI agent is observing about the tribal world.
    """
    return _generate_with_gemini(prompt)


def enhance_markov_dialogue(dialogue: str) -> str:
    """Enhance dialogue using Markov chains and Gemini."""
    prompt = f"""
    Enhance this basic dialogue with more natural, contextual language:
    "{dialogue}"
    Make it sound like authentic tribal communication.
    """
    return _generate_with_gemini(prompt)


# Mark this as the full implementation
__full_implementation__ = True
