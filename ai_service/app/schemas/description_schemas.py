"""
Schemas for AI-powered description quality analysis.
Only necessary context is sent to AI (NOT entire spec).
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class DescriptionContext(BaseModel):
    """Minimal context for understanding what the description is for"""
    method: Optional[str] = Field(None, description="For operations: GET, POST, etc.")
    schema_type: Optional[str] = Field(None, alias="schemaType", description="For schemas: object, array, etc.")
    property_names: Optional[List[str]] = Field(None, alias="propertyNames", description="For schemas: property names")
    operation_summary: Optional[str] = Field(None, alias="operationSummary", description="For operations: existing summary")
    status_code: Optional[int] = Field(None, alias="statusCode", description="For responses: 200, 404, etc.")

    class Config:
        populate_by_name = True


class DescriptionItem(BaseModel):
    """A single item to analyze (operation, schema, parameter, etc.)"""
    path: str = Field(..., description="JSON path: /paths/~1users~1{id}/get/description")
    type: str = Field(..., description="Type: operation, schema, parameter, response")
    current_description: Optional[str] = Field(None, alias="currentDescription", description="May be null/empty")
    context: DescriptionContext

    class Config:
        populate_by_name = True


class DescriptionAnalysisRequest(BaseModel):
    """Request containing descriptions to analyze (NOT entire spec)"""
    items: List[DescriptionItem]


class QualityLevel(str, Enum):
    """Quality level enum"""
    EXCELLENT = "EXCELLENT"  # 90-100
    GOOD = "GOOD"            # 70-89
    FAIR = "FAIR"            # 50-69
    POOR = "POOR"            # 1-49
    MISSING = "MISSING"      # 0 (no description)


class Issue(BaseModel):
    """A quality issue found in the description"""
    type: str = Field(..., description="completeness, clarity, accuracy, best_practice")
    severity: str = Field(..., description="high, medium, low")
    description: str = Field(..., description="Human-readable issue description")


class JsonPatchOperation(BaseModel):
    """JSON Patch operation (RFC 6902)"""
    op: str = Field(..., description="Operation: add, replace, remove")
    path: str = Field(..., description="JSON Pointer path")
    value: Optional[str] = Field(None, description="New value (for add/replace)")


class DescriptionQuality(BaseModel):
    """Quality analysis result for a single description"""
    path: str
    quality_score: int = Field(..., alias="qualityScore", ge=0, le=100)
    level: QualityLevel
    issues: List[Issue]
    suggested_description: str = Field(..., alias="suggestedDescription")
    patch: JsonPatchOperation

    class Config:
        populate_by_name = True


class DescriptionAnalysisResponse(BaseModel):
    """Response with quality scores and JSON Patch operations"""
    results: List[DescriptionQuality]
    overall_score: int = Field(..., alias="overallScore", ge=0, le=100)
    patches: List[JsonPatchOperation] = Field(..., description="All patches to apply improvements")

    class Config:
        populate_by_name = True
