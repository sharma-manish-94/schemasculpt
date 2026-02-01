"""
Context Management Router.

Endpoints for managing conversation sessions and context.
These endpoints handle:
- Session creation and management
- Context statistics
- Session summaries and intelligent suggestions
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_context_manager

if TYPE_CHECKING:
    from app.services.context_manager import ContextManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/context", tags=["Context Management"])


@router.post("/session")
async def create_session(
    user_id: Optional[str] = None,
    context_manager: "ContextManager" = Depends(get_context_manager),
) -> Dict[str, Any]:
    """
    Create a new conversation session.

    Sessions are used to maintain context across multiple AI requests,
    enabling more coherent and contextually aware responses.

    Args:
        user_id: Optional user identifier for tracking.
        context_manager: Injected context manager.

    Returns:
        Dictionary containing the new session ID and metadata.
    """
    session_id = context_manager.create_session(user_id)

    return {
        "session_id": session_id,
        "user_id": user_id,
        "created_at": datetime.utcnow().isoformat(),
    }


@router.get("/session/{session_id}")
async def get_session_summary(
    session_id: str,
    context_manager: "ContextManager" = Depends(get_context_manager),
) -> Dict[str, Any]:
    """
    Get a summary of a conversation session.

    Returns the session summary along with intelligent suggestions
    for next actions based on the conversation history.

    Args:
        session_id: The session identifier.
        context_manager: Injected context manager.

    Returns:
        Dictionary containing session summary and suggestions.

    Raises:
        HTTPException: 404 if session not found.
    """
    try:
        summary = context_manager.get_session_summary(session_id)
        suggestions = context_manager.get_intelligent_suggestions(session_id, None)

        return {
            "session_summary": summary,
            "suggestions": suggestions,
        }
    except Exception:
        logger.warning(f"Session not found: {session_id}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "SESSION_NOT_FOUND",
                "message": f"Session {session_id} not found",
            },
        )


@router.get("/statistics")
async def get_context_statistics(
    context_manager: "ContextManager" = Depends(get_context_manager),
) -> Dict[str, Any]:
    """
    Get context management statistics.

    Returns metrics about session usage, conversation turns,
    and overall context management performance.

    Returns:
        Dictionary containing context statistics.
    """
    return context_manager.get_context_statistics()
