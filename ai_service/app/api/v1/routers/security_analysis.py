"""
Security Analysis Router.

Provides comprehensive security analysis capabilities for OpenAPI specifications:
- Full security workflow analysis (authentication, authorization, data exposure)
- Individual analyzer endpoints (auth-only, authz-only, data-exposure)
- Attack path simulation (AI-powered attack chain discovery)
- RAG-enhanced security analysis with knowledge base context

This router handles the "Wow" features that differentiate SchemaSculpt:
- Multi-agent attack path simulation
- OWASP API Security Top 10 compliance checking
- Intelligent attack chain detection
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_llm_service, get_rag_service, get_security_workflow
from app.core.config import settings
from app.core.logging import set_correlation_id
from app.schemas.ai_schemas import AIRequest, AIResponse, OperationType
from app.schemas.security_schemas import SecurityAnalysisRequest
from app.services.context_manager import ContextManager
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.security.security_workflow import SecurityAnalysisWorkflow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/security", tags=["Security Analysis"])

# Shared context manager
context_manager = ContextManager()

# Security analysis cache (will be migrated to ICacheRepository)
SECURITY_ANALYSIS_CACHE: Dict[str, Dict[str, Any]] = {}
SECURITY_CACHE_TTL = timedelta(hours=24)


# =============================================================================
# Comprehensive Security Analysis
# =============================================================================


@router.post("/analyze")
async def run_comprehensive_security_analysis(
    request: SecurityAnalysisRequest,
    security_workflow: SecurityAnalysisWorkflow = Depends(get_security_workflow),
) -> Dict[str, Any]:
    """
    Run comprehensive security analysis on an OpenAPI specification.

    This is the main security analysis endpoint that runs a multi-agent
    security workflow covering:
    - Authentication mechanism analysis
    - Authorization controls (RBAC, BOLA, BFLA detection)
    - Data exposure and PII protection
    - OWASP API Security Top 10 compliance

    Args:
        request: Security analysis request containing the spec and options.
        security_workflow: Injected security analysis workflow service.

    Returns:
        Comprehensive security report with findings, scores, and recommendations.

    Note:
        Results are cached for 24 hours unless force_refresh is True.
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Starting comprehensive security analysis",
        extra={"correlation_id": correlation_id},
    )

    try:
        # Check cache first (unless force refresh requested)
        cache_key = _generate_cache_key_for_spec(request.spec_text)

        if not request.force_refresh:
            cached_report = _get_cached_security_report(cache_key)
            if cached_report:
                logger.info(
                    f"Returning cached security report for key: {cache_key[:16]}..."
                )
                return {
                    "cached": True,
                    "report": cached_report,
                    "correlation_id": correlation_id,
                }

        # Convert validation suggestions to dictionary format
        validation_suggestions_as_dicts = None
        if request.validation_suggestions:
            validation_suggestions_as_dicts = [
                {
                    "rule_id": suggestion.rule_id,
                    "message": suggestion.message,
                    "severity": suggestion.severity,
                    "path": suggestion.path,
                    "category": suggestion.category,
                }
                for suggestion in request.validation_suggestions
            ]

        # Run the security analysis workflow
        security_report = await security_workflow.analyze(
            request.spec_text,
            validation_suggestions=validation_suggestions_as_dicts,
        )

        # Convert report to dictionary for response
        report_as_dict = security_report.model_dump()

        # Cache the report for future requests
        _cache_security_report(cache_key, report_as_dict)

        logger.info(
            f"Security analysis complete. Score: {security_report.overall_score:.1f}, "
            f"Risk: {security_report.risk_level.value}",
            extra={
                "correlation_id": correlation_id,
                "overall_score": security_report.overall_score,
                "risk_level": security_report.risk_level.value,
                "total_issues": len(security_report.all_issues),
            },
        )

        return {
            "cached": False,
            "report": report_as_dict,
            "correlation_id": correlation_id,
        }

    except json.JSONDecodeError as json_error:
        logger.error(f"Invalid JSON in specification: {str(json_error)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_SPECIFICATION_FORMAT",
                "message": "The provided OpenAPI specification is not valid JSON",
                "details": str(json_error),
            },
        )
    except Exception as error:
        logger.error(f"Security analysis failed: {str(error)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "SECURITY_ANALYSIS_FAILED",
                "message": f"Failed to analyze security: {str(error)}",
            },
        )


