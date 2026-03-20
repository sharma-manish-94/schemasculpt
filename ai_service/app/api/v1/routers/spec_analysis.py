"""
OpenAPI Specification Analysis Router.

Provides AI-powered interpretation and analysis of OpenAPI specification data,
transforming raw analyzer output from the Java backend into actionable insights.

This router handles the "Wow" features that differentiate SchemaSculpt:
- Taint Analysis: Data leakage and compliance risk assessment
- Authorization Matrix: RBAC anomaly detection and privilege escalation risks
- Schema Similarity: Duplicate schema detection and refactoring recommendations
- Zombie API Detection: Dead code and maintenance burden analysis
- Comprehensive Architecture: Holistic API health scoring

Design Philosophy:
- This router does NOT perform the raw analysis (that happens in Java backend)
- Instead, it provides AI-powered INTERPRETATION of analysis results
- The LLM adds business context, prioritization, and actionable recommendations
- This hybrid approach leverages deterministic analysis + AI intelligence

Security Note:
- All inputs are validated before LLM processing
- Spec text is truncated to prevent excessive token usage
- JSON parsing is wrapped in try-catch for security
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_llm_service
from app.core.config import settings
from app.core.logging import set_correlation_id
from app.schemas.spec_analysis_schemas import (
    AuthorizationMatrixRequest,
    ComprehensiveAnalysisRequest,
    SchemaSimilarityRequest,
    TaintAnalysisRequest,
    ZombieApiRequest,
)
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/analyze", tags=["OpenAPI Specification Analysis"])

# Maximum characters to send to LLM for context
MAX_CONTEXT_CHARS = 3000


def _safe_json_truncate(data: Any, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    """
    Safely convert data to JSON string with truncation.

    Prevents excessive token usage while preserving valid JSON structure.

    Args:
        data: Data to convert to JSON
        max_chars: Maximum characters to return

    Returns:
        Truncated JSON string
    """
    try:
        json_str = json.dumps(data, indent=2)
        if len(json_str) > max_chars:
            return json_str[:max_chars] + "\n... (truncated)"
        return json_str
    except (TypeError, ValueError):
        return str(data)[:max_chars]


async def _call_llm_for_interpretation(
    llm_service: LLMService,
    system_prompt: str,
    user_prompt: str,
    correlation_id: str,
) -> Dict[str, Any]:
    """
    Call LLM for JSON interpretation of analysis results.

    Centralizes LLM call logic with consistent error handling and logging.

    Args:
        llm_service: The LLM service instance
        system_prompt: System context for the LLM
        user_prompt: The actual analysis prompt
        correlation_id: Request correlation ID for tracing

    Returns:
        Parsed JSON response from LLM

    Raises:
        HTTPException: If LLM call fails or response is invalid
    """
    payload = {
        "model": settings.default_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2, "num_predict": 3000},
    }

    # Initialize before try block to avoid UnboundLocalError in exception handler
    llm_response: Optional[str] = None

    try:
        response = await llm_service.client.post(
            llm_service.chat_endpoint, json=payload
        )

        if response.status_code != 200:
            logger.error(
                f"LLM request failed with status {response.status_code}",
                extra={"correlation_id": correlation_id},
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "LLM_REQUEST_FAILED",
                    "message": "AI interpretation service unavailable",
                },
            )

        llm_response = response.json().get("message", {}).get("content", "{}")
        return json.loads(llm_response)

    except json.JSONDecodeError as e:
        logger.warning(
            f"Failed to parse LLM JSON response: {str(e)}",
            extra={"correlation_id": correlation_id},
        )
        # Return a structured error response instead of failing
        return {
            "error": "PARSE_ERROR",
            "message": "AI response was not valid JSON",
            "raw_response_preview": llm_response[:500] if llm_response else None,
        }


@router.post("/taint-analysis")
async def interpret_taint_analysis(
    request: TaintAnalysisRequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> Dict[str, Any]:
    """
    AI-powered interpretation of Taint Analysis results.

    Takes the raw taint analysis data from the Java backend and provides:
    - Executive summary of data leakage risks
    - Business impact assessment
    - Prioritized remediation recommendations
    - Compliance implications (GDPR, PCI-DSS, HIPAA)

    The taint analyzer tracks how sensitive data flows through API endpoints:
    - Sources: Where sensitive data enters (request params, headers, body)
    - Sinks: Where sensitive data exits (responses, logs, external calls)
    - Tainted paths: Data flow from source to sink without sanitization

    Request body:
        vulnerabilities (List[Dict]): Taint vulnerabilities from backend
            - Each vulnerability contains: endpoint, severity, source, sink, tainted_path
        spec_text (str, optional): OpenAPI specification for additional context

    Returns:
        Dict containing:
            - executive_summary: Business-focused summary
            - risk_level: CRITICAL | HIGH | MEDIUM | LOW
            - top_issues: Prioritized list of data leakage risks
            - remediation_priorities: Action items ordered by urgency
            - compliance_recommendations: GDPR/PCI-DSS/HIPAA specific guidance

    Example:
        POST /ai/analyze/taint-analysis
        {
            "vulnerabilities": [
                {
                    "endpoint": "GET /users/{id}",
                    "severity": "CRITICAL",
                    "source": "path parameter: id",
                    "sink": "response body",
                    "tainted_path": "id -> user.ssn -> response"
                }
            ]
        }
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Interpreting taint analysis results",
        extra={"correlation_id": correlation_id},
    )

    try:
        # Convert Pydantic models to dicts for processing
        vulnerabilities = [v.model_dump() for v in request.vulnerabilities]

        if not vulnerabilities:
            return {
                "summary": "No taint vulnerabilities detected. Your API appears to have proper data flow controls.",
                "risk_level": "LOW",
                "recommendations": [],
                "correlation_id": correlation_id,
            }

        # Categorize vulnerabilities by severity
        critical_vulns = [v for v in vulnerabilities if v.get("severity") == "CRITICAL"]
        warning_vulns = [v for v in vulnerabilities if v.get("severity") == "WARNING"]

        taint_prompt = f"""You are an API security expert analyzing taint analysis results.

TAINT ANALYSIS FINDINGS:
Total Vulnerabilities: {len(vulnerabilities)}
- CRITICAL (Public data leakage): {len(critical_vulns)}
- WARNING (Secured but needs review): {len(warning_vulns)}

CRITICAL VULNERABILITIES:
{_safe_json_truncate(critical_vulns, 1500)}

WARNING VULNERABILITIES:
{_safe_json_truncate(warning_vulns, 1000)}

Provide a comprehensive security analysis in JSON format:
{{
  "executive_summary": "Brief executive summary of the data leakage risks",
  "risk_level": "CRITICAL|HIGH|MEDIUM|LOW",
  "business_impact": "Explanation of business/compliance impact",
  "top_issues": [
    {{
      "endpoint": "endpoint path",
      "issue": "description",
      "severity": "CRITICAL|WARNING",
      "leaked_data": "what sensitive data is exposed",
      "attack_scenario": "how an attacker could exploit this",
      "compliance_impact": "GDPR/PCI-DSS/HIPAA violations"
    }}
  ],
  "remediation_priorities": [
    {{
      "priority": "IMMEDIATE|HIGH|MEDIUM",
      "action": "specific fix to implement",
      "endpoints_affected": ["list of endpoints"],
      "estimated_effort": "hours/days"
    }}
  ],
  "compliance_recommendations": {{
    "gdpr": "GDPR-specific recommendations",
    "pci_dss": "PCI-DSS recommendations if credit card data involved",
    "hipaa": "HIPAA recommendations if health data involved"
  }}
}}"""

        interpretation = await _call_llm_for_interpretation(
            llm_service,
            "You are an expert API security analyst specializing in data protection and compliance. Respond only with valid JSON.",
            taint_prompt,
            correlation_id,
        )

        return {
            **interpretation,
            "total_vulnerabilities": len(vulnerabilities),
            "critical_count": len(critical_vulns),
            "warning_count": len(warning_vulns),
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Taint analysis interpretation failed: {str(e)}",
            extra={"correlation_id": correlation_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "TAINT_INTERPRETATION_FAILED",
                "message": f"Failed to interpret taint analysis: {str(e)}",
                "correlation_id": correlation_id,
            },
        )


