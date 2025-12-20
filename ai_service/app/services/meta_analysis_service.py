"""
Meta-analysis service for linter-augmented AI analysis.
Connects dots between linter findings to detect higher-order patterns.
"""

import json
from typing import Any, List

from ..core.logging import get_logger
from ..schemas.meta_analysis_schemas import (
    AIInsight,
    AIMetaAnalysisRequest,
    AIMetaAnalysisResponse,
)

logger = get_logger("meta_analysis_service")


class MetaAnalysisService:
    """Service for performing AI meta-analysis on linter findings."""

    def __init__(self, llm_service):
        """
        Initialize with LLM service for AI reasoning.

        Args:
            llm_service: Instance of LLMService for AI-powered analysis
        """
        self.llm_service = llm_service
        self.logger = get_logger("meta_analysis_service")

    async def analyze(self, request: AIMetaAnalysisRequest) -> AIMetaAnalysisResponse:
        """
        Perform meta-analysis on linter findings to detect patterns and higher-order issues.

        Args:
            request: Contains spec text, errors, and linter suggestions

        Returns:
            AIMetaAnalysisResponse with insights, summary, and confidence score
        """
        self.logger.info(
            f"Starting meta-analysis with {len(request.errors)} errors, "
            f"{len(request.suggestions)} suggestions"
        )

        # Build the augmented prompt with linter findings
        prompt = self._build_meta_analysis_prompt(request)

        # Call LLM for pattern detection
        try:
            response_json = await self.llm_service.generate_json_response(
                prompt=prompt,
                schema_description="Return a JSON object with 'insights' (array), 'summary' (string), and 'confidenceScore' (number 0-1)",
                max_tokens=3072,
            )

            # Parse the LLM response
            response_data = json.loads(response_json)

            # Map to response schema
            insights = [
                AIInsight(
                    title=insight.get("title", "Untitled Insight"),
                    description=insight.get("description", ""),
                    severity=insight.get("severity", "info"),
                    category=insight.get("category", "general"),
                    affectedPaths=insight.get("affectedPaths", []),
                    relatedIssues=insight.get("relatedIssues", []),
                )
                for insight in response_data.get("insights", [])
            ]

            return AIMetaAnalysisResponse(
                insights=insights,
                summary=response_data.get("summary", "Analysis completed."),
                confidenceScore=response_data.get("confidenceScore", 0.7),
            )

        except Exception as e:
            self.logger.error(f"Meta-analysis failed: {str(e)}")
            # Return a fallback response
            return AIMetaAnalysisResponse(
                insights=[],
                summary=f"Meta-analysis encountered an error: {str(e)}",
                confidenceScore=0.0,
            )

    def _build_meta_analysis_prompt(self, request: AIMetaAnalysisRequest) -> str:
        """
        Build the augmented prompt for LLM meta-analysis.

        This is the key innovation: we give the AI both the spec AND the linter findings,
        so it can focus on higher-level reasoning rather than finding basic issues.
        """
        # Format errors and suggestions for the prompt
        errors_text = self._format_issues_for_prompt(
            request.errors, "Validation Errors"
        )
        suggestions_text = self._format_issues_for_prompt(
            request.suggestions, "Linter Suggestions"
        )

        prompt = f"""You are a senior security architect and API governance expert. Your task is to perform a meta-analysis of an OpenAPI specification that has already been analyzed by automated linters.

**Your Role:**
Instead of finding basic issues (the linters already did that), you need to:
1. Identify PATTERNS and COMBINATIONS of issues that indicate deeper problems
2. Detect security threats that arise from multiple issues together
3. Find design anti-patterns that span multiple endpoints
4. Identify governance violations and architectural concerns

**OpenAPI Specification:**
```json
{request.specText[:5000]}{"..." if len(request.specText) > 5000 else ""}
```

**Linter Findings:**

{errors_text}

{suggestions_text}

**Your Analysis Task:**
Analyze the linter findings in combination with the API specification. Look for:
- Security vulnerabilities (e.g., public endpoints returning PII, missing auth on sensitive operations)
- Design inconsistencies (e.g., inconsistent naming, missing patterns across similar endpoints)
- Performance concerns (e.g., missing pagination, lack of caching headers)
- Governance issues (e.g., undocumented breaking changes, missing standards compliance)

**Output Format (JSON):**
{{
  "insights": [
    {{
      "title": "Brief title of the insight",
      "description": "Detailed explanation of the pattern or issue found",
      "severity": "critical|high|medium|low|info",
      "category": "security|design|performance|governance",
      "affectedPaths": ["/path1", "/path2"],
      "relatedIssues": ["ruleId1", "ruleId2"]
    }}
  ],
  "summary": "One-paragraph summary of the overall API health and key concerns",
  "confidenceScore": 0.85
}}

**Important:**
- Only report insights where you've found meaningful PATTERNS or COMBINATIONS
- Don't just repeat individual linter findings
- Focus on actionable, high-value observations
- If no significant patterns found, return empty insights array
"""

        return prompt

    def _format_issues_for_prompt(self, issues: List[Any], title: str) -> str:
        """Format errors or suggestions for inclusion in the prompt."""
        if not issues:
            return f"**{title}:** None found.\n"

        formatted = [f"**{title}:**"]

        for i, issue in enumerate(
            issues[:20], 1
        ):  # Limit to first 20 to avoid token overflow
            if hasattr(issue, "message"):
                message = issue.message
                severity = getattr(issue, "severity", "unknown")
                rule_id = getattr(issue, "ruleId", None)
                path = getattr(issue, "path", None)

                issue_str = f"{i}. [{severity.upper()}]"
                if rule_id:
                    issue_str += f" [{rule_id}]"
                if path:
                    issue_str += f" at {path}:"
                issue_str += f" {message}"

                formatted.append(issue_str)

        if len(issues) > 20:
            formatted.append(f"... and {len(issues) - 20} more issues")

        return "\n".join(formatted) + "\n"
