"""
VCAP/Cloud Foundry LLM Provider implementation for SchemaSculpt AI Service.
Supports SAP AI Core and other Cloud Foundry deployed LLM services.
"""

import json
import os
from typing import Dict, Any, AsyncGenerator, Optional, List
import httpx

from .base_provider import (
    BaseLLMProvider,
    LLMResponse,
    LLMStreamResponse,
    ProviderType
)
from ..core.logging import get_logger
from ..core.exceptions import LLMError


class VCAPProvider(BaseLLMProvider):
    """
    VCAP/Cloud Foundry LLM provider implementation.
    Reads configuration from VCAP_SERVICES environment variable.
    Supports SAP AI Core and generic Cloud Foundry LLM deployments.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = get_logger("vcap_provider")

        # Parse VCAP_SERVICES if available
        self.vcap_config = self._parse_vcap_services()

        # Get configuration with VCAP fallback
        self.service_name = config.get("service_name", "aicore")
        self.default_model = config.get("default_model", "gpt-3.5-turbo")
        self.timeout = config.get("timeout", 120)

        # Extract credentials from VCAP or config
        service_credentials = self._get_service_credentials()

        self.api_url = config.get("api_url") or service_credentials.get("url")
        self.api_key = config.get("api_key") or service_credentials.get("api_key")
        self.client_id = service_credentials.get("client_id")
        self.client_secret = service_credentials.get("client_secret")
        self.auth_url = service_credentials.get("auth_url")

        if not self.api_url:
            raise LLMError("VCAP provider requires api_url in config or VCAP_SERVICES")

        # Prepare authentication
        self.access_token = None
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout)
        )

    def _get_provider_type(self) -> ProviderType:
        return ProviderType.VCAP

    def _parse_vcap_services(self) -> Dict[str, Any]:
        """Parse VCAP_SERVICES environment variable."""
        vcap_services_str = os.getenv("VCAP_SERVICES")
        if not vcap_services_str:
            self.logger.warning("VCAP_SERVICES not found in environment")
            return {}

        try:
            vcap_services = json.loads(vcap_services_str)
            self.logger.info("Successfully parsed VCAP_SERVICES")
            return vcap_services
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse VCAP_SERVICES: {str(e)}")
            return {}

    def _get_service_credentials(self) -> Dict[str, Any]:
        """Extract service credentials from VCAP_SERVICES."""
        if not self.vcap_config:
            return {}

        # Look for service by name (e.g., "aicore", "genai-hub", etc.)
        for service_type, services in self.vcap_config.items():
            for service in services:
                if service.get("name") == self.service_name:
                    credentials = service.get("credentials", {})
                    self.logger.info(f"Found credentials for service: {self.service_name}")
                    return credentials

        # If not found by name, try first available AI service
        ai_service_types = ["aicore", "genai-hub", "ml-foundation", "llm-service"]
        for service_type in ai_service_types:
            if service_type in self.vcap_config and len(self.vcap_config[service_type]) > 0:
                credentials = self.vcap_config[service_type][0].get("credentials", {})
                self.logger.info(f"Using first available {service_type} credentials")
                return credentials

        self.logger.warning("No AI service credentials found in VCAP_SERVICES")
        return {}

    async def _get_access_token(self) -> str:
        """Get OAuth2 access token if required."""
        if not self.auth_url or not self.client_id or not self.client_secret:
            # No OAuth required, use API key directly
            return self.api_key or ""

        try:
            # OAuth2 client credentials flow
            auth_data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }

            response = await self.client.post(
                self.auth_url,
                data=auth_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code != 200:
                raise LLMError(f"OAuth authentication failed: {response.status_code}")

            token_data = response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                raise LLMError("No access token in OAuth response")

            self.logger.info("Successfully obtained OAuth2 access token")
            return access_token

        except Exception as e:
            error_msg = f"Failed to get OAuth token: {str(e)}"
            self.logger.error(error_msg)
            raise LLMError(error_msg)

    async def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with authentication."""
        headers = {"Content-Type": "application/json"}

        if self.auth_url:
            # OAuth2 flow
            if not self.access_token:
                self.access_token = await self._get_access_token()
            headers["Authorization"] = f"Bearer {self.access_token}"
        elif self.api_key:
            # API key authentication
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> LLMResponse:
        """Send chat completion request to VCAP LLM service."""
        model = model or self.default_model

        # Standard OpenAI-compatible payload (most CF deployments use this format)
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        # Add any additional parameters
        if kwargs:
            payload.update(kwargs)

        try:
            headers = await self._get_headers()
            endpoint = f"{self.api_url}/chat/completions"

            self.logger.debug(f"Sending chat request to VCAP: {endpoint}")

            response = await self.client.post(
                endpoint,
                json=payload,
                headers=headers
            )

            if response.status_code == 401:
                # Token might have expired, refresh and retry
                self.access_token = None
                headers = await self._get_headers()
                response = await self.client.post(
                    endpoint,
                    json=payload,
                    headers=headers
                )

            if response.status_code != 200:
                error_msg = f"VCAP API error: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                raise LLMError(error_msg)

            result = response.json()

            # Parse OpenAI-compatible response
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = result.get("usage", {})

            return LLMResponse(
                content=content,
                model=model,
                provider="vcap",
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0)
                },
                metadata={
                    "service_name": self.service_name,
                    "deployment": "cloud_foundry"
                }
            )

        except httpx.RequestError as e:
            error_msg = f"VCAP connection error: {str(e)}"
            self.logger.error(error_msg)
            raise LLMError(error_msg)

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[LLMStreamResponse, None]:
        """Stream chat completion response from VCAP service."""
        model = model or self.default_model

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        if kwargs:
            payload.update(kwargs)

        try:
            headers = await self._get_headers()
            endpoint = f"{self.api_url}/chat/completions"

            async with self.client.stream(
                "POST",
                endpoint,
                json=payload,
                headers=headers
            ) as response:
                if response.status_code != 200:
                    error_msg = f"VCAP streaming error: {response.status_code}"
                    self.logger.error(error_msg)
                    raise LLMError(error_msg)

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    data = line[6:]  # Remove "data: " prefix
                    if data == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        finish_reason = chunk.get("choices", [{}])[0].get("finish_reason")

                        yield LLMStreamResponse(
                            content=content,
                            is_final=finish_reason is not None,
                            model=model,
                            provider="vcap"
                        )

                    except json.JSONDecodeError:
                        continue

        except httpx.RequestError as e:
            error_msg = f"VCAP streaming error: {str(e)}"
            self.logger.error(error_msg)
            raise LLMError(error_msg)

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate completion for a prompt."""
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, model, temperature, max_tokens, **kwargs)

    async def health_check(self) -> bool:
        """Check if VCAP service is accessible."""
        try:
            headers = await self._get_headers()
            # Try to access the base URL or a health endpoint
            response = await self.client.get(
                f"{self.api_url}/health",
                headers=headers
            )
            return response.status_code in [200, 404]  # 404 is OK if health endpoint doesn't exist
        except Exception as e:
            self.logger.error(f"VCAP health check failed: {str(e)}")
            return False

    def get_available_models(self) -> List[str]:
        """Get list of available models (configured in VCAP)."""
        # This would need to be populated from VCAP service metadata
        return [self.default_model, "gpt-4", "gpt-3.5-turbo", "claude-3"]

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