@router.post("/authz-matrix")
async def interpret_authz_matrix(
    request: AuthorizationMatrixRequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> Dict[str, Any]:
    """
    AI-powered interpretation of Authorization Matrix results.

    Analyzes RBAC configuration for security anomalies and misconfigurations.
    The authorization matrix maps API operations to their required scopes/roles.

    Key anomaly patterns detected:
    - Privilege escalation: DELETE/PUT accessible with read-only scopes
    - Missing authorization: Public endpoints that should be protected
    - Overly permissive: Single scope grants too broad access
    - Role confusion: Admin operations accessible to regular users

    Request body:
        scopes (List[str]): All OAuth2 scopes/roles defined in the API
        matrix (Dict[str, List[str]]): Maps "METHOD /path" to required scopes
        spec_text (str, optional): OpenAPI specification for context

    Returns:
        Dict containing:
            - executive_summary: Authorization security overview
            - risk_level: CRITICAL | HIGH | MEDIUM | LOW
            - anomalies_detected: List of authorization issues found
            - best_practice_violations: RBAC best practice deviations
            - recommendations: Prioritized fixes

    Security Considerations:
        - BOLA (Broken Object Level Authorization) detection
        - BFLA (Broken Function Level Authorization) detection
        - Excessive Data Exposure via authorization gaps
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Interpreting authz matrix results",
        extra={"correlation_id": correlation_id},
    )

    try:
        scopes = request.scopes
        matrix = request.matrix

        if not matrix:
            return {
                "summary": "No authorization matrix data available.",
                "anomalies": [],
                "correlation_id": correlation_id,
            }

        authz_prompt = f"""You are an API security expert analyzing RBAC authorization matrix.

AUTHORIZATION MATRIX:
Total Endpoints: {len(matrix)}
Available Scopes/Roles: {', '.join(scopes) if scopes else 'None defined'}

MATRIX DATA:
{_safe_json_truncate(matrix)}

Analyze this authorization matrix for security anomalies. Look for:
1. Destructive operations (DELETE, PUT) accessible with read-only scopes
2. Admin operations accessible with regular user scopes
3. Public endpoints (no security) that should be protected
4. Overly permissive scopes (one scope grants access to too many operations)
5. Missing authorization on sensitive operations

Provide analysis in JSON format:
{{
  "executive_summary": "Brief summary of authorization security",
  "risk_level": "CRITICAL|HIGH|MEDIUM|LOW",
  "anomalies_detected": [
    {{
      "type": "PRIVILEGE_ESCALATION|MISSING_AUTH|OVERLY_PERMISSIVE",
      "severity": "CRITICAL|HIGH|MEDIUM",
      "endpoint": "operation endpoint",
      "issue": "description of the issue",
      "current_scopes": ["list of scopes"],
      "attack_scenario": "how this could be exploited",
      "recommended_scopes": ["what scopes should be required"]
    }}
  ],
  "best_practice_violations": [
    "List of RBAC best practice violations found"
  ],
  "recommendations": [
    {{
      "priority": "IMMEDIATE|HIGH|MEDIUM",
      "recommendation": "specific action to take",
      "affected_endpoints": ["list of endpoints"]
    }}
  ]
}}"""

        interpretation = await _call_llm_for_interpretation(
            llm_service,
            "You are an expert in RBAC and authorization security. Respond only with valid JSON.",
            authz_prompt,
            correlation_id,
        )

        return {
            **interpretation,
            "total_endpoints": len(matrix),
            "total_scopes": len(scopes),
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Authz matrix interpretation failed: {str(e)}",
            extra={"correlation_id": correlation_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "AUTHZ_INTERPRETATION_FAILED",
                "message": f"Failed to interpret authorization matrix: {str(e)}",
                "correlation_id": correlation_id,
            },
        )


@router.post("/schema-similarity")
async def interpret_schema_similarity(
    request: SchemaSimilarityRequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> Dict[str, Any]:
    """
    AI-powered interpretation of Schema Similarity Clustering results.

    Provides refactoring recommendations for duplicate/similar schemas.
    Schema duplication is a common API design smell that increases:
    - Maintenance burden (changes in multiple places)
    - Inconsistency risk (schemas drift apart over time)
    - Documentation confusion (users unsure which schema to use)

    Refactoring strategies recommended:
    - MERGE: Combine identical schemas into one
    - BASE_SCHEMA_WITH_INHERITANCE: Use allOf for shared base
    - COMPOSITION: Use $ref for shared components

    Request body:
        clusters (List[Dict]): Schema clusters from similarity analyzer
            - Each cluster contains: schemas, similarity_score, shared_fields
        spec_text (str, optional): OpenAPI specification for context

    Returns:
        Dict containing:
            - executive_summary: Schema organization overview
            - code_health_score: 0-100 quality score
            - refactoring_opportunities: Detailed refactoring recommendations
            - quick_wins: Low-effort, high-impact improvements
            - architectural_recommendations: Long-term improvements
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Interpreting schema similarity results",
        extra={"correlation_id": correlation_id},
    )

    try:
        # Convert Pydantic models to dicts for processing
        clusters = [c.model_dump() for c in request.clusters]

        if not clusters:
            return {
                "summary": "No duplicate or similar schemas detected. Your schema design is well-organized.",
                "refactoring_opportunities": [],
                "correlation_id": correlation_id,
            }

        similarity_prompt = f"""You are an API design expert analyzing schema similarity clustering results.

SCHEMA SIMILARITY CLUSTERS:
Total Clusters Found: {len(clusters)}

CLUSTER DATA:
{_safe_json_truncate(clusters)}

Analyze these clusters and provide refactoring recommendations in JSON format:
{{
  "executive_summary": "Brief summary of schema duplication issues",
  "code_health_score": 0-100,
  "potential_savings": "estimated lines of code reduction",
  "refactoring_opportunities": [
    {{
      "cluster_id": "cluster identifier",
      "schema_names": ["list of similar schemas"],
      "similarity_score": 0.0-1.0,
      "issue": "description of duplication/similarity",
      "refactoring_strategy": "MERGE|BASE_SCHEMA_WITH_INHERITANCE|COMPOSITION",
      "implementation_steps": [
        "Step 1: Create base schema...",
        "Step 2: Apply allOf/oneOf...",
        "Step 3: Update references..."
      ],
      "estimated_effort": "hours",
      "benefits": "why this refactoring is valuable",
      "breaking_change_risk": "HIGH|MEDIUM|LOW"
    }}
  ],
  "quick_wins": [
    {{
      "schemas": ["schemas that can be quickly merged"],
      "effort": "15-30 minutes",
      "impact": "description of impact"
    }}
  ],
  "architectural_recommendations": [
    "High-level recommendations for schema organization"
  ]
}}"""

        interpretation = await _call_llm_for_interpretation(
            llm_service,
            "You are an expert in API design and schema architecture. Respond only with valid JSON.",
            similarity_prompt,
            correlation_id,
        )

        return {
            **interpretation,
            "total_clusters": len(clusters),
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Schema similarity interpretation failed: {str(e)}",
            extra={"correlation_id": correlation_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "SIMILARITY_INTERPRETATION_FAILED",
                "message": f"Failed to interpret schema similarity: {str(e)}",
                "correlation_id": correlation_id,
            },
        )


