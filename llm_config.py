"""
LLM Configuration for Chronicler System

This module handles LLM API configuration and provides a unified interface
for different LLM providers (OpenAI, Anthropic, Google Gemini, etc.).

API keys should be set as environment variables:
- OPENAI_API_KEY for OpenAI
- ANTHROPIC_API_KEY for Anthropic
- GOOGLE_API_KEY for Google Gemini

Usage:
    from llm_config import get_llm_client, call_llm, summarize_text

    client = get_llm_client()
    response = call_llm(client, prompt, system_prompt)
"""
import os
from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def call(self, messages: list, **kwargs) -> str:
        """Make a call to the LLM with messages."""
        pass

    @abstractmethod
    def summarize(self, text: str, **kwargs) -> str:
        """Summarize the given text."""
        pass


class OpenAIClient(LLMClient):
    """OpenAI API client."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
            self.model = model
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")

    def call(self, messages: list, **kwargs) -> str:
        """Make a call to OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=kwargs.get('max_tokens', 1000),
                temperature=kwargs.get('temperature', 0.7)
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")

    def summarize(self, text: str, **kwargs) -> str:
        """Summarize text using OpenAI."""
        summary_prompt = f"Please provide a concise summary of the following text in 3 bullet points:\n\n{text}"
        messages = [
            {"role": "system", "content": "You are a helpful assistant that creates concise summaries."},
            {"role": "user", "content": summary_prompt}
        ]
        return self.call(messages, max_tokens=300, temperature=0.3)


class AnthropicClient(LLMClient):
    """Anthropic Claude API client."""

    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = model
        except ImportError:
            raise ImportError("Anthropic package not installed. Run: pip install anthropic")

    def call(self, messages: list, **kwargs) -> str:
        """Make a call to Anthropic API."""
        try:
            # Convert OpenAI-style messages to Anthropic format
            system_message = ""
            conversation_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    conversation_messages.append(msg)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get('max_tokens', 1000),
                temperature=kwargs.get('temperature', 0.7),
                system=system_message,
                messages=conversation_messages
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {e}")

    def summarize(self, text: str, **kwargs) -> str:
        """Summarize text using Anthropic."""
        summary_prompt = f"Please provide a concise summary of the following text in 3 bullet points:\n\n{text}"
        messages = [
            {"role": "user", "content": summary_prompt}
        ]
        return self.call(messages, max_tokens=300, temperature=0.3)


class GoogleGeminiClient(LLMClient):
    """Google Gemini API client."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model)
        except ImportError:
            raise ImportError("Google Generative AI package not installed. Run: pip install google-generativeai")

    def call(self, messages: list, **kwargs) -> str:
        """Make a call to Google Gemini API."""
        try:
            # Convert OpenAI-style messages to Gemini format
            # Combine system message with user message if present
            system_content = ""
            user_content = ""
            
            for msg in messages:
                if msg["role"] == "system":
                    system_content = msg["content"]
                elif msg["role"] == "user":
                    user_content = msg["content"]
            
            # Combine system and user content
            if system_content:
                prompt = f"{system_content}\n\n{user_content}"
            else:
                prompt = user_content
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": kwargs.get('temperature', 0.7),
                    "max_output_tokens": kwargs.get('max_tokens', 1000),
                }
            )
            return response.text
        except Exception as e:
            raise Exception(f"Google Gemini API error: {e}")

    def summarize(self, text: str, **kwargs) -> str:
        """Summarize text using Google Gemini."""
        summary_prompt = f"Please provide a concise summary of the following text in 3 bullet points:\n\n{text}"
        messages = [{"role": "user", "content": summary_prompt}]
        return self.call(messages, max_tokens=300, temperature=0.3)


class MockClient(LLMClient):
    """Mock client for testing without API keys."""

    def call(self, messages: list, **kwargs) -> str:
        """Return mock response."""
        user_content = next((m['content'] for m in messages if m['role'] == 'user'), '')
        return f"Mock response to: {user_content[:100]}..."

    def summarize(self, text: str, **kwargs) -> str:
        """Return mock summary."""
        return "- Mock summary point 1\n- Mock summary point 2\n- Mock summary point 3"


def get_llm_client(provider: str = "auto") -> LLMClient:
    """
    Get an LLM client based on available API keys and provider preference.

    Args:
        provider: "openai", "anthropic", "google", "mock", or "auto" (default)

    Returns:
        LLMClient instance

    Raises:
        ValueError: If no valid configuration found
    """
    if provider == "mock":
        return MockClient()

    # Auto-detect based on available keys
    if provider == "auto":
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        google_key = os.getenv("GOOGLE_API_KEY")

        if google_key:
            provider = "google"
        elif openai_key:
            provider = "openai"
        elif anthropic_key:
            provider = "anthropic"
        else:
            print("Warning: No API keys found. Using mock client.")
            return MockClient()

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        return OpenAIClient(api_key)

    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        return AnthropicClient(api_key)

    elif provider == "google":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        return GoogleGeminiClient(api_key)

    else:
        raise ValueError(f"Unknown provider: {provider}")


def call_llm(client: LLMClient, user_prompt: str, system_prompt: str = "", **kwargs) -> str:
    """
    Unified interface for LLM calls.

    Args:
        client: LLMClient instance
        user_prompt: The user message
        system_prompt: Optional system message
        **kwargs: Additional parameters (max_tokens, temperature, etc.)

    Returns:
        LLM response as string
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    return client.call(messages, **kwargs)


def summarize_text(client: LLMClient, text: str, **kwargs) -> str:
    """
    Unified interface for text summarization.

    Args:
        client: LLMClient instance
        text: Text to summarize
        **kwargs: Additional parameters

    Returns:
        Summary as string
    """
    return client.summarize(text, **kwargs)


# Configuration constants
DEFAULT_MODEL = {
    "openai": "gpt-4",
    "anthropic": "claude-3-sonnet-20240229",
    "google": "gemini-1.5-flash"
}

DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1000