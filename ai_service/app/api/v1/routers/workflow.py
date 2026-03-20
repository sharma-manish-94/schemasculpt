"""
Workflow Router.

Endpoints for executing predefined and custom AI workflows.
These endpoints orchestrate complex multi-step AI operations.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_agent_manager
from app.core.logging import set_correlation_id

if TYPE_CHECKING:
    from app.services.agent_manager import AgentManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/workflow", tags=["Workflows"])


@router.post("/{workflow_name}")
async def execute_predefined_workflow(
    workflow_name: str,
    input_data: Dict[str, Any],
    agent_manager: "AgentManager" = Depends(get_agent_manager),
) -> Dict[str, Any]:
    """
    Execute a predefined workflow with custom input data.

    Workflows are named configurations that define a sequence of AI agents
    to execute for specific use cases.

    Args:
        workflow_name: Name of the predefined workflow to execute.
        input_data: Input data to pass to the workflow.
        agent_manager: Injected agent manager for workflow execution.

    Returns:
        Dictionary containing workflow execution results.

    Raises:
        HTTPException: 400 if workflow name is invalid, 500 if execution fails.
    """
    correlation_id = set_correlation_id()

    logger.info(
        f"Executing workflow: {workflow_name}",
        extra={"correlation_id": correlation_id, "workflow": workflow_name},
    )

    try:
        result = await agent_manager.execute_custom_workflow(workflow_name, input_data)
        return result

    except ValueError as e:
        logger.warning(f"Invalid workflow requested: {workflow_name}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_WORKFLOW",
                "message": str(e),
                "correlation_id": correlation_id,
            },
        )
    except Exception as e:
        logger.exception(f"Workflow execution failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "WORKFLOW_FAILED",
                "message": f"Workflow execution failed: {str(e)}",
                "correlation_id": correlation_id,
            },
        )


@router.post("/custom")
async def execute_custom_workflow(
    workflow_definition: Dict[str, Any],
    agent_manager: "AgentManager" = Depends(get_agent_manager),
) -> Dict[str, Any]:
    """
    Execute a custom ad-hoc workflow defined at runtime.

    Allows defining and executing one-off workflows without pre-registration.

    Args:
        workflow_definition: Workflow configuration including steps and parameters.
        agent_manager: Injected agent manager for workflow execution.

    Returns:
        Dictionary containing workflow execution results.

    Raises:
        HTTPException: If workflow execution fails.
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Executing custom workflow",
        extra={
            "correlation_id": correlation_id,
            "workflow_type": workflow_definition.get("workflow_type", "unknown"),
        },
    )

    try:
        result = await agent_manager.execute_ad_hoc_workflow(workflow_definition)
        return result

    except Exception as e:
        logger.exception(f"Custom workflow execution failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "CUSTOM_WORKFLOW_FAILED",
                "message": f"Custom workflow execution failed: {str(e)}",
                "correlation_id": correlation_id,
            },
        )


# Create a separate router for workflow listing (different prefix)
workflows_list_router = APIRouter(prefix="/ai", tags=["Workflows"])


@workflows_list_router.get("/workflows")
async def get_available_workflows(
    agent_manager: "AgentManager" = Depends(get_agent_manager),
) -> Dict[str, Any]:
    """
    Get the list of available predefined workflows.

    Returns:
        Dictionary containing available workflows and their descriptions.
    """
    return {
        "workflows": agent_manager.get_available_workflows(),
    }
