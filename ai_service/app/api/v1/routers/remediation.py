import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_llm_service
from app.schemas.remediation_schemas import SuggestFixRequest, SuggestFixResponse
from app.services.agents.remediation_agent import RemediationAgent
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai/remediate", tags=["Remediation"])


@router.post("/suggest-fix", response_model=SuggestFixResponse)
async def suggest_code_fix(
    request: SuggestFixRequest,
    llm_service: LLMService = Depends(get_llm_service),
):
    """
    Accepts a vulnerable code snippet and returns an AI-generated fix.
    """
    remediation_agent = RemediationAgent(llm_service)

    task = {
        "task_type": "suggest_fix",
        "vulnerable_code": request.vulnerable_code,
        "language": request.language,
        "vulnerability_type": request.vulnerability_type,
    }

    result = await remediation_agent.execute(task)

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Failed to generate fix."),
        )

    return SuggestFixResponse(suggested_fix=result.get("suggested_fix"))
