"""
Base Agent class for SchemaSculpt AI Agentic System.
Provides the foundation for specialized agents with common functionality.
"""

import asyncio
import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from ...core.exceptions import LLMError
from ...core.logging import get_logger
from ...schemas.ai_schemas import LLMParameters


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents in the SchemaSculpt system.
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.agent_id = str(uuid4())
        self.logger = get_logger(f"agent.{name}")

        # Agent state
        self._is_busy = False
        self._execution_count = 0
        self._total_tokens_used = 0
        self._total_execution_time = 0.0

        # Agent capabilities
        self.capabilities = self._define_capabilities()

    @abstractmethod
    def _define_capabilities(self) -> List[str]:
        """Define the specific capabilities of this agent."""
        pass

    @abstractmethod
    async def execute(
        self, task: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the agent's primary task."""
        pass

    async def _pre_execution_hook(self, task: Dict[str, Any]) -> None:
        """Hook called before task execution."""
        self._is_busy = True
        self._execution_count += 1
        self.logger.info(
            f"Agent {self.name} starting execution #{self._execution_count}"
        )

    async def _post_execution_hook(
        self, result: Dict[str, Any], execution_time: float
    ) -> None:
        """Hook called after task execution."""
        self._is_busy = False
        self._total_execution_time += execution_time
        self.logger.info(
            f"Agent {self.name} completed execution in {execution_time:.2f}s"
        )

    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "is_busy": self._is_busy,
            "execution_count": self._execution_count,
            "total_tokens_used": self._total_tokens_used,
            "total_execution_time": self._total_execution_time,
            "average_execution_time": (
                self._total_execution_time / self._execution_count
                if self._execution_count > 0
                else 0
            ),
        }

    def can_handle_task(self, task_type: str) -> bool:
        """Check if this agent can handle the given task type."""
        return task_type in self.capabilities

    async def validate_task(self, task: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate if the task is properly formatted for this agent."""
        required_fields = self._get_required_task_fields()

        for field in required_fields:
            if field not in task:
                return False, f"Missing required field: {field}"

        return True, None

    def _get_required_task_fields(self) -> List[str]:
        """Get the required fields for this agent's tasks."""
        return ["task_type", "input_data"]

    def _create_success_result(
        self, data: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a standardized success result."""
        return {
            "success": True,
            "agent": self.name,
            "agent_id": self.agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "metadata": metadata or {},
        }

    def _create_error_result(
        self, error: str, error_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a standardized error result."""
        return {
            "success": False,
            "agent": self.name,
            "agent_id": self.agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "error": error,
            "error_code": error_code or "AGENT_ERROR",
            "data": None,
        }


class LLMAgent(BaseAgent):
    """
    Base class for agents that interact with LLM services.
    """

    def __init__(self, name: str, description: str, llm_service):
        super().__init__(name, description)
        self.llm_service = llm_service

    async def _call_llm(
        self, messages: List[Dict[str, str]], params: Optional[LLMParameters] = None
    ) -> str:
        """Call LLM service with proper error handling."""
        try:
            if params is None:
                params = LLMParameters()  # Use defaults

            response = await self.llm_service._call_llm_with_retry(messages, params)

            # Track token usage (rough estimate)
            tokens_used = len(response.split())
            self._total_tokens_used += tokens_used

            return response

        except Exception as e:
            self.logger.error(f"LLM call failed: {str(e)}")
            raise LLMError(f"Agent {self.name} LLM call failed: {str(e)}")

    def _build_system_prompt(self, task_specific_context: str = "") -> str:
        """Build system prompt for this agent."""
        base_prompt = f"""You are {self.name}, a specialized AI agent with the following capabilities:
{chr(10).join(f"- {cap}" for cap in self.capabilities)}

{self.description}

{task_specific_context}

Important guidelines:
- Provide accurate, helpful responses within your area of expertise
- If a task is outside your capabilities, clearly state this
- Always return valid JSON when requested
- Be concise but thorough in your analysis"""

        return base_prompt

    async def _parse_llm_json_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response as JSON with error handling."""
        try:
            # Clean the response
            cleaned_response = self.llm_service._advanced_content_cleaning(response)
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM JSON response: {str(e)}")
            raise LLMError(
                f"Agent {self.name} received invalid JSON from LLM: {str(e)}"
            )


class CoordinatorAgent(BaseAgent):
    """
    Agent responsible for coordinating multiple agents and managing workflows.
    """

    def __init__(self):
        super().__init__(
            name="Coordinator",
            description="Coordinates multiple agents and manages complex workflows",
        )
        self.registered_agents: Dict[str, BaseAgent] = {}
        self.active_workflows: Dict[str, Dict[str, Any]] = {}

    def _define_capabilities(self) -> List[str]:
        return [
            "workflow_coordination",
            "agent_management",
            "task_distribution",
            "result_aggregation",
            "error_recovery",
        ]

    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the coordinator."""
        self.registered_agents[agent.name] = agent
        self.logger.info(f"Registered agent: {agent.name}")

    async def execute(
        self, task: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a coordinated multi-agent workflow."""
        workflow_id = str(uuid4())
        workflow_type = task.get("workflow_type", "sequential")

        try:
            await self._pre_execution_hook(task)
            start_time = datetime.utcnow()

            # Initialize workflow tracking
            self.active_workflows[workflow_id] = {
                "start_time": start_time,
                "workflow_type": workflow_type,
                "tasks": task.get("agent_tasks", []),
                "results": [],
                "status": "running",
            }

            if workflow_type == "sequential":
                result = await self._execute_sequential_workflow(
                    workflow_id, task, context
                )
            elif workflow_type == "parallel":
                result = await self._execute_parallel_workflow(
                    workflow_id, task, context
                )
            elif workflow_type == "conditional":
                result = await self._execute_conditional_workflow(
                    workflow_id, task, context
                )
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")

            # Update workflow status
            self.active_workflows[workflow_id]["status"] = "completed"
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            await self._post_execution_hook(result, execution_time)
            return result

        except Exception as e:
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id]["status"] = "failed"
            self.logger.error(f"Workflow execution failed: {str(e)}")
            return self._create_error_result(str(e), "WORKFLOW_ERROR")

    async def _execute_sequential_workflow(
        self, workflow_id: str, task: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agents sequentially, passing results between them."""
        agent_tasks = task.get("agent_tasks", [])
        results = []
        accumulated_context = context.copy()

        for i, agent_task in enumerate(agent_tasks):
            agent_name = agent_task.get("agent")

            if agent_name not in self.registered_agents:
                error_msg = f"Agent {agent_name} not found"
                self.logger.error(error_msg)
                return self._create_error_result(error_msg, "AGENT_NOT_FOUND")

            agent = self.registered_agents[agent_name]

            # Add previous results to context
            if results:
                accumulated_context["previous_results"] = results

            self.logger.info(
                f"Executing agent {agent_name} (step {i+1}/{len(agent_tasks)})"
            )

            agent_result = await agent.execute(agent_task, accumulated_context)
            results.append(agent_result)

            # Update workflow tracking
            self.active_workflows[workflow_id]["results"].append(agent_result)

            # If agent failed and no error recovery specified, stop workflow
            if not agent_result.get("success", False):
                if not task.get("continue_on_error", False):
                    return self._create_error_result(
                        f"Workflow stopped at agent {agent_name}: {agent_result.get('error')}",
                        "WORKFLOW_AGENT_FAILED",
                    )

        return self._create_success_result(
            results,
            {
                "workflow_id": workflow_id,
                "workflow_type": "sequential",
                "agents_executed": len(results),
            },
        )

    async def _execute_parallel_workflow(
        self, workflow_id: str, task: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agents in parallel for improved performance."""
        agent_tasks = task.get("agent_tasks", [])

        # Create tasks for concurrent execution
        async_tasks = []
        for agent_task in agent_tasks:
            agent_name = agent_task.get("agent")

            if agent_name not in self.registered_agents:
                error_msg = f"Agent {agent_name} not found"
                self.logger.error(error_msg)
                return self._create_error_result(error_msg, "AGENT_NOT_FOUND")

            agent = self.registered_agents[agent_name]
            async_tasks.append(agent.execute(agent_task, context))

        # Execute all agents concurrently
        self.logger.info(f"Executing {len(async_tasks)} agents in parallel")
        results = await asyncio.gather(*async_tasks, return_exceptions=True)

        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = self._create_error_result(
                    f"Agent failed with exception: {str(result)}", "AGENT_EXCEPTION"
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)

        # Update workflow tracking
        self.active_workflows[workflow_id]["results"] = processed_results

        return self._create_success_result(
            processed_results,
            {
                "workflow_id": workflow_id,
                "workflow_type": "parallel",
                "agents_executed": len(processed_results),
                "successful_agents": sum(
                    1 for r in processed_results if r.get("success", False)
                ),
            },
        )

    async def _execute_conditional_workflow(
        self, workflow_id: str, task: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agents based on conditional logic."""
        conditions = task.get("conditions", [])
        results = []

        for condition_block in conditions:
            condition = condition_block.get("condition")
            agent_tasks = condition_block.get("agent_tasks", [])

            # Evaluate condition (simple implementation)
            if self._evaluate_condition(condition, context, results):
                self.logger.info(
                    f"Condition '{condition}' met, executing {len(agent_tasks)} agents"
                )

                for agent_task in agent_tasks:
                    agent_name = agent_task.get("agent")

                    if agent_name not in self.registered_agents:
                        continue  # Skip missing agents in conditional workflows

                    agent = self.registered_agents[agent_name]
                    agent_result = await agent.execute(agent_task, context)
                    results.append(agent_result)

        return self._create_success_result(
            results,
            {
                "workflow_id": workflow_id,
                "workflow_type": "conditional",
                "conditions_evaluated": len(conditions),
                "agents_executed": len(results),
            },
        )

    def _evaluate_condition(
        self,
        condition: str,
        context: Dict[str, Any],
        previous_results: List[Dict[str, Any]],
    ) -> bool:
        """Evaluate a simple condition (can be extended for complex logic)."""
        # Simple condition evaluation - can be made more sophisticated
        if condition == "always":
            return True
        elif condition == "if_previous_success" and previous_results:
            return all(r.get("success", False) for r in previous_results)
        elif condition == "if_previous_failed" and previous_results:
            return any(not r.get("success", True) for r in previous_results)
        elif condition == "if_no_previous":
            return len(previous_results) == 0
        else:
            # Default to true for unknown conditions
            return True

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific workflow."""
        return self.active_workflows.get(workflow_id)

    def get_all_workflow_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get the status of all active workflows."""
        return self.active_workflows.copy()

    def cleanup_completed_workflows(self, max_age_hours: int = 24) -> int:
        """Clean up old completed workflows."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        workflows_to_remove = []

        for workflow_id, workflow_data in self.active_workflows.items():
            if (
                workflow_data.get("status") in ["completed", "failed"]
                and workflow_data.get("start_time", datetime.utcnow()) < cutoff_time
            ):
                workflows_to_remove.append(workflow_id)

        for workflow_id in workflows_to_remove:
            del self.active_workflows[workflow_id]

        self.logger.info(f"Cleaned up {len(workflows_to_remove)} old workflows")
        return len(workflows_to_remove)
