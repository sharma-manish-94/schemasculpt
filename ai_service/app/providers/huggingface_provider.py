"""
HuggingFace LLM Provider implementation for SchemaSculpt AI Service.
Supports HuggingFace Inference API and local transformers.
"""

from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from ..core.exceptions import LLMError
from ..core.logging import get_logger
from .base_provider import BaseLLMProvider, LLMResponse, LLMStreamResponse, ProviderType


class HuggingFaceProvider(BaseLLMProvider):
    """
    HuggingFace LLM provider implementation.
    Supports both Inference API and local models via transformers.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = get_logger("huggingface_provider")

        self.api_key = config.get("api_key")
        self.api_url = config.get(
            "api_url", "https://api-inference.huggingface.co/models"
        )
        self.default_model = config.get(
            "default_model", "mistralai/Mistral-7B-Instruct-v0.2"
        )
        self.timeout = config.get("timeout", 120)
        self.use_local = config.get("use_local", False)

        if not self.use_local and not self.api_key:
            self.logger.warning(
                "No HuggingFace API key provided. Some features may be limited."
            )

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
        )

        # Initialize local model if configured
        self.local_pipeline = None
        if self.use_local:
            self._initialize_local_model()

    def _get_provider_type(self) -> ProviderType:
        return ProviderType.HUGGINGFACE

    def _initialize_local_model(self):
        """Initialize local HuggingFace model using transformers."""
        try:
            import torch
            from transformers import pipeline

            device = 0 if torch.cuda.is_available() else -1
            self.logger.info(
                f"Initializing local HuggingFace model on {'GPU' if device >= 0 else 'CPU'}"
            )

            self.local_pipeline = pipeline(
                "text-generation",
                model=self.default_model,
                device=device,
                torch_dtype=torch.float16 if device >= 0 else torch.float32,
            )
            self.logger.info("Local HuggingFace model initialized successfully")

        except ImportError:
            self.logger.error(
                "transformers library not installed. Install with: pip install transformers torch"
            )
            raise LLMError("transformers library required for local HuggingFace models")
        except Exception as e:
            self.logger.error(f"Failed to initialize local model: {str(e)}")
            raise LLMError(f"Local model initialization failed: {str(e)}")

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to a single prompt string."""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"<|system|>\n{content}</s>")
            elif role == "user":
                prompt_parts.append(f"<|user|>\n{content}</s>")
            elif role == "assistant":
                prompt_parts.append(f"<|assistant|>\n{content}</s>")

        prompt_parts.append("<|assistant|>\n")
        return "\n".join(prompt_parts)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs,
    ) -> LLMResponse:
        """Send chat completion request to HuggingFace."""
        model = model or self.default_model

        if self.use_local and self.local_pipeline:
            return await self._chat_local(messages, temperature, max_tokens, **kwargs)
        else:
            return await self._chat_api(
                messages, model, temperature, max_tokens, **kwargs
            )

    async def _chat_local(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs,
    ) -> LLMResponse:
        """Use local transformers pipeline for chat."""
        try:
            prompt = self._messages_to_prompt(messages)

            # Run in thread pool to avoid blocking
            import asyncio

            loop = asyncio.get_event_loop()

            result = await loop.run_in_executor(
                None,
                lambda: self.local_pipeline(
                    prompt,
                    max_new_tokens=max_tokens or 2048,
                    temperature=temperature,
                    do_sample=True,
                    **kwargs,
                ),
            )

            content = result[0]["generated_text"]
            # Extract only the assistant's response
            if "<|assistant|>" in content:
                content = content.split("<|assistant|>")[-1].strip()

            return LLMResponse(
                content=content,
                model=self.default_model,
                provider="huggingface_local",
                metadata={"method": "local_pipeline"},
            )

        except Exception as e:
            error_msg = f"Local HuggingFace chat error: {str(e)}"
            self.logger.error(error_msg)
            raise LLMError(error_msg)

    async def _chat_api(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        **kwargs,
    ) -> LLMResponse:
        """Use HuggingFace Inference API for chat."""
        try:
            # Convert messages to prompt
            prompt = self._messages_to_prompt(messages)

            payload = {
                "inputs": prompt,
                "parameters": {
                    "temperature": temperature,
                    "max_new_tokens": max_tokens or 2048,
                    "return_full_text": False,
                },
            }

            url = f"{self.api_url}/{model}"
            self.logger.debug(f"Sending request to HuggingFace API: {url}")

            response = await self.client.post(url, json=payload)

            if response.status_code != 200:
                error_msg = (
                    f"HuggingFace API error: {response.status_code} - {response.text}"
                )
                self.logger.error(error_msg)
                raise LLMError(error_msg)

            result = response.json()

            # Handle different response formats
            if isinstance(result, list) and len(result) > 0:
                content = result[0].get("generated_text", "")
            elif isinstance(result, dict):
                content = result.get("generated_text", "")
            else:
                content = str(result)

            return LLMResponse(
                content=content,
                model=model,
                provider="huggingface_api",
                metadata={"api_url": url},
            )

        except httpx.RequestError as e:
            error_msg = f"HuggingFace API connection error: {str(e)}"
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
        """
        Stream chat completion response.
        Note: Streaming may not be supported by all HuggingFace models.
        """
        # For now, we'll simulate streaming by chunking the response
        response = await self.chat(messages, model, temperature, max_tokens, **kwargs)

        # Split content into chunks
        chunk_size = 50
        content = response.content
        for i in range(0, len(content), chunk_size):
            chunk = content[i : i + chunk_size]
            is_final = i + chunk_size >= len(content)

            yield LLMStreamResponse(
                content=chunk,
                is_final=is_final,
                model=response.model,
                provider=response.provider,
            )

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate completion for a prompt."""
        # Convert to messages format
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, model, temperature, max_tokens, **kwargs)

    async def health_check(self) -> bool:
        """Check if HuggingFace provider is healthy."""
        if self.use_local:
            return self.local_pipeline is not None

        try:
            # Try a simple API call
            response = await self.client.get("https://huggingface.co/api/health")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"HuggingFace health check failed: {str(e)}")
            return False

    def get_available_models(self) -> List[str]:
        """Get list of popular HuggingFace models for text generation."""
        return [
            "mistralai/Mistral-7B-Instruct-v0.2",
            "meta-llama/Llama-2-7b-chat-hf",
            "google/flan-t5-xxl",
            "bigcode/starcoder",
            "tiiuae/falcon-7b-instruct",
        ]

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