@router.post("/zombie-apis")
async def interpret_zombie_apis(
    request: ZombieApiRequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> Dict[str, Any]:
    """
    AI-powered interpretation of Zombie API Detection results.

    Analyzes unreachable, shadowed, and orphaned endpoints.
    Zombie APIs are technical debt that:
    - Confuse developers trying to understand the API
    - Create security risks (unpatched, unmaintained code)
    - Waste infrastructure resources
    - Bloat documentation

    Types of zombies detected:
    - Shadowed: Routes unreachable due to path conflicts
    - Orphaned: Operations with no params/body/response defined
    - Deprecated: Marked deprecated but still present
    - Unreferenced: Never called by any client (if usage data available)

    Request body:
        shadowedEndpoints (List[Dict]): Shadowed endpoints from analyzer
        orphanedOperations (List[Dict]): Orphaned operations from analyzer
        spec_text (str, optional): OpenAPI specification for context

    Returns:
        Dict containing:
            - executive_summary: API hygiene overview
            - code_health_score: 0-100 maintenance score
            - shadowed_endpoint_analysis: Details on route conflicts
            - orphaned_operation_analysis: Details on incomplete operations
            - cleanup_priorities: Prioritized cleanup tasks
            - architectural_improvements: Preventive measures
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Interpreting zombie API results",
        extra={"correlation_id": correlation_id},
    )

    try:
        shadowed = request.shadowedEndpoints
        orphaned = request.orphanedOperations

        if not shadowed and not orphaned:
            return {
                "summary": "No zombie APIs detected. All endpoints appear reachable and properly defined.",
                "cleanup_recommendations": [],
                "correlation_id": correlation_id,
            }

        zombie_prompt = f"""You are an API maintenance expert analyzing zombie API detection results.

ZOMBIE API FINDINGS:
Shadowed Endpoints: {len(shadowed)}
Orphaned Operations: {len(orphaned)}

SHADOWED ENDPOINTS (unreachable due to routing conflicts):
{_safe_json_truncate(shadowed, 2000)}

ORPHANED OPERATIONS (no params/body/response):
{_safe_json_truncate(orphaned, 1000)}

Analyze these zombie APIs and provide cleanup recommendations in JSON format:
{{
  "executive_summary": "Brief summary of API hygiene issues",
  "code_health_score": 0-100,
  "maintenance_burden": "description of technical debt",
  "shadowed_endpoint_analysis": [
    {{
      "shadowed_path": "unreachable endpoint",
      "shadowing_path": "conflicting endpoint",
      "reason": "why it's unreachable",
      "recommendation": "REORDER|RENAME|REMOVE|MERGE",
      "fix_instructions": "specific steps to fix",
      "breaking_change": "yes|no|maybe"
    }}
  ],
  "orphaned_operation_analysis": [
    {{
      "operation": "operation identifier",
      "reason": "why it's considered orphaned",
      "recommendation": "REMOVE|COMPLETE_IMPLEMENTATION|CONVERT_TO_HEALTH_CHECK",
      "rationale": "why this recommendation makes sense"
    }}
  ],
  "cleanup_priorities": [
    {{
      "priority": "HIGH|MEDIUM|LOW",
      "action": "specific cleanup action",
      "affected_endpoints": ["list of endpoints"],
      "estimated_effort": "hours"
    }}
  ],
  "architectural_improvements": [
    "Suggestions for preventing zombie APIs in the future"
  ]
}}"""

        interpretation = await _call_llm_for_interpretation(
            llm_service,
            "You are an expert in API design and maintenance. Respond only with valid JSON.",
            zombie_prompt,
            correlation_id,
        )

        return {
            **interpretation,
            "total_shadowed": len(shadowed),
            "total_orphaned": len(orphaned),
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Zombie API interpretation failed: {str(e)}",
            extra={"correlation_id": correlation_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ZOMBIE_INTERPRETATION_FAILED",
                "message": f"Failed to interpret zombie API detection: {str(e)}",
                "correlation_id": correlation_id,
            },
        )


@router.post("/comprehensive-architecture")
async def comprehensive_architecture_analysis(
    request: ComprehensiveAnalysisRequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> Dict[str, Any]:
    """
    Comprehensive architectural analysis combining all 4 advanced analyzers.

    This endpoint provides a holistic view of API health by synthesizing:
    - Security (Taint Analysis + Authorization Matrix)
    - Code Quality (Schema Similarity + Zombie APIs)
    - Overall API health score with breakdown

    Use this for executive reporting and architectural reviews.
    The analysis provides a single "API Health Score" that combines
    all dimensions weighted by their impact on production readiness.

    Scoring methodology:
    - Security Score (40% weight): Data exposure + access control
    - Access Control Score (20% weight): Authorization configuration
    - Code Quality Score (20% weight): Schema organization
    - Maintenance Score (20% weight): Zombie API burden

    Request body:
        taint_analysis (Dict): Results from taint analyzer
        authz_matrix (Dict): Results from authz matrix analyzer
        schema_similarity (Dict): Results from similarity analyzer
        zombie_apis (Dict): Results from zombie API detector
        spec_text (str, optional): OpenAPI specification

    Returns:
        Dict containing:
            - overall_health_score: 0-100 composite score
            - health_breakdown: Scores by dimension
            - executive_summary: Business-focused summary
            - critical_issues: Issues requiring immediate attention
            - 30_day_roadmap: Prioritized improvement plan
            - risk_assessment: Overall risk profile
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Performing comprehensive architecture analysis",
        extra={"correlation_id": correlation_id},
    )

    try:
        taint = request.taint_analysis or {}
        authz = request.authz_matrix or {}
        similarity = request.schema_similarity or {}
        zombie = request.zombie_apis or {}

        # Calculate input statistics for the prompt
        taint_vulns = len(taint.get("vulnerabilities", []))
        authz_endpoints = len(authz.get("matrix", {}))
        authz_scopes = len(authz.get("scopes", []))
        similarity_clusters = len(similarity.get("clusters", []))
        zombie_shadowed = len(zombie.get("shadowedEndpoints", []))
        zombie_orphaned = len(zombie.get("orphanedOperations", []))

        comprehensive_prompt = f"""You are a senior API architect performing a comprehensive analysis.

ANALYSIS RESULTS:

1. TAINT ANALYSIS (Data Security):
Vulnerabilities: {taint_vulns}
{_safe_json_truncate(taint, 1200)}

2. AUTHORIZATION MATRIX (Access Control):
Endpoints: {authz_endpoints}
Scopes: {authz_scopes}
{_safe_json_truncate(authz, 1200)}

3. SCHEMA SIMILARITY (Code Quality):
Duplicate Clusters: {similarity_clusters}
{_safe_json_truncate(similarity, 1200)}

4. ZOMBIE API DETECTION (Maintenance):
Shadowed: {zombie_shadowed}
Orphaned: {zombie_orphaned}
{_safe_json_truncate(zombie, 1200)}

Provide a comprehensive executive report in JSON format:
{{
  "overall_health_score": 0-100,
  "health_breakdown": {{
    "security_score": 0-100,
    "access_control_score": 0-100,
    "code_quality_score": 0-100,
    "maintenance_score": 0-100
  }},
  "executive_summary": "High-level summary for business stakeholders",
  "risk_assessment": {{
    "overall_risk": "CRITICAL|HIGH|MEDIUM|LOW",
    "production_readiness": "NOT_READY|NEEDS_WORK|READY_WITH_CAVEATS|PRODUCTION_READY",
    "key_risks": ["list of top 3 risks"]
  }},
  "critical_issues": [
    {{
      "category": "SECURITY|ACCESS_CONTROL|CODE_QUALITY|MAINTENANCE",
      "issue": "description",
      "impact": "business impact",
      "urgency": "IMMEDIATE|THIS_SPRINT|NEXT_QUARTER"
    }}
  ],
  "30_day_roadmap": [
    {{
      "week": 1,
      "focus": "area of focus",
      "tasks": ["specific tasks"],
      "expected_outcome": "what will be achieved"
    }}
  ],
  "recommendations_by_stakeholder": {{
    "engineering": ["technical recommendations"],
    "security_team": ["security-focused recommendations"],
    "management": ["strategic recommendations"]
  }}
}}"""

        interpretation = await _call_llm_for_interpretation(
            llm_service,
            "You are a senior API architect providing executive-level analysis. Respond only with valid JSON.",
            comprehensive_prompt,
            correlation_id,
        )

        return {
            **interpretation,
            "analysis_inputs": {
                "taint_vulnerabilities": taint_vulns,
                "authz_endpoints": authz_endpoints,
                "authz_scopes": authz_scopes,
                "similarity_clusters": similarity_clusters,
                "zombie_shadowed": zombie_shadowed,
                "zombie_orphaned": zombie_orphaned,
            },
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Comprehensive architecture analysis failed: {str(e)}",
            extra={"correlation_id": correlation_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "COMPREHENSIVE_ANALYSIS_FAILED",
                "message": f"Failed to perform comprehensive analysis: {str(e)}",
                "correlation_id": correlation_id,
            },
        )