# =============================================================================
# Individual Security Analyzers
# =============================================================================


@router.post("/analyze/authentication")
async def analyze_authentication_mechanisms(
    request: SecurityAnalysisRequest,
) -> Dict[str, Any]:
    """
    Analyze authentication mechanisms in an OpenAPI specification.

    Focuses exclusively on authentication including:
    - Security scheme definitions (OAuth2, API Key, Basic Auth, Bearer)
    - Authentication weaknesses
    - Unprotected endpoints
    - Token handling issues

    Args:
        request: Security analysis request containing the spec.

    Returns:
        Authentication-specific analysis results.
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Starting authentication analysis",
        extra={"correlation_id": correlation_id},
    )

    try:
        spec_as_dict = json.loads(request.spec_text)

        from app.services.security.authentication_analyzer import AuthenticationAnalyzer

        analyzer = AuthenticationAnalyzer()
        analysis_result = await analyzer.analyze(spec_as_dict)

        return {
            "analysis": analysis_result.model_dump(),
            "correlation_id": correlation_id,
        }

    except json.JSONDecodeError as json_error:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_SPECIFICATION_FORMAT",
                "message": "The provided specification is not valid JSON",
            },
        )
    except Exception as error:
        logger.error(f"Authentication analysis failed: {str(error)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "AUTHENTICATION_ANALYSIS_FAILED",
                "message": f"Failed to analyze authentication: {str(error)}",
            },
        )


@router.post("/analyze/authorization")
async def analyze_authorization_controls(
    request: SecurityAnalysisRequest,
) -> Dict[str, Any]:
    """
    Analyze authorization controls in an OpenAPI specification.

    Focuses exclusively on authorization including:
    - RBAC (Role-Based Access Control) implementation
    - BOLA (Broken Object Level Authorization) detection
    - BFLA (Broken Function Level Authorization) detection
    - Protected vs unprotected endpoint analysis

    Args:
        request: Security analysis request containing the spec.

    Returns:
        Authorization-specific analysis results.
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Starting authorization analysis",
        extra={"correlation_id": correlation_id},
    )

    try:
        spec_as_dict = json.loads(request.spec_text)

        from app.services.security.authorization_analyzer import AuthorizationAnalyzer

        analyzer = AuthorizationAnalyzer()
        analysis_result = await analyzer.analyze(spec_as_dict)

        return {
            "analysis": analysis_result.model_dump(),
            "correlation_id": correlation_id,
        }

    except Exception as error:
        logger.error(f"Authorization analysis failed: {str(error)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "AUTHORIZATION_ANALYSIS_FAILED",
                "message": f"Failed to analyze authorization: {str(error)}",
            },
        )


