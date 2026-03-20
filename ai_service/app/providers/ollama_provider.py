"""
Ollama LLM Provider implementation for SchemaSculpt AI Service.
Connects to local or remote Ollama instances.
"""

import json
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from ..core.exceptions import LLMError
from ..core.logging import get_logger
from .base_provider import BaseLLMProvider, LLMResponse, LLMStreamResponse, ProviderType


class OllamaProvider(BaseLLMProvider):
    """
    Ollama LLM provider implementation.
    Supports local and remote Ollama instances.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = get_logger("ollama_provider")

        self.base_url = config.get("base_url", "http://localhost:11434")
        self.default_model = config.get("default_model", "mistral:7b-instruct")
        self.timeout = config.get("timeout", 120)

        self.chat_endpoint = f"{self.base_url}/api/chat"
        self.generate_endpoint = f"{self.base_url}/api/generate"
        self.tags_endpoint = f"{self.base_url}/api/tags"

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout), limits=httpx.Limits(max_connections=10)
        )

    def _get_provider_type(self) -> ProviderType:
        return ProviderType.OLLAMA

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs,
    ) -> LLMResponse:
        """Send chat completion request to Ollama."""
        model = model or self.default_model

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        # Add any additional Ollama-specific options
        if kwargs:
            payload["options"].update(kwargs)

        try:
            self.logger.debug(
                f"Sending chat request to Ollama: model={model}, messages={len(messages)}"
            )

            response = await self.client.post(self.chat_endpoint, json=payload)

            if response.status_code != 200:
                error_msg = (
                    f"Ollama API error: {response.status_code} - {response.text}"
                )
                self.logger.error(error_msg)
                raise LLMError(error_msg)

            result = response.json()
            content = result.get("message", {}).get("content", "")

            # Extract token usage if available
            usage = None
            if "eval_count" in result:
                usage = {
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0),
                    "total_tokens": result.get("prompt_eval_count", 0)
                    + result.get("eval_count", 0),
                }

            return LLMResponse(
                content=content,
                model=model,
                provider="ollama",
                usage=usage,
                metadata={
                    "total_duration": result.get("total_duration"),
                    "load_duration": result.get("load_duration"),
                    "eval_duration": result.get("eval_duration"),
                },
            )

        except httpx.RequestError as e:
            error_msg = f"Ollama connection error: {str(e)}"
            self.logger.error(error_msg)
            raise LLMError(error_msg)
        except Exception as e:
            error_msg = f"Ollama chat error: {str(e)}"
            self.logger.error(error_msg)
            raise LLMError(error_msg)

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[LLMStreamResponse, None]:
        """Stream chat completion response from Ollama."""
        model = model or self.default_model

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
            },
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        if kwargs:
            payload["options"].update(kwargs)

        try:
            self.logger.debug(f"Starting streaming chat with Ollama: model={model}")

            async with self.client.stream(
                "POST", self.chat_endpoint, json=payload
            ) as response:
                if response.status_code != 200:
                    error_msg = f"Ollama API error: {response.status_code}"
                    self.logger.error(error_msg)
                    raise LLMError(error_msg)

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    try:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        is_final = chunk.get("done", False)

                        yield LLMStreamResponse(
                            content=content,
                            is_final=is_final,
                            model=model,
                            provider="ollama",
                            metadata={"chunk": chunk} if is_final else None,
                        )

                    except json.JSONDecodeError:
                        self.logger.warning(f"Failed to parse streaming chunk: {line}")
                        continue

        except httpx.RequestError as e:
            error_msg = f"Ollama streaming error: {str(e)}"
            self.logger.error(error_msg)
            raise LLMError(error_msg)

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate completion using Ollama's generate endpoint."""
        model = model or self.default_model

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        if kwargs:
            payload["options"].update(kwargs)

        try:
            self.logger.debug(f"Sending generate request to Ollama: model={model}")

            response = await self.client.post(self.generate_endpoint, json=payload)

            if response.status_code != 200:
                error_msg = (
                    f"Ollama API error: {response.status_code} - {response.text}"
                )
                self.logger.error(error_msg)
                raise LLMError(error_msg)

            result = response.json()
            content = result.get("response", "")

            return LLMResponse(
                content=content,
                model=model,
                provider="ollama",
                usage={
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0),
                    "total_tokens": result.get("prompt_eval_count", 0)
                    + result.get("eval_count", 0),
                },
                metadata={
                    "total_duration": result.get("total_duration"),
                    "eval_duration": result.get("eval_duration"),
                },
            )

        except httpx.RequestError as e:
            error_msg = f"Ollama connection error: {str(e)}"
            self.logger.error(error_msg)
            raise LLMError(error_msg)

    async def health_check(self) -> bool:
        """Check if Ollama is accessible."""
        try:
            response = await self.client.get(self.tags_endpoint)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Ollama health check failed: {str(e)}")
            return False

    def get_available_models(self) -> List[str]:
        """
        Get list of available models from Ollama.
        Note: This is a synchronous fallback. Use async health check for real-time data.
        """
        try:
            # This should ideally be async, but keeping it simple for now
            import requests

            response = requests.get(self.tags_endpoint, timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model.get("name") for model in models if model.get("name")]
            return [self.default_model]
        except Exception as e:
            self.logger.warning(f"Failed to fetch Ollama models: {str(e)}")
            return [self.default_model]

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
