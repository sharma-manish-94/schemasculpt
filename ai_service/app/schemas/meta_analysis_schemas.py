"""
Schemas for AI meta-analysis of linter findings.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ValidationError(BaseModel):
    """Validation error from Java backend."""
    message: str
    severity: str
    path: Optional[str] = None
    context: Optional[dict] = None


class ValidationSuggestion(BaseModel):
    """Linter suggestion from Java backend."""
    message: str
    ruleId: Optional[str] = Field(None, alias="ruleId")
    severity: str
    category: str
    context: Optional[dict] = None
    explainable: bool = True

    model_config = {"populate_by_name": True}


class AIMetaAnalysisRequest(BaseModel):
    """Request for AI meta-analysis of linter findings."""
    specText: str = Field(..., description="The OpenAPI specification text")
    errors: List[ValidationError] = Field(default_factory=list)
    suggestions: List[ValidationSuggestion] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class AIInsight(BaseModel):
    """Individual AI-generated insight."""
    title: str
    description: str
    severity: str = Field(..., description="critical, high, medium, low, info")
    category: str = Field(..., description="security, design, performance, governance")
    affectedPaths: List[str] = Field(default_factory=list)
    relatedIssues: List[str] = Field(default_factory=list, description="Related linter ruleIds")

    model_config = {"populate_by_name": True}


class AIMetaAnalysisResponse(BaseModel):
    """Response from AI meta-analysis."""
    insights: List[AIInsight]
    summary: str
    confidenceScore: float = Field(..., ge=0.0, le=1.0)

    model_config = {"populate_by_name": True}
