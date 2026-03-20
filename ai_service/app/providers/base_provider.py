"""
Base LLM Provider interface for SchemaSculpt AI Service.
All LLM providers must implement this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional


class ProviderType(Enum):
    """Supported LLM provider types."""

    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    VCAP = "vcap"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMResponse:
    """Standard LLM response format."""

    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None  # token usage stats
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMStreamResponse:
    """Streaming LLM response chunk."""

    content: str
    is_final: bool
    model: str
    provider: str
    metadata: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """
    Base class for all LLM providers.
    Provides a common interface for different LLM backends.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LLM provider with configuration.

        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config
        self.provider_type = self._get_provider_type()

    @abstractmethod
    def _get_provider_type(self) -> ProviderType:
        """Return the provider type."""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs,
    ) -> LLMResponse:
        """
        Send a chat completion request to the LLM.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model name to use (provider-specific)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse with the model's output
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[LLMStreamResponse, None]:
        """
        Stream a chat completion response from the LLM.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model name to use (provider-specific)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Yields:
            LLMStreamResponse chunks
        """
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate completion for a single prompt.

        Args:
            prompt: Input prompt text
            model: Model name to use (provider-specific)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse with the model's output
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the LLM provider is healthy and accessible.

        Returns:
            True if healthy, False otherwise
        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models for this provider.

        Returns:
            List of model names
        """
        pass

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about this provider.

        Returns:
            Dictionary with provider metadata
        """
        return {
            "provider_type": self.provider_type.value,
            "config": {
                k: v for k, v in self.config.items() if k not in ["api_key", "token"]
            },
            "capabilities": {"chat": True, "streaming": True, "generation": True},
        }
