"""
Core configuration management for SchemaSculpt AI Service.
Provides centralized configuration with environment variable support.
"""

import os
from functools import lru_cache
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    app_name: str = Field(default="SchemaSculpt AI Service", env="APP_NAME")
    app_version: str = Field(default="2.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")

    # API Configuration
    api_prefix: str = Field(default="/api/v2", env="API_PREFIX")
    allowed_hosts: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")

    # LLM Configuration
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_chat_endpoint: str = Field(default="/api/chat", env="OLLAMA_CHAT_ENDPOINT")
    ollama_generate_endpoint: str = Field(default="/api/generate", env="OLLAMA_GENERATE_ENDPOINT")
    default_model: str = Field(default="mistral:7b-instruct", env="DEFAULT_LLM_MODEL")
    model_temperature: float = Field(default=0.1, env="MODEL_TEMPERATURE")
    max_tokens: int = Field(default=2048, env="MAX_TOKENS")
    request_timeout: int = Field(default=120, env="REQUEST_TIMEOUT")

    # Advanced LLM Settings
    enable_streaming: bool = Field(default=True, env="ENABLE_STREAMING")
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    max_concurrent_requests: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")

    # Prompt Engineering
    system_prompt_template_path: str = Field(default="prompts/system", env="SYSTEM_PROMPT_PATH")
    user_prompt_template_path: str = Field(default="prompts/user", env="USER_PROMPT_PATH")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_calls: int = Field(default=100, env="RATE_LIMIT_CALLS")
    rate_limit_period: int = Field(default=3600, env="RATE_LIMIT_PERIOD")  # 1 hour

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")

    # Security
    api_key: Optional[str] = Field(default=None, env="API_KEY")
    cors_origins: List[str] = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")

    # Monitoring & Metrics
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_endpoint: str = Field(default="/metrics", env="METRICS_ENDPOINT")

    # Database (for advanced features like conversation history)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    redis_url: Optional[str] = Field(default="redis://localhost:6379", env="REDIS_URL")

    # AI Service Data Directory
    ai_service_data_dir: str = Field(default=".", env="AI_SERVICE_DATA_DIR")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Allow extra environment variables


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Global settings instance
settings = get_settings()