"""
LLM Provider Factory.

Creates ILLMProvider instances by wrapping the existing provider implementations.
This factory provides a clean interface for the dependency injection layer.
"""

import logging
from typing import Any, Dict

from app.domain.interfaces.llm_provider import ILLMProvider
from app.providers.provider_factory import ProviderFactory

from .provider_adapter import LLMProviderAdapter

logger = logging.getLogger(__name__)


async def create_provider(provider_type: str, config: Dict[str, Any]) -> ILLMProvider:
    """
    Create an ILLMProvider instance.

    This function wraps the existing ProviderFactory and adapts the result
    to the ILLMProvider interface.

    Args:
        provider_type: Type of provider ("ollama", "huggingface", "vcap", etc.)
        config: Provider-specific configuration

    Returns:
        ILLMProvider: An adapted provider implementing the domain interface.

    Raises:
        LLMError: If provider type is not supported or initialization fails.

    Example:
        provider = await create_provider("ollama", {"base_url": "http://localhost:11434"})
        response = await provider.chat([{"role": "user", "content": "Hello"}])
    """
    logger.info(f"Creating ILLMProvider for type: {provider_type}")

    # Use the existing factory to create the base provider
    base_provider = ProviderFactory.create_provider(provider_type, config)

    # Wrap in adapter to implement ILLMProvider
    adapted_provider = LLMProviderAdapter(base_provider)

    logger.info(
        f"Created ILLMProvider: {adapted_provider.provider_name} "
        f"(model: {adapted_provider.default_model})"
    )

    return adapted_provider


def get_supported_providers() -> list[str]:
    """
    Get list of supported provider types.

    Returns:
        List of provider type strings.
    """
    from app.providers.base_provider import ProviderType

    return [p.value for p in ProviderType]
