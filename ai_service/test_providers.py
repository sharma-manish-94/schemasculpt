#!/usr/bin/env python3
"""
Quick test script for LLM providers.
Tests provider initialization and basic functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.providers.provider_factory import ProviderFactory


def _redact_sensitive_config(config: dict) -> dict:
    """Return a copy of the config with sensitive values redacted."""
    sensitive_keywords = ("key", "secret", "token", "password")

    def _redact(obj):
        if isinstance(obj, dict):
            redacted = {}
            for k, v in obj.items():
                if isinstance(k, str) and any(
                    kw in k.lower() for kw in sensitive_keywords
                ):
                    redacted[k] = "<redacted>" if v is not None else None
                else:
                    redacted[k] = _redact(v)
            return redacted
        elif isinstance(obj, list):
            return [_redact(item) for item in obj]
        return obj

    return _redact(config)


async def test_provider(provider_type: str):
    """Test a specific provider."""
    print(f"\n{'='*60}")
    print(f"Testing {provider_type.upper()} Provider")
    print(f"{'='*60}\n")

    try:
        # Get provider config
        original_provider = settings.llm_provider
        settings.llm_provider = provider_type
        config = settings.get_provider_config()
        settings.llm_provider = original_provider

        # Avoid logging sensitive values such as API keys or tokens
        safe_config = _redact_sensitive_config(config)
        print(f"Configuration: {safe_config}\n")

        # Create provider
        print(f"Initializing {provider_type} provider...")
        provider = ProviderFactory.create_provider(provider_type, config)
        print(f"✓ Provider initialized successfully\n")

        # Test health check
        print("Running health check...")
        is_healthy = await provider.health_check()
        health_status = "✓ Healthy" if is_healthy else "✗ Unhealthy"
        print(f"{health_status}\n")

        if not is_healthy:
            print(
                f"⚠ Provider is unhealthy. Check configuration and service availability."
            )
            return

        # Test basic chat
        print("Testing basic chat completion...")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": "Say 'Hello from SchemaSculpt!' and nothing else.",
            },
        ]

        response = await provider.chat(
            messages=messages, temperature=0.1, max_tokens=50
        )

        print(f"✓ Chat completed")
        print(f"  Model: {response.model}")
        print(f"  Provider: {response.provider}")
        print(f"  Response: {response.content[:100]}...")
        if response.usage:
            print(f"  Tokens: {response.usage}")

        # Test streaming (if supported)
        print("\nTesting streaming...")
        try:
            chunks = []
            async for chunk in provider.chat_stream(
                messages=messages, temperature=0.1, max_tokens=50
            ):
                chunks.append(chunk.content)
                if chunk.is_final:
                    break

            print(f"✓ Streaming completed ({len(chunks)} chunks)")
            print(f"  Full response: {''.join(chunks)[:100]}...")

        except Exception as e:
            print(f"⚠ Streaming test failed: {str(e)}")

        # Get provider info
        print("\nProvider Information:")
        info = provider.get_provider_info()
        for key, value in info.items():
            print(f"  {key}: {value}")

        print(f"\n✓ All tests passed for {provider_type}!")

        # Cleanup
        if hasattr(provider, "close"):
            await provider.close()

    except Exception as e:
        print(f"✗ Error testing {provider_type}: {str(e)}")
        import traceback

        traceback.print_exc()


async def main():
    """Main test function."""
    print(f"\n{'#'*60}")
    print(f"  SchemaSculpt AI Service - Provider Tests")
    print(f"{'#'*60}\n")

    print(f"Current configuration:")
    print(f"  LLM_PROVIDER: {settings.llm_provider}")
    print(f"  DEFAULT_MODEL: {settings.default_model}")

    # Test configured provider
    await test_provider(settings.llm_provider)

    # Optionally test other providers
    print(f"\n\n{'='*60}")
    print("Available Providers")
    print(f"{'='*60}\n")
    print("To test other providers, set LLM_PROVIDER environment variable:")
    print("  export LLM_PROVIDER=huggingface")
    print("  export LLM_PROVIDER=vcap")
    print("  python test_providers.py")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\nTest failed with error: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
