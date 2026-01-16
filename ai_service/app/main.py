from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import cleanup_dependencies
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import get_logger
from app.providers.provider_factory import initialize_provider
from app.services.rag_initializer import initialize_rag_on_startup

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
        logger.info(
            f"Provider health check: {'✓ Healthy' if is_healthy else '✗ Unhealthy'}"
        )
    except Exception as e:
        logger.error(f"Failed to initialize provider: {str(e)}")
        # Continue anyway - endpoints will handle errors gracefully

    # Startup: Initialize RAG knowledge bases
    try:
        logger.info("Initializing RAG knowledge bases...")
        rag_result = await initialize_rag_on_startup()
        if rag_result.get("status") == "success":
            total_docs = rag_result.get("total_documents", 0)
            logger.info(
                f"RAG knowledge bases initialized successfully ({total_docs} documents)"
            )
        elif rag_result.get("status") == "already_initialized":
            logger.info(
                "RAG knowledge bases already populated, skipping initialization"
            )
        else:
            logger.warning(f"RAG initialization completed with warnings: {rag_result}")
    except Exception as e:
        logger.error(f"Failed to initialize RAG knowledge bases: {str(e)}")
        logger.warning("Application will continue without RAG support")
        # Continue anyway - RAG is optional, app can work without it

    yield

    # Shutdown: Cleanup dependencies
    logger.info("Shutting down AI service...")
    await cleanup_dependencies()
    logger.info("Cleanup complete")


app = FastAPI(
    title="SchemaSculpt AI Service", version=settings.app_version, lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
    ],  # React and Spring Boot
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Include the aggregated v1 API router
# This includes all domain-specific routers plus legacy endpoints
app.include_router(api_router)


@app.get("/")
def read_root():
    return {
        "message": "SchemaSculpt AI Service is running",
        "version": settings.app_version,
        "provider": settings.llm_provider,
        "model": settings.default_model,
    }
