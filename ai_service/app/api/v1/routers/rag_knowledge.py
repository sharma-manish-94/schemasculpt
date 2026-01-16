"""
RAG Knowledge Base Router.

Provides endpoints for RAG (Retrieval-Augmented Generation) operations:
- Get knowledge base status and statistics
- Explain validation issues using knowledge base context
- Query the knowledge base for relevant security information

The RAG system enhances AI responses by retrieving relevant context from:
- OWASP security guidelines
- OpenAPI best practices
- Common vulnerability patterns
- Attack technique descriptions
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_llm_service, get_rag_service
from app.core.config import settings
from app.core.logging import set_correlation_id
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["RAG Knowledge Base"])

# Explanation cache (will be migrated to ICacheRepository)
EXPLANATION_CACHE: Dict[str, Dict[str, Any]] = {}
EXPLANATION_CACHE_TTL = timedelta(hours=settings.explanation_cache_ttl_hours)


# =============================================================================
# Knowledge Base Status
# =============================================================================


@router.get("/ai/rag/status")
async def get_rag_knowledge_base_status(
    rag_service: RAGService = Depends(get_rag_service),
) -> Dict[str, Any]:
    """
    Get status and statistics of the RAG knowledge base.

    Returns information about:
    - Knowledge base availability
    - Document counts per collection
    - Embedding model status
    - Last update timestamp

    Returns:
        Dictionary with RAG service status and statistics.
    """
    try:
        knowledge_base_stats = await rag_service.get_knowledge_base_stats()
        return {
            "rag_service": knowledge_base_stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as error:
        logger.error(f"Failed to get RAG knowledge base status: {str(error)}")
        return {
            "rag_service": {
                "available": False,
                "error": str(error),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }


# =============================================================================
# Validation Issue Explanation
# =============================================================================


@router.post("/ai/explain")
async def explain_validation_issue(
    request_data: Dict[str, Any],
    llm_service: LLMService = Depends(get_llm_service),
    rag_service: RAGService = Depends(get_rag_service),
) -> Dict[str, Any]:
    """
    Provide detailed AI-powered explanations for validation issues.

    Uses RAG to find relevant context and best practices from the
    knowledge base. Responses are cached for 24 hours to improve performance.

    Args:
        request_data: Dictionary containing:
            - rule_id (str): The validation rule identifier
            - message (str): The validation error message
            - category (str): Category of the issue (e.g., "security", "style")
            - spec_text (str, optional): Relevant spec excerpt
            - context (dict, optional): Additional context information

    Returns:
        Dictionary with:
            - explanation: Clear description of the issue
            - severity: Issue severity level
            - related_best_practices: List of relevant best practices
            - example_solutions: Concrete fix examples
            - additional_resources: Links to documentation
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
        cached_explanation = _get_cached_explanation(rule_id, message, category)
        if cached_explanation:
            logger.info(f"Returning cached explanation for rule: {rule_id}")
            return cached_explanation

        spec_text = request_data.get("spec_text", "")
        context = request_data.get("context", {})

        # Query RAG knowledge base for relevant context
        rag_query = f"OpenAPI best practices validation {rule_id} {category} {message}"
        context_data = await rag_service.retrieve_security_context(
            rag_query, n_results=3
        )

        # Build the explanation prompt
        knowledge_context = context_data.get(
            "context", "No additional context available"
        )
        if len(knowledge_context) > 800:
            knowledge_context = knowledge_context[:800] + "..."

        explanation_prompt = _build_explanation_prompt(
            rule_id, category, message, context, knowledge_context, spec_text
        )

        # Generate explanation using LLM
        explanation_response = await _generate_explanation(
            llm_service, explanation_prompt
        )

        # Cache the explanation
        _cache_explanation(rule_id, message, category, explanation_response)

        return explanation_response

    except Exception as error:
        logger.error(f"Failed to generate explanation: {str(error)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "EXPLANATION_GENERATION_FAILED",
                "message": f"Failed to generate explanation: {str(error)}",
            },
        )


# =============================================================================
# Helper Functions
# =============================================================================


def _build_explanation_prompt(
    rule_id: str,
    category: str,
    message: str,
    context: Dict[str, Any],
    knowledge_context: str,
    spec_text: str,
) -> str:
    """Build the prompt for generating validation issue explanations."""
    return f"""You are an OpenAPI expert. Explain this validation issue concisely and professionally.

VALIDATION ISSUE:
- Rule: {rule_id}
- Category: {category}
- Message: {message}
- Context: {json.dumps(context, indent=2) if context else "None"}

KNOWLEDGE BASE CONTEXT:
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


async def _generate_explanation(llm_service: LLMService, prompt: str) -> Dict[str, Any]:
    """Generate explanation using the LLM service."""
    payload = {
        "model": settings.default_model,
        "messages": [
            {
                "role": "system",
                "content": "You are an OpenAPI expert. Always respond with valid JSON only, no additional text.",
            },
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.3, "num_predict": 2048},
    }

    response = await llm_service.client.post(
        f"{settings.ollama_base_url}{settings.ollama_chat_endpoint}",
        json=payload,
        timeout=60.0,
    )

    if response.status_code != 200:
        raise Exception(f"LLM request failed with status {response.status_code}")

    response_json = response.json()
    content = response_json.get("message", {}).get("content", "")

    # Parse the JSON response
    try:
        explanation = json.loads(content)
        return explanation
    except json.JSONDecodeError:
        # Return a default structure if parsing fails
        return {
            "explanation": content,
            "severity": "info",
            "related_best_practices": [],
            "example_solutions": [],
            "additional_resources": [],
        }


def _generate_explanation_cache_key(rule_id: str, message: str, category: str) -> str:
    """Generate a unique cache key for an explanation."""
    import hashlib

    key_data = f"{rule_id}:{category}:{message}"
    return hashlib.md5(key_data.encode()).hexdigest()


def _get_cached_explanation(
    rule_id: str, message: str, category: str
) -> Dict[str, Any] | None:
    """Get cached explanation if available and not expired."""
    cache_key = _generate_explanation_cache_key(rule_id, message, category)
    cached = EXPLANATION_CACHE.get(cache_key)

    if not cached:
        return None

    # Check if expired
    if datetime.utcnow() - cached["timestamp"] > EXPLANATION_CACHE_TTL:
        del EXPLANATION_CACHE[cache_key]
        return None

    return cached["data"]


def _cache_explanation(
    rule_id: str, message: str, category: str, data: Dict[str, Any]
) -> None:
    """Store explanation in cache."""
    cache_key = _generate_explanation_cache_key(rule_id, message, category)
    EXPLANATION_CACHE[cache_key] = {
        "data": data,
        "timestamp": datetime.utcnow(),
    }
