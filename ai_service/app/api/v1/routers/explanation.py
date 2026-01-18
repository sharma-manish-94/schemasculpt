"""
Explanation Router.

Endpoints for AI-powered explanations of validation issues and suggestions.
Uses RAG (Retrieval-Augmented Generation) to provide context-aware explanations
with best practices from a knowledge base.
"""

import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_cache_repository, get_llm_service, get_rag_service
from app.core.config import settings
from app.core.logging import set_correlation_id

if TYPE_CHECKING:
    from app.domain.interfaces.cache_repository import ICacheRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["Explanation"])

# Cache key prefix for explanation cache
_CACHE_PREFIX = "explanation:"
_EXPLANATION_CACHE_TTL = timedelta(hours=settings.explanation_cache_ttl_hours)


def _generate_cache_key(rule_id: str, message: str, category: str) -> str:
    """Generate cache key for explanation."""
    key_data = f"{rule_id}:{category}:{message}"
    return f"{_CACHE_PREFIX}{hashlib.md5(key_data.encode()).hexdigest()}"


async def _get_cached_explanation(
    cache: "ICacheRepository",
    rule_id: str,
    message: str,
    category: str,
) -> Optional[Dict[str, Any]]:
    """Get cached explanation if available."""
    cache_key = _generate_cache_key(rule_id, message, category)
    cached = await cache.get(cache_key)

    if cached:
        logger.info(f"Returning cached explanation for rule {rule_id}")
        return cached

    return None


async def _cache_explanation(
    cache: "ICacheRepository",
    rule_id: str,
    message: str,
    category: str,
    data: Dict[str, Any],
) -> None:
    """Store explanation in cache."""
    cache_key = _generate_cache_key(rule_id, message, category)
    await cache.set(cache_key, data, ttl=_EXPLANATION_CACHE_TTL)


def _extract_json_from_response(llm_response: str) -> Optional[Dict[str, Any]]:
    """Extract and parse JSON from LLM response."""
    try:
        # Try to extract JSON from response
        json_start = llm_response.find("{")
        json_end = llm_response.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = llm_response[json_start:json_end]

            # Clean up common JSON issues
            json_str = re.sub(r",\s*]", "]", json_str)
            json_str = re.sub(r",\s*}", "}", json_str)
            json_str = re.sub(r'"\s*\n\s*"', '",\n"', json_str)

            result = json.loads(json_str)
            if isinstance(result, dict):
                return result

    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse JSON: {str(e)}")

    return None


def _manual_extraction(llm_response: str) -> Dict[str, Any]:
    """Manually extract structured data from LLM response as fallback."""
    result = {
        "explanation": "",
        "severity": "info",
        "related_best_practices": [],
        "example_solutions": [],
        "additional_resources": [],
    }

    try:
        # Extract explanation
        expl_match = re.search(
            r'"explanation"\s*:\s*"((?:[^"\\]|\\["\\])*)"', llm_response, re.DOTALL
        )
        if expl_match:
            result["explanation"] = (
                expl_match.group(1).replace('\\"', '"').replace("\\n", "\n")
            )

        # Extract severity
        sev_match = re.search(r'"severity"\s*:\s*"(\w+)"', llm_response)
        if sev_match:
            result["severity"] = sev_match.group(1)

        # Extract arrays helper
        def extract_array(field_name: str) -> list:
            array_match = re.search(
                rf'"{field_name}"\s*:\s*\[(.*?)\]', llm_response, re.DOTALL
            )
            if array_match:
                items_str = array_match.group(1)
                items = re.findall(r'"((?:[^"\\]|\\.)*)"', items_str)
                return [item.replace('\\"', '"') for item in items]
            return []

        result["related_best_practices"] = extract_array("related_best_practices")
        result["example_solutions"] = extract_array("example_solutions")
        result["additional_resources"] = extract_array("additional_resources")

        # If we couldn't extract explanation, use the whole response
        if not result["explanation"]:
            result["explanation"] = llm_response

    except Exception as e:
        logger.error(f"Manual extraction failed: {str(e)}")
        result["explanation"] = llm_response

    return result


