"""
AI-powered description quality analysis service.
Analyzes description quality and generates JSON Patch operations for improvements.
"""
import logging
from typing import List
from app.schemas.description_schemas import (
    DescriptionAnalysisRequest,
    DescriptionAnalysisResponse,
    DescriptionQuality,
    DescriptionItem,
    Issue,
    JsonPatchOperation,
    QualityLevel
)
from app.services.llm_adapter import LLMAdapter

logger = logging.getLogger(__name__)


class DescriptionAnalysisService:
    def __init__(self, llm_adapter: LLMAdapter):
        self.llm_adapter = llm_adapter

    async def analyze(self, request: DescriptionAnalysisRequest) -> DescriptionAnalysisResponse:
        """
        Analyze description quality for multiple items in batch.
        Returns quality scores, issues, and JSON Patch operations.
        """
        logger.info(f"Analyzing {len(request.items)} descriptions")

        # Batch analyze all descriptions in a single LLM call
        results = await self._batch_analyze_descriptions(request.items)

        # Calculate overall score
        overall_score = self._calculate_overall_score(results)

        # Collect all patches
        patches = [result.patch for result in results]

        logger.info(f"Description analysis complete. Overall score: {overall_score}")
        return DescriptionAnalysisResponse(
            results=results,
            overall_score=overall_score,
            patches=patches
        )

    async def _batch_analyze_descriptions(
        self, items: List[DescriptionItem]
    ) -> List[DescriptionQuality]:
        """Batch analyze descriptions in a single LLM call for efficiency"""

        # Build prompt with all items
        prompt = self._build_batch_analysis_prompt(items)

        # Call LLM once for all descriptions
        llm_response = await self.llm_adapter.generate(
            prompt=prompt,
            max_tokens=4000,
            temperature=0.3  # Lower temperature for more consistent quality analysis
        )

        # Parse LLM response and create results
        results = self._parse_llm_response(llm_response, items)

        return results

    def _build_batch_analysis_prompt(self, items: List[DescriptionItem]) -> str:
        """Build a single prompt to analyze all descriptions"""

        prompt = """You are an API documentation quality analyzer. Analyze the following descriptions and provide:
1. Quality score (0-100)
2. Issues found (completeness, clarity, accuracy, best practices)
3. Improved description

**Scoring Criteria:**
- 90-100 (EXCELLENT): Complete, clear, accurate, follows best practices
- 70-89 (GOOD): Mostly complete, generally clear, minor issues
- 50-69 (FAIR): Incomplete or unclear, needs improvement
- 1-49 (POOR): Very incomplete or misleading
- 0 (MISSING): No description provided

**Best Practices:**
- Describe WHAT the operation/schema does (not HOW)
- Use imperative mood for operations ("Retrieve user", not "Retrieves user")
- Mention key parameters and return values
- Be concise but complete (1-3 sentences)
- Avoid redundant information already in summary

**Descriptions to analyze:**

"""

        for i, item in enumerate(items, 1):
            prompt += f"\n### Item {i}\n"
            prompt += f"Path: {item.path}\n"
            prompt += f"Type: {item.type}\n"

            # Add context
            if item.context.method:
                prompt += f"Method: {item.context.method}\n"
            if item.context.operation_summary:
                prompt += f"Summary: {item.context.operation_summary}\n"
            if item.context.schema_type:
                prompt += f"Schema Type: {item.context.schema_type}\n"
            if item.context.property_names:
                prompt += f"Properties: {', '.join(item.context.property_names[:10])}\n"  # Max 10 properties
            if item.context.status_code:
                prompt += f"Status Code: {item.context.status_code}\n"

            current = item.current_description or "(missing)"
            prompt += f"Current Description: {current}\n"

        prompt += """

**For EACH item, respond in this exact format:**

ITEM_1:
SCORE: <0-100>
LEVEL: <EXCELLENT|GOOD|FAIR|POOR|MISSING>
ISSUES:
- [type: <completeness|clarity|accuracy|best_practice>] [severity: <high|medium|low>] <description>
- ...
SUGGESTED: <improved description here>
---

ITEM_2:
...

Be concise and actionable. Focus on practical improvements."""

        return prompt

    def _parse_llm_response(
        self, llm_response: str, items: List[DescriptionItem]
    ) -> List[DescriptionQuality]:
        """
        Parse LLM response and create DescriptionQuality objects with JSON patches.
        Falls back to rule-based analysis if LLM response is invalid.
        """
        results = []

        try:
            # Split response by item markers
            item_blocks = llm_response.split("ITEM_")[1:]  # Skip before first ITEM_

            for i, (block, item) in enumerate(zip(item_blocks, items)):
                try:
                    result = self._parse_single_item(block, item)
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Failed to parse item {i+1}, using fallback: {e}")
                    # Fallback to rule-based analysis
                    results.append(self._fallback_analysis(item))

        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            # Fallback: analyze all items with rules
            for item in items:
                results.append(self._fallback_analysis(item))

        return results

    def _parse_single_item(self, block: str, item: DescriptionItem) -> DescriptionQuality:
        """Parse a single item block from LLM response"""
        lines = block.strip().split("\n")

        score = 0
        level = QualityLevel.MISSING
        issues = []
        suggested = ""

        for line in lines:
            line = line.strip()

            if line.startswith("SCORE:"):
                try:
                    score = int(line.split(":")[1].strip())
                except:
                    score = 0

            elif line.startswith("LEVEL:"):
                level_str = line.split(":")[1].strip()
                level = QualityLevel(level_str)

            elif line.startswith("- [type:"):
                # Parse issue: - [type: completeness] [severity: high] Missing parameter details
                issue = self._parse_issue_line(line)
                if issue:
                    issues.append(issue)

            elif line.startswith("SUGGESTED:"):
                suggested = line.split(":", 1)[1].strip()

        # Create JSON Patch operation
        patch = JsonPatchOperation(
            op="replace" if item.current_description else "add",
            path=item.path,
            value=suggested
        )

        return DescriptionQuality(
            path=item.path,
            quality_score=score,
            level=level,
            issues=issues,
            suggested_description=suggested,
            patch=patch
        )

    def _parse_issue_line(self, line: str) -> Issue | None:
        """Parse an issue line: - [type: completeness] [severity: high] Missing parameter details"""
        try:
            # Extract type
            type_start = line.find("[type:") + 6
            type_end = line.find("]", type_start)
            issue_type = line[type_start:type_end].strip()

            # Extract severity
            sev_start = line.find("[severity:") + 10
            sev_end = line.find("]", sev_start)
            severity = line[sev_start:sev_end].strip()

            # Extract description (after second ])
            desc = line[sev_end + 1:].strip()

            return Issue(type=issue_type, severity=severity, description=desc)
        except:
            return None

    def _fallback_analysis(self, item: DescriptionItem) -> DescriptionQuality:
        """Rule-based fallback when LLM fails"""
        current = item.current_description or ""

        if not current or len(current.strip()) == 0:
            # Missing description
            suggested = self._generate_fallback_description(item)
            return DescriptionQuality(
                path=item.path,
                quality_score=0,
                level=QualityLevel.MISSING,
                issues=[Issue(
                    type="completeness",
                    severity="high",
                    description="Description is missing"
                )],
                suggested_description=suggested,
                patch=JsonPatchOperation(op="add", path=item.path, value=suggested)
            )

        elif len(current) < 20:
            # Too short
            suggested = self._enhance_short_description(current, item)
            return DescriptionQuality(
                path=item.path,
                quality_score=40,
                level=QualityLevel.POOR,
                issues=[Issue(
                    type="completeness",
                    severity="medium",
                    description="Description is too brief"
                )],
                suggested_description=suggested,
                patch=JsonPatchOperation(op="replace", path=item.path, value=suggested)
            )

        else:
            # Acceptable
            return DescriptionQuality(
                path=item.path,
                quality_score=70,
                level=QualityLevel.GOOD,
                issues=[],
                suggested_description=current,
                patch=JsonPatchOperation(op="replace", path=item.path, value=current)
            )

    def _generate_fallback_description(self, item: DescriptionItem) -> str:
        """Generate a basic description when missing"""
        if item.type == "operation" and item.context.method:
            method = item.context.method
            path_name = item.path.split("/")[-2]  # Extract operation name from path
            return f"{method} operation for {path_name}"

        elif item.type == "schema":
            schema_name = item.path.split("/")[-2]
            return f"Schema representing a {schema_name}"

        return "Description needed"

    def _enhance_short_description(self, current: str, item: DescriptionItem) -> str:
        """Enhance a short description with context"""
        if item.context.method:
            return f"{current}. {item.context.method} operation."
        return f"{current}. Please provide more details."

    def _calculate_overall_score(self, results: List[DescriptionQuality]) -> int:
        """Calculate weighted overall score"""
        if not results:
            return 0

        total_score = sum(r.quality_score for r in results)
        return total_score // len(results)
