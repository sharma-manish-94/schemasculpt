"""
Provider Factory for LLM providers.
Handles provider initialization and selection based on configuration.
"""

from typing import Dict, Any, Optional
from functools import lru_cache

from .base_provider import BaseLLMProvider, ProviderType
from .ollama_provider import OllamaProvider
from .huggingface_provider import HuggingFaceProvider
from .vcap_provider import VCAPProvider
from ..core.logging import get_logger
from ..core.exceptions import LLMError


logger = get_logger("provider_factory")


class ProviderFactory:
    """Factory for creating and managing LLM providers."""

    _provider_registry = {
        ProviderType.OLLAMA: OllamaProvider,
        ProviderType.HUGGINGFACE: HuggingFaceProvider,
        ProviderType.VCAP: VCAPProvider,
    }

    @classmethod
    def create_provider(
        cls,
        provider_type: str,
        config: Dict[str, Any]
    ) -> BaseLLMProvider:
        """
        Create an LLM provider instance.

        Args:
            provider_type: Type of provider ("ollama", "huggingface", "vcap", etc.)
            config: Provider-specific configuration

        Returns:
            Initialized BaseLLMProvider instance

        Raises:
            LLMError: If provider type is not supported
        """
        try:
            provider_enum = ProviderType(provider_type.lower())
        except ValueError:
            supported = ", ".join([p.value for p in ProviderType])
            raise LLMError(
                f"Unsupported provider type: {provider_type}. "
                f"Supported providers: {supported}"
            )

        provider_class = cls._provider_registry.get(provider_enum)
        if not provider_class:
            raise LLMError(f"Provider class not found for: {provider_type}")

        try:
            logger.info(f"Initializing {provider_type} provider")
            provider = provider_class(config)
            logger.info(f"{provider_type} provider initialized successfully")
            return provider
        except Exception as e:
            error_msg = f"Failed to initialize {provider_type} provider: {str(e)}"
            logger.error(error_msg)
            raise LLMError(error_msg)

    @classmethod
    def register_provider(
        cls,
        provider_type: ProviderType,
        provider_class: type
    ):
        """
        Register a new provider type.

        Args:
            provider_type: Provider type enum
            provider_class: Provider class (must inherit from BaseLLMProvider)
        """
        if not issubclass(provider_class, BaseLLMProvider):
            raise LLMError(
                f"Provider class must inherit from BaseLLMProvider: {provider_class}"
            )

        cls._provider_registry[provider_type] = provider_class
        logger.info(f"Registered provider: {provider_type.value}")


# Global provider instance (singleton pattern)
_global_provider: Optional[BaseLLMProvider] = None


def initialize_provider(provider_type: str, config: Dict[str, Any]) -> BaseLLMProvider:
    """
    Initialize the global LLM provider.

    Args:
        provider_type: Type of provider to initialize
        config: Provider configuration

    Returns:
        Initialized provider instance
    """
    global _global_provider

    if _global_provider is not None:
        logger.warning("Replacing existing global provider")

    _global_provider = ProviderFactory.create_provider(provider_type, config)
    return _global_provider


def get_llm_provider() -> BaseLLMProvider:
    """
    Get the global LLM provider instance.

    Returns:
        Global provider instance

    Raises:
        LLMError: If provider is not initialized
    """
    if _global_provider is None:
        raise LLMError(
            "LLM provider not initialized. Call initialize_provider() first."
        )

    return _global_provider


def reset_provider():
    """Reset the global provider (useful for testing)."""
    global _global_provider
    _global_provider = None
