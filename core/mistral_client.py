"""Mistral API client for reasoning tasks."""

import os

from mistralai import Mistral


def get_client() -> Mistral:
    """Return Mistral client with API key from environment."""
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY must be set in environment")
    return Mistral(api_key=api_key)


def chat(prompt: str, system: str = "", model: str = "mistral-small-latest") -> str:
    """
    Send a chat completion request to Mistral.

    Args:
        prompt: User message
        system: Optional system message
        model: Model ID

    Returns:
        Assistant reply text
    """
    client = get_client()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.complete(model=model, messages=messages)
    return response.choices[0].message.content or ""