@router.post("/explain")
async def explain_validation_issue(
    request_data: Dict[str, Any],
    llm_service=Depends(get_llm_service),
    rag_service=Depends(get_rag_service),
    cache: "ICacheRepository" = Depends(get_cache_repository),
) -> Dict[str, Any]:
    """
    Provide detailed AI-powered explanations for validation issues and suggestions.

    Uses RAG to find relevant context and best practices from the knowledge base.
    Responses are cached for performance optimization.

    Args:
        request_data: Dictionary containing rule_id, message, category, and optional context.
        llm_service: Injected LLM service.
        rag_service: Injected RAG service for knowledge retrieval.
        cache: Injected cache repository for caching explanations.

    Returns:
        Dictionary containing explanation, best practices, and solutions.

    Raises:
        HTTPException: If explanation generation fails.
    """
    correlation_id = set_correlation_id()

    rule_id = request_data.get("rule_id", "")
    message = request_data.get("message", "")
    category = request_data.get("category", "general")

    logger.info(
        "Generating explanation for validation issue",
        extra={
            "correlation_id": correlation_id,
            "rule_id": rule_id,
            "category": category,
        },
    )

    try:
        # Check cache first
        cached_explanation = await _get_cached_explanation(
            cache, rule_id, message, category
        )
        if cached_explanation:
            return cached_explanation

        spec_text = request_data.get("spec_text", "")
        context = request_data.get("context", {})

        # Create query for RAG knowledge base
        rag_query = f"OpenAPI best practices validation {rule_id} {category} {message}"

        # Retrieve relevant context from knowledge base
        context_data = await rag_service.retrieve_security_context(
            rag_query, n_results=3
        )

        # Build comprehensive explanation prompt
        knowledge_context = context_data.get(
            "context", "No additional context available"
        )
        if len(knowledge_context) > 800:
            knowledge_context = knowledge_context[:800] + "..."

        explanation_prompt = f"""You are an OpenAPI expert. Explain this validation issue concisely and professionally.

VALIDATION ISSUE:
- Rule: {rule_id}
- Category: {category}
- Message: {message}
- Context: {json.dumps(context, indent=2) if context else "None"}

KNOWLEDGE BASE:
{knowledge_context}

SPEC EXCERPT:
{spec_text[:500] if spec_text else "No specification provided"}

INSTRUCTIONS:
1. Provide a clear explanation of why this is an issue (2-3 sentences)
2. List 2-3 related best practices
3. Provide 1-2 specific example solutions
4. Suggest relevant resources (optional)

IMPORTANT: Respond ONLY with valid JSON. Do not include any text before or after the JSON.

{{
  "explanation": "Brief explanation of the issue and its impact",
  "severity": "info",
  "related_best_practices": [
    "First best practice",
    "Second best practice"
  ],
  "example_solutions": [
    "First solution approach",
    "Second solution approach"
  ],
  "additional_resources": [
    "Resource 1",
    "Resource 2"
  ]
}}"""

        # Call LLM
        payload = {
            "model": settings.default_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an OpenAPI expert. Always respond with valid JSON only.",
                },
                {"role": "user", "content": explanation_prompt},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.3, "num_predict": 2048},
        }

        response = await llm_service.client.post(
            llm_service.chat_endpoint, json=payload
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"LLM request failed: {response.status_code}",
            )

        # Extract response text
        response_data = response.json()
        llm_response = response_data.get("message", {}).get("content", "").strip()

        # Parse structured response
        structured_response = _extract_json_from_response(llm_response)
        if structured_response is None:
            logger.warning("JSON extraction failed, attempting manual extraction")
            structured_response = _manual_extraction(llm_response)

        # Build final response
        explanation_response = {
            "explanation": structured_response.get(
                "explanation", "Unable to generate explanation"
            ),
            "severity": structured_response.get("severity", "info"),
            "category": category,
            "related_best_practices": structured_response.get(
                "related_best_practices", []
            ),
            "example_solutions": structured_response.get("example_solutions", []),
            "additional_resources": structured_response.get("additional_resources", []),
            "metadata": {
                "rule_id": rule_id,
                "rag_sources": context_data.get("sources", []),
                "knowledge_base_available": rag_service.is_available(),
                "generated_at": datetime.utcnow().isoformat(),
            },
        }

        # Cache the explanation
        await _cache_explanation(
            cache, rule_id, message, category, explanation_response
        )

        logger.info(f"Generated explanation for rule {rule_id}")
        return explanation_response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Explanation generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "EXPLANATION_FAILED",
                "message": f"Failed to generate explanation: {str(e)}",
                "correlation_id": correlation_id,
            },
        )


@router.get("/rag/status")
async def get_rag_status(
    rag_service=Depends(get_rag_service),
) -> Dict[str, Any]:
    """
    Get status and statistics of the RAG knowledge base.

    Returns:
        Dictionary containing RAG service status and statistics.
    """
    try:
        stats = await rag_service.get_knowledge_base_stats()
        return {"rag_service": stats, "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Failed to get RAG status: {str(e)}")
        return {
            "rag_service": {
                "available": False,
                "error": "RAG service status is currently unavailable.",
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
