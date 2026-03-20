"""
Meta Analysis Router.

Endpoints for AI-powered meta-analysis of OpenAPI specifications.
These endpoints use AI to:
- Detect higher-order patterns from linter findings
- Analyze description quality
- Find patterns that individual linter rules cannot detect
"""

import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_description_analysis_service, get_meta_analysis_service
from app.core.logging import set_correlation_id
from app.schemas.description_schemas import (
    DescriptionAnalysisRequest,
    DescriptionAnalysisResponse,
)
from app.schemas.meta_analysis_schemas import (
    AIMetaAnalysisRequest,
    AIMetaAnalysisResponse,
)

if TYPE_CHECKING:
    from app.services.description_analysis_service import DescriptionAnalysisService
    from app.services.meta_analysis_service import MetaAnalysisService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["Meta Analysis"])


@router.post("/meta-analysis", response_model=AIMetaAnalysisResponse)
async def perform_meta_analysis(
    request: AIMetaAnalysisRequest,
    meta_analysis_service: "MetaAnalysisService" = Depends(get_meta_analysis_service),
) -> AIMetaAnalysisResponse:
    """
    Perform AI meta-analysis on linter findings to detect higher-order patterns.

    This is the "linter-augmented AI analyst" feature. It takes the results from
    deterministic linters and uses AI to find patterns, combinations, and higher-level
    issues that individual linter rules cannot detect.

    Args:
        request: Meta-analysis request containing errors and suggestions.
        meta_analysis_service: Injected meta-analysis service.

    Returns:
        AIMetaAnalysisResponse with insights and confidence score.

    Raises:
        HTTPException: If meta-analysis fails.
    """
    correlation_id = set_correlation_id()

    logger.info(
        f"Performing meta-analysis with {len(request.errors)} errors, "
        f"{len(request.suggestions)} suggestions",
        extra={
            "correlation_id": correlation_id,
            "error_count": len(request.errors),
            "suggestion_count": len(request.suggestions),
        },
    )

    try:
        result = await meta_analysis_service.analyze(request)

        logger.info(
            f"Meta-analysis completed with {len(result.insights)} insights",
            extra={
                "correlation_id": correlation_id,
                "insight_count": len(result.insights),
                "confidence": result.confidenceScore,
            },
        )

        return result

    except Exception as e:
        logger.exception(
            f"Meta-analysis failed: {str(e)}", extra={"correlation_id": correlation_id}
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "META_ANALYSIS_FAILED",
                "message": "Failed to perform meta-analysis",
                "details": {"original_error": str(e)},
                "correlation_id": correlation_id,
            },
        )


@router.post("/analyze-descriptions", response_model=DescriptionAnalysisResponse)
async def analyze_descriptions(
    request: DescriptionAnalysisRequest,
    description_analysis_service: "DescriptionAnalysisService" = Depends(
        get_description_analysis_service
    ),
) -> DescriptionAnalysisResponse:
    """
    Analyze description quality using AI.

    This endpoint:
    - Accepts ONLY descriptions + minimal context (NOT entire spec)
    - Analyzes quality (completeness, clarity, accuracy, best practices)
    - Returns quality scores + JSON Patch operations for improvements
    - Batches multiple descriptions in a single LLM call for efficiency

    Args:
        request: Description analysis request containing items to analyze.
        description_analysis_service: Injected description analysis service.

    Returns:
        DescriptionAnalysisResponse with quality scores and patches.

    Raises:
        HTTPException: If description analysis fails.
    """
    correlation_id = set_correlation_id()

    logger.info(
        f"Analyzing {len(request.items)} descriptions",
        extra={"correlation_id": correlation_id, "item_count": len(request.items)},
    )

    try:
        result = await description_analysis_service.analyze(request)

        logger.info(
            f"Description analysis completed with overall score: {result.overall_score}",
            extra={
                "correlation_id": correlation_id,
                "overall_score": result.overall_score,
                "patches_count": len(result.patches),
            },
        )

        return result

    except Exception as e:
        logger.exception(
            f"Description analysis failed: {str(e)}",
            extra={"correlation_id": correlation_id},
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "DESCRIPTION_ANALYSIS_FAILED",
                "message": "Failed to analyze description quality",
                "details": {"original_error": str(e)},
                "correlation_id": correlation_id,
            },
        )