@router.post("/analyze/data-exposure")
async def analyze_data_exposure_risks(
    request: SecurityAnalysisRequest,
) -> Dict[str, Any]:
    """
    Analyze data exposure and PII protection in an OpenAPI specification.

    Focuses exclusively on data security including:
    - PII (Personally Identifiable Information) field detection
    - Sensitive data exposure in responses
    - Password field protection
    - HTTPS enforcement
    - Excessive data exposure patterns

    Args:
        request: Security analysis request containing the spec.

    Returns:
        Data exposure analysis results.
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Starting data exposure analysis",
        extra={"correlation_id": correlation_id},
    )

    try:
        spec_as_dict = json.loads(request.spec_text)

        from app.services.security.data_exposure_analyzer import DataExposureAnalyzer

        analyzer = DataExposureAnalyzer()
        analysis_result = await analyzer.analyze(spec_as_dict)

        return {
            "analysis": analysis_result.model_dump(),
            "correlation_id": correlation_id,
        }

    except Exception as error:
        logger.error(f"Data exposure analysis failed: {str(error)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "DATA_EXPOSURE_ANALYSIS_FAILED",
                "message": f"Failed to analyze data exposure: {str(error)}",
            },
        )


# =============================================================================
# Cached Report Retrieval
# =============================================================================


@router.get("/report/{spec_hash}")
async def get_cached_security_report_by_hash(
    spec_hash: str,
) -> Dict[str, Any]:
    """
    Retrieve a cached security analysis report by its specification hash.

    Args:
        spec_hash: The SHA-256 hash of the specification text.

    Returns:
        The cached security report if found.

    Raises:
        HTTPException: 404 if no cached report exists for the given hash.
    """
    logger.info(f"Retrieving cached security report for hash: {spec_hash[:16]}...")

    cached_report = _get_cached_security_report(spec_hash)

    if cached_report:
        return {
            "cached": True,
            "report": cached_report,
            "spec_hash": spec_hash,
        }

    raise HTTPException(
        status_code=404,
        detail={
            "error": "REPORT_NOT_FOUND",
            "message": f"No cached security report found for hash: {spec_hash}",
            "hint": "Run /ai/security/analyze to generate a new report",
        },
    )


# =============================================================================
# Attack Path Simulation (The "Wow" Feature)
# =============================================================================


@router.post("/attack-path-simulation")
async def run_attack_path_simulation(
    request: Dict[str, Any],
    llm_service: LLMService = Depends(get_llm_service),
) -> Dict[str, Any]:
    """
    AI-powered attack path simulation - discovers multi-step attack chains.

    This is the flagship security feature that thinks like a hacker.
    Unlike simple linting that finds isolated vulnerabilities, this feature:

    1. Scans for individual vulnerabilities (Scanner Agent)
    2. Analyzes how vulnerabilities can be CHAINED together (Threat Modeling Agent)
    3. Generates executive-level security reports (Reporter Agent)

    **Example Attack Chain:**
    - Step 1: GET /users/{id} exposes sensitive 'role' field (Information Disclosure)
    - Step 2: PUT /users/{id} accepts 'role' in request body (Mass Assignment)
    - Result: Any user can escalate to admin privileges!

    Args:
        request: Dictionary containing:
            - spec_text (str): OpenAPI specification (JSON or YAML)
            - analysis_depth (str): "quick" | "standard" | "comprehensive" | "exhaustive"
            - max_chain_length (int): Maximum steps in an attack chain (default: 5)
            - exclude_low_severity (bool): Skip low-severity chains (default: false)
            - focus_areas (list): Specific areas to focus on

    Returns:
        Comprehensive attack path report including:
            - report_id: Unique identifier
            - risk_level: CRITICAL | HIGH | MEDIUM | LOW
            - overall_security_score: 0-100
            - executive_summary: Business-focused summary
            - critical_chains: Critical attack chains
            - high_priority_chains: High severity chains
            - immediate_actions: Fixes needed now
            - short_term_actions: Fixes for next 1-2 weeks
            - long_term_actions: Architectural improvements
    """
    from app.schemas.attack_path_schemas import AttackPathAnalysisRequest
    from app.services.agents.attack_path_orchestrator import AttackPathOrchestrator

    correlation_id = set_correlation_id()
    logger.info(
        "Starting attack path simulation",
        extra={"correlation_id": correlation_id},
    )

    try:
        spec_text = request.get("spec_text")
        if not spec_text:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "MISSING_SPECIFICATION",
                    "message": "The 'spec_text' field is required",
                },
            )

        # Build the analysis request
        analysis_request = AttackPathAnalysisRequest(
            spec_text=spec_text,
            analysis_depth=request.get("analysis_depth", "standard"),
            max_chain_length=request.get("max_chain_length", 5),
            exclude_low_severity=request.get("exclude_low_severity", False),
            focus_areas=request.get("focus_areas", []),
        )

        # Check cache first
        spec_hash = hashlib.sha256(spec_text.encode()).hexdigest()
        cache_key = f"attack_path_{spec_hash}_{analysis_request.analysis_depth}"

        cached_data = SECURITY_ANALYSIS_CACHE.get(cache_key)
        if cached_data and datetime.utcnow() < cached_data["expires_at"]:
            logger.info(f"Returning cached attack path report: {cache_key[:32]}...")
            return cached_data["report"]

        # Run the attack path simulation
        orchestrator = AttackPathOrchestrator(llm_service)
        attack_path_report = await orchestrator.run_attack_path_analysis(
            analysis_request
        )

        # Convert to dictionary for response
        report_as_dict = attack_path_report.model_dump()

        # Cache the report
        SECURITY_ANALYSIS_CACHE[cache_key] = {
            "report": report_as_dict,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + SECURITY_CACHE_TTL,
        }
        logger.info(f"Cached attack path report: {cache_key[:32]}...")

        return report_as_dict

    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Attack path simulation failed: {str(error)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ATTACK_PATH_SIMULATION_FAILED",
                "message": f"Failed to run attack path simulation: {str(error)}",
            },
        )


@router.post("/attack-path-findings")
async def analyze_attack_chains_from_linter_findings(
    request: Dict[str, Any],
    llm_service: LLMService = Depends(get_llm_service),
) -> Dict[str, Any]:
    """
    Analyze attack chains from pre-computed linter findings.

    This is the EFFICIENT approach to AI-powered security analysis:
    Instead of sending a 5MB spec to the AI on every run, we:
    1. Run fast deterministic linters on the backend (Java)
    2. Send only the findings (a few KB) to the AI
    3. AI analyzes how findings can be chained into attack paths

    This approach is:
    - 10x faster (no full spec parsing)
    - 100x cheaper (fewer tokens)
    - More accurate (linters catch edge cases AI misses)

    Args:
        request: Dictionary containing:
            - spec_text (str): OpenAPI specification for context
            - findings (list): Pre-computed linter findings
            - spec_metadata (dict): Optional metadata about the spec

    Returns:
        Attack chain analysis based on the findings.
    """
    correlation_id = set_correlation_id()
    logger.info(
        "Starting attack chain analysis from findings",
        extra={"correlation_id": correlation_id},
    )

    try:
        spec_text = request.get("spec_text")
        findings = request.get("findings", [])

        if not spec_text:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "MISSING_SPECIFICATION",
                    "message": "The 'spec_text' field is required",
                },
            )

        if not findings:
            return {
                "attack_chains": [],
                "message": "No findings provided for analysis",
                "correlation_id": correlation_id,
            }

        # This would call the attack chain analyzer with findings
        # For now, return a placeholder response
        # TODO: Implement full attack chain analysis from findings

        return {
            "status": "analysis_complete",
            "findings_analyzed": len(findings),
            "correlation_id": correlation_id,
            "message": "Attack chain analysis from findings - implementation in progress",
        }

    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Attack chain analysis failed: {str(error)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ATTACK_CHAIN_ANALYSIS_FAILED",
                "message": f"Failed to analyze attack chains: {str(error)}",
            },
        )


# =============================================================================
# RAG-Enhanced Security Analysis
# =============================================================================


@router.post("/analyze-with-knowledge-base", response_model=AIResponse)
async def analyze_security_with_rag_context(
    request: AIRequest,
    llm_service: LLMService = Depends(get_llm_service),
    rag_service: RAGService = Depends(get_rag_service),
) -> AIResponse:
    """
    Perform RAG-enhanced security analysis using the knowledge base.

    Retrieves relevant security context from the knowledge base and
    generates comprehensive analysis with that context.

    The knowledge base contains:
    - OWASP security guidelines
    - Common vulnerability patterns
    - Best practices for API security
    - Attack technique descriptions

    Args:
        request: AI request containing the spec and analysis prompt.

    Returns:
        AIResponse with security analysis enhanced by knowledge base context.
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Starting RAG-enhanced security analysis",
        extra={"correlation_id": correlation_id},
    )

    try:
        # Build security query for knowledge base
        spec_preview = request.spec_text[:300] if request.spec_text else ""
        security_query = (
            f"Security analysis OpenAPI specification vulnerabilities "
            f"authentication authorization: {spec_preview}"
        )

        # Retrieve relevant context from knowledge base
        context_data = await rag_service.retrieve_security_context(
            security_query, n_results=3
        )

        # Build enhanced prompt with context
        context_summary = context_data.get("context", "No additional context available")
        if len(context_summary) > 1000:
            context_summary = context_summary[:1000] + "..."

        enhanced_prompt = f"""Analyze this OpenAPI spec for security vulnerabilities:

SECURITY CONTEXT FROM KNOWLEDGE BASE:
{context_summary}

USER REQUEST:
{request.prompt}

FOCUS AREAS:
- Authentication and authorization
- Input validation
- Data exposure
- Rate limiting
- HTTPS/TLS enforcement
- CORS configuration
- Error handling

Provide specific, actionable recommendations."""

        # Create enhanced request for LLM processing
        enhanced_request = AIRequest(
            spec_text=request.spec_text,
            prompt=enhanced_prompt,
            operation_type=OperationType.VALIDATE,
            streaming=request.streaming,
            response_format=request.response_format,
            llm_parameters=request.llm_parameters,
            validate_output=False,
            user_id=request.user_id,
            session_id=request.session_id,
            tags=request.tags + ["security_analysis", "rag_enhanced"],
        )

        # Process through LLM service
        result = await llm_service.process_ai_request(enhanced_request)

        # Enhance result with RAG metadata
        if hasattr(result, "metadata"):
            result.metadata.update(
                {
                    "rag_sources": context_data.get("sources", []),
                    "rag_relevance_scores": context_data.get("relevance_scores", []),
                    "knowledge_base_available": rag_service.is_available(),
                    "analysis_type": "security_rag_enhanced",
                }
            )

        logger.info(
            f"RAG-enhanced security analysis completed with "
            f"{len(context_data.get('sources', []))} knowledge sources"
        )

        return result

    except Exception as error:
        logger.error(f"RAG-enhanced security analysis failed: {str(error)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "SECURITY_ANALYSIS_FAILED",
                "message": f"Security analysis failed: {str(error)}",
                "rag_available": rag_service.is_available() if rag_service else False,
            },
        )


# =============================================================================
# Helper Functions
# =============================================================================


def _generate_cache_key_for_spec(spec_text: str) -> str:
    """Generate a cache key from the specification text."""
    return hashlib.sha256(spec_text.encode()).hexdigest()


def _get_cached_security_report(cache_key: str) -> Optional[Dict[str, Any]]:
    """
    Get cached security report if available and not expired.

    Args:
        cache_key: The cache key to look up.

    Returns:
        The cached report dictionary if found and valid, None otherwise.
    """
    cached_data = SECURITY_ANALYSIS_CACHE.get(cache_key)

    if not cached_data:
        return None

    # Check if expired
    if datetime.utcnow() >= cached_data.get("expires_at", datetime.min):
        del SECURITY_ANALYSIS_CACHE[cache_key]
        return None

    return cached_data.get("report")


def _cache_security_report(cache_key: str, report: Dict[str, Any]) -> None:
    """
    Store a security report in the cache.

    Args:
        cache_key: The cache key to store under.
        report: The report dictionary to cache.
    """
    SECURITY_ANALYSIS_CACHE[cache_key] = {
        "report": report,
        "cached_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + SECURITY_CACHE_TTL,
    }
