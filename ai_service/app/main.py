from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import endpoints
from app.api import repository_endpoints
from app.core.config import settings
from app.providers.provider_factory import initialize_provider
from app.core.logging import get_logger

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown."""
    # Startup: Initialize LLM provider
    try:
        logger.info(f"Initializing {settings.llm_provider} provider...")
        provider_config = settings.get_provider_config()
        provider = initialize_provider(settings.llm_provider, provider_config)
        logger.info(f"{settings.llm_provider} provider initialized successfully")

        # Health check
        is_healthy = await provider.health_check()
        logger.info(f"Provider health check: {'✓ Healthy' if is_healthy else '✗ Unhealthy'}")
    except Exception as e:
        logger.error(f"Failed to initialize provider: {str(e)}")
        # Continue anyway - endpoints will handle errors gracefully

    yield

    # Shutdown: Cleanup
    logger.info("Shutting down AI service...")


app = FastAPI(
    title="SchemaSculpt AI Service",
    version=settings.app_version,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # React and Spring Boot
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(endpoints.router)
app.include_router(repository_endpoints.router)


@app.get("/")
def read_root():
    return {
        "message": "SchemaSculpt AI Service is running",
        "version": settings.app_version,
        "provider": settings.llm_provider,
        "model": settings.default_model
    }