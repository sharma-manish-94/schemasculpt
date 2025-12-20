"""
LLM Adapter Service - Provides backward compatibility with existing LLMService interface.
Uses the new provider abstraction layer while maintaining the same API.
"""

import time
from typing import Any, Dict, List, Optional

from ..core.exceptions import LLMError
from ..core.logging import get_logger
from ..providers.provider_factory import get_llm_provider
from ..schemas.ai_schemas import (
    AIRequest,
    AIResponse,
    OperationType,
    PerformanceMetrics,
)

logger = get_logger("llm_adapter")


class LLMAdapter:
    """
    Adapter service that wraps the provider abstraction.
    Maintains compatibility with the existing LLMService interface.
    """

    def __init__(self):
        self.logger = logger

    async def call_llm(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Call the LLM provider and return the response text.

        Args:
            messages: List of chat messages
            model: Optional model override
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text response
        """
        try:
            provider = get_llm_provider()
            response = await provider.chat(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            return response.content

        except Exception as e:
            self.logger.error(f"LLM call failed: {str(e)}")
            raise LLMError(f"LLM generation failed: {str(e)}")

    async def call_llm_with_retry(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        max_retries: int = 3,
        **kwargs,
    ) -> str:
        """
        Call LLM with automatic retry on failure.

        Args:
            messages: List of chat messages
            model: Optional model override
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            max_retries: Maximum number of retry attempts
            **kwargs: Additional parameters

        Returns:
            Generated text response
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                return await self.call_llm(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"LLM call attempt {attempt + 1}/{max_retries} failed: {str(e)}"
                )

                if attempt < max_retries - 1:
                    # Exponential backoff
                    import asyncio

                    await asyncio.sleep(2**attempt)

        raise LLMError(
            f"LLM call failed after {max_retries} attempts: {str(last_error)}"
        )

    async def stream_llm(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs,
    ):
        """
        Stream LLM responses.

        Args:
            messages: List of chat messages
            model: Optional model override
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            **kwargs: Additional parameters

        Yields:
            StreamResponse chunks
        """
        try:
            provider = get_llm_provider()
            async for chunk in provider.chat_stream(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            ):
                yield chunk

        except Exception as e:
            self.logger.error(f"LLM streaming failed: {str(e)}")
            raise LLMError(f"LLM streaming failed: {str(e)}")

    async def health_check(self) -> bool:
        """Check if LLM provider is healthy."""
        try:
            provider = get_llm_provider()
            return await provider.health_check()
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False

    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current provider."""
        try:
            provider = get_llm_provider()
            return provider.get_provider_info()
        except Exception as e:
            self.logger.error(f"Failed to get provider info: {str(e)}")
            return {"error": str(e), "provider_type": "unknown"}


# Global adapter instance (backward compatibility)
_global_adapter: Optional[LLMAdapter] = None


def get_llm_adapter() -> LLMAdapter:
    """Get the global LLM adapter instance."""
    global _global_adapter
    if _global_adapter is None:
        _global_adapter = LLMAdapter()
    return _global_adapter
