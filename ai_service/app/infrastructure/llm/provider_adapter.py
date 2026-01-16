"""
LLM Provider Adapter.

Adapts the existing BaseLLMProvider implementations to the ILLMProvider interface.
This follows the Adapter Pattern to bridge the legacy providers with the new domain interface.
"""

from typing import Any, AsyncGenerator, Dict, List, Optional

from app.domain.interfaces.llm_provider import ILLMProvider
from app.domain.models.value_objects import LLMResponse, LLMStreamChunk, LLMUsage
from app.providers.base_provider import BaseLLMProvider
from app.providers.base_provider import LLMResponse as LegacyLLMResponse
from app.providers.base_provider import LLMStreamResponse as LegacyStreamResponse


class LLMProviderAdapter(ILLMProvider):
    """
    Adapter that wraps BaseLLMProvider to implement ILLMProvider.

    This allows the existing provider implementations (OllamaProvider, HuggingFaceProvider, etc.)
    to be used with the new domain interface without modification.

    Example:
        from app.providers.ollama_provider import OllamaProvider
        from app.infrastructure.llm.provider_adapter import LLMProviderAdapter

        ollama = OllamaProvider(config)
        provider = LLMProviderAdapter(ollama)

        # Now use via ILLMProvider interface
        response = await provider.chat([{"role": "user", "content": "Hello"}])
    """

    def __init__(self, provider: BaseLLMProvider):
        """
        Initialize the adapter with a BaseLLMProvider instance.

        Args:
            provider: The underlying BaseLLMProvider implementation.
        """
        self._provider = provider

    @property
    def provider_name(self) -> str:
        """Return the provider name."""
        return self._provider.provider_type.value

    @property
    def default_model(self) -> str:
        """Return the default model for this provider."""
        return getattr(self._provider, "default_model", "unknown")

    def _convert_response(self, legacy_response: LegacyLLMResponse) -> LLMResponse:
        """Convert legacy LLMResponse to domain LLMResponse."""
        usage = None
        if legacy_response.usage:
            usage = LLMUsage(
                prompt_tokens=legacy_response.usage.get("prompt_tokens", 0),
                completion_tokens=legacy_response.usage.get("completion_tokens", 0),
                total_tokens=legacy_response.usage.get("total_tokens", 0),
            )

        return LLMResponse(
            content=legacy_response.content,
            model=legacy_response.model,
            provider=legacy_response.provider,
            usage=usage,
            metadata=legacy_response.metadata or {},
        )

    def _convert_stream_chunk(
        self, legacy_chunk: LegacyStreamResponse
    ) -> LLMStreamChunk:
        """Convert legacy LLMStreamResponse to domain LLMStreamChunk."""
        return LLMStreamChunk(
            content=legacy_chunk.content,
            model=legacy_chunk.model,
            provider=legacy_chunk.provider,
            is_final=legacy_chunk.is_final,
            metadata=legacy_chunk.metadata or {},
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send a chat completion request to the LLM."""
        legacy_response = await self._provider.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return self._convert_response(legacy_response)

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        """Stream a chat completion response from the LLM."""
        async for legacy_chunk in self._provider.chat_stream(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ):
            yield self._convert_stream_chunk(legacy_chunk)

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate completion for a single prompt."""
        legacy_response = await self._provider.generate(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return self._convert_response(legacy_response)

    async def health_check(self) -> bool:
        """Check if the LLM provider is healthy and accessible."""
        return await self._provider.health_check()

    async def get_available_models(self) -> List[str]:
        """Get list of available models for this provider."""
        # The base provider has a sync method, wrap it
        return self._provider.get_available_models()

    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about this provider."""
        base_info = self._provider.get_provider_info()
        return {
            "provider_name": self.provider_name,
            "default_model": self.default_model,
            "capabilities": base_info.get("capabilities", {}),
            "config": base_info.get("config", {}),
        }
