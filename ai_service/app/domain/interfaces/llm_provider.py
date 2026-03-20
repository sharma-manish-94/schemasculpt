"""
LLM Provider Interface.

Defines the contract for all LLM provider implementations (Ollama, HuggingFace, OpenAI, etc.).
This allows swapping providers without changing service layer code.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.domain.models.value_objects import LLMResponse, LLMStreamChunk


class ILLMProvider(ABC):
    """
    Abstract interface for LLM providers.

    All LLM provider implementations must implement this interface.
    This follows the Strategy Pattern and Dependency Inversion Principle.

    Usage:
        # In service layer
        class AIService:
            def __init__(self, llm_provider: ILLMProvider):
                self._llm = llm_provider

            async def process(self, prompt: str) -> str:
                response = await self._llm.chat([{"role": "user", "content": prompt}])
                return response.content
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'ollama', 'huggingface', 'openai')."""

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return the default model for this provider."""

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Send a chat completion request to the LLM.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
                      Roles: 'system', 'user', 'assistant'
            model: Model name to use (provider-specific). Uses default if None.
            temperature: Sampling temperature (0.0 to 2.0). Lower = more deterministic.
            max_tokens: Maximum tokens to generate. None = provider default.
            **kwargs: Additional provider-specific parameters.

        Returns:
            LLMResponse with the model's output and metadata.

        Raises:
            LLMError: If the LLM request fails.
            LLMTimeoutError: If the request times out.
        """

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        """
        Stream a chat completion response from the LLM.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            model: Model name to use (provider-specific). Uses default if None.
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional provider-specific parameters.

        Yields:
            LLMStreamChunk objects containing partial responses.

        Raises:
            LLMError: If the LLM request fails.
            LLMTimeoutError: If the request times out.
        """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate completion for a single prompt (non-chat format).

        This is a convenience method that wraps the prompt in a user message.

        Args:
            prompt: Input prompt text.
            model: Model name to use.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional provider-specific parameters.

        Returns:
            LLMResponse with the model's output.
        """

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the LLM provider is healthy and accessible.

        Returns:
            True if the provider is healthy, False otherwise.
        """

    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """
        Get list of available models for this provider.

        Returns:
            List of model names available for use.
        """

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about this provider.

        Returns:
            Dictionary with provider metadata.
        """
        return {
            "provider_name": self.provider_name,
            "default_model": self.default_model,
            "capabilities": {
                "chat": True,
                "streaming": True,
                "generation": True,
            },
        }
