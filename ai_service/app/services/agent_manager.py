"""
Agent Manager for SchemaSculpt AI Agentic System.
Orchestrates multiple specialized agents to handle complex OpenAPI generation and modification tasks.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..core.logging import get_logger
from ..schemas.ai_schemas import GenerateSpecRequest, AIResponse, OperationType, PerformanceMetrics
from .agents.base_agent import CoordinatorAgent
from .agents.domain_analyzer import DomainAnalyzerAgent
from .agents.schema_generator import SchemaGeneratorAgent
from .agents.path_generator import PathGeneratorAgent


class AgentManager:
    """
    Manages and coordinates specialized AI agents for complex OpenAPI tasks.
    """

    def __init__(self, llm_service):
        self.logger = get_logger("agent_manager")
        self.llm_service = llm_service

        # Initialize coordinator
        self.coordinator = CoordinatorAgent()

        # Initialize specialized agents
        self.domain_analyzer = DomainAnalyzerAgent(llm_service)
        self.schema_generator = SchemaGeneratorAgent(llm_service)
        self.path_generator = PathGeneratorAgent(llm_service)

        # Register agents with coordinator
        self._register_agents()

        # Predefined workflows
        self._workflows = self._define_workflows()

    def _register_agents(self):
        """Register all agents with the coordinator."""
        self.coordinator.register_agent(self.domain_analyzer)
        self.coordinator.register_agent(self.schema_generator)
        self.coordinator.register_agent(self.path_generator)

        self.logger.info("Registered all agents with coordinator")

    def _define_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Define predefined workflows for common tasks."""
        return {
            "complete_spec_generation": {
                "workflow_type": "sequential",
                "description": "Generate complete OpenAPI specification from scratch",
                "agent_tasks": [
                    {
                        "agent": "DomainAnalyzer",
                        "task_type": "analyze_domain",
                        "input_data": {}  # Will be populated at runtime
                    },
                    {
                        "agent": "DomainAnalyzer",
                        "task_type": "extract_entities",
                        "input_data": {}
                    },
                    {
                        "agent": "SchemaGenerator",
                        "task_type": "generate_schemas",
                        "input_data": {}
                    },
                    {
                        "agent": "PathGenerator",
                        "task_type": "generate_paths",
                        "input_data": {}
                    }
                ]
            },
            "schema_optimization": {
                "workflow_type": "parallel",
                "description": "Optimize existing schemas and paths",
                "agent_tasks": [
                    {
                        "agent": "SchemaGenerator",
                        "task_type": "optimize_schemas",
                        "input_data": {}
                    },
                    {
                        "agent": "PathGenerator",
                        "task_type": "optimize_paths",
                        "input_data": {}
                    }
                ]
            },
            "security_enhancement": {
                "workflow_type": "sequential",
                "description": "Add comprehensive security to API specification",
                "agent_tasks": [
                    {
                        "agent": "PathGenerator",
                        "task_type": "add_security",
                        "input_data": {}
                    },
                    {
                        "agent": "SchemaGenerator",
                        "task_type": "add_validation",
                        "input_data": {}
                    }
                ]
            },
            "comprehensive_enhancement": {
                "workflow_type": "sequential",
                "description": "Complete enhancement of existing specification",
                "agent_tasks": [
                    {
                        "agent": "SchemaGenerator",
                        "task_type": "add_validation",
                        "input_data": {}
                    },
                    {
                        "agent": "SchemaGenerator",
                        "task_type": "generate_examples",
                        "input_data": {}
                    },
                    {
                        "agent": "PathGenerator",
                        "task_type": "enhance_operations",
                        "input_data": {}
                    },
                    {
                        "agent": "PathGenerator",
                        "task_type": "add_security",
                        "input_data": {}
                    }
                ]
            }
        }

    async def execute_complete_spec_generation(self, request: GenerateSpecRequest) -> AIResponse:
        """
        Execute the complete specification generation workflow.
        """
        start_time = datetime.utcnow()
        self.logger.info("Starting complete spec generation workflow")

        try:
            # Prepare workflow task
            workflow_task = self._workflows["complete_spec_generation"].copy()

            # Populate task data
            workflow_task["agent_tasks"][0]["input_data"] = {
                "prompt": request.prompt,
                "domain": request.domain
            }

            # Execute workflow
            context = {
                "request": {
                    "domain": request.domain,
                    "complexity_level": request.complexity_level,
                    "include_examples": request.include_examples,
                    "include_security": request.include_security,
                    "api_style": request.api_style,
                    "openapi_version": request.openapi_version
                }
            }

            workflow_result = await self.coordinator.execute(workflow_task, context)

            if not workflow_result.get("success", False):
                raise Exception(f"Workflow failed: {workflow_result.get('error', 'Unknown error')}")

            # Assemble final specification
            final_spec = await self._assemble_final_specification(workflow_result, request)

            # Calculate performance metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            total_tokens = sum(
                result.get("metadata", {}).get("tokens_used", 0)
                for result in workflow_result.get("data", [])
                if isinstance(result.get("data"), dict)
            )

            performance = PerformanceMetrics(
                processing_time_ms=processing_time,
                token_count=total_tokens,
                model_used=request.llm_parameters.model,
                cache_hit=False
            )

            # Create AI response
            validation_result = await self.llm_service._validate_openapi_spec(final_spec)

            return AIResponse(
                updated_spec_text=final_spec,
                operation_type=OperationType.GENERATE,
                validation=validation_result,
                confidence_score=self._calculate_confidence_score(workflow_result),
                changes_summary="Generated complete OpenAPI specification using agentic workflow",
                performance=performance,
                follow_up_suggestions=self._generate_follow_up_suggestions(workflow_result)
            )

        except Exception as e:
            self.logger.error(f"Complete spec generation failed: {str(e)}")
            raise

    async def execute_custom_workflow(self, workflow_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a predefined workflow with custom input data.
        """
        if workflow_name not in self._workflows:
            raise ValueError(f"Unknown workflow: {workflow_name}")

        workflow_task = self._workflows[workflow_name].copy()

        # Populate input data for all tasks
        for task in workflow_task["agent_tasks"]:
            task["input_data"].update(input_data)

        context = {"workflow_name": workflow_name, "custom_input": input_data}

        return await self.coordinator.execute(workflow_task, context)

    async def execute_ad_hoc_workflow(self, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an ad-hoc workflow defined by the user.
        """
        return await self.coordinator.execute(workflow_definition, {})

    async def _assemble_final_specification(
        self,
        workflow_result: Dict[str, Any],
        request: GenerateSpecRequest
    ) -> str:
        """
        Assemble the final OpenAPI specification from agent results.
        """
        # Extract results from workflow
        agent_results = workflow_result.get("data", [])

        # Initialize specification structure
        spec = {
            "openapi": request.openapi_version,
            "info": {
                "title": self._extract_api_title(agent_results, request),
                "version": "1.0.0",
                "description": self._extract_api_description(agent_results, request)
            },
            "paths": {},
            "components": {
                "schemas": {}
            }
        }

        # Extract and merge results from each agent
        for result in agent_results:
            if not result.get("success", False):
                continue

            data = result.get("data", {})
            agent = result.get("agent", "")

            if agent == "SchemaGenerator" and "schemas" in data:
                spec["components"]["schemas"].update(data["schemas"])

            elif agent == "PathGenerator" and "paths" in data:
                spec["paths"].update(data["paths"])

            elif agent == "PathGenerator" and "security_schemes" in data:
                if "components" not in spec:
                    spec["components"] = {}
                if "securitySchemes" not in spec["components"]:
                    spec["components"]["securitySchemes"] = {}
                spec["components"]["securitySchemes"].update(data["security_schemes"])

        # Add security if requested
        if request.include_security and "securitySchemes" in spec.get("components", {}):
            spec["security"] = [
                {scheme: []} for scheme in spec["components"]["securitySchemes"].keys()
            ]

        # Clean up empty components
        if not spec["components"].get("schemas") and not spec["components"].get("securitySchemes"):
            del spec["components"]

        return json.dumps(spec, indent=2)

    def _extract_api_title(self, agent_results: List[Dict], request: GenerateSpecRequest) -> str:
        """Extract API title from domain analysis or generate from prompt."""
        for result in agent_results:
            if result.get("agent") == "DomainAnalyzer" and result.get("success"):
                data = result.get("data", {})
                if "domain" in data:
                    return f"{data['domain'].title()} API"

        # Fallback: generate from prompt
        prompt_words = request.prompt.split()[:3]
        return f"{' '.join(word.title() for word in prompt_words)} API"

    def _extract_api_description(self, agent_results: List[Dict], request: GenerateSpecRequest) -> str:
        """Extract API description from domain analysis."""
        for result in agent_results:
            if result.get("agent") == "DomainAnalyzer" and result.get("success"):
                data = result.get("data", {})
                if "business_processes" in data and data["business_processes"]:
                    processes = [proc["description"] for proc in data["business_processes"][:2]]
                    return f"API for {', '.join(processes)}"

        return f"API generated from requirements: {request.prompt[:100]}..."

    def _calculate_confidence_score(self, workflow_result: Dict[str, Any]) -> float:
        """Calculate confidence score based on workflow success."""
        agent_results = workflow_result.get("data", [])
        successful_agents = sum(1 for result in agent_results if result.get("success", False))
        total_agents = len(agent_results)

        if total_agents == 0:
            return 0.5

        base_confidence = successful_agents / total_agents

        # Adjust based on complexity and completeness
        complexity_bonus = 0.1 if total_agents >= 4 else 0  # Full workflow bonus
        return min(0.95, base_confidence + complexity_bonus)

    def _generate_follow_up_suggestions(self, workflow_result: Dict[str, Any]) -> List[str]:
        """Generate follow-up suggestions based on workflow results."""
        suggestions = []
        agent_results = workflow_result.get("data", [])

        # Analyze results for suggestions
        has_schemas = any(
            result.get("agent") == "SchemaGenerator" and result.get("success")
            for result in agent_results
        )

        has_paths = any(
            result.get("agent") == "PathGenerator" and result.get("success")
            for result in agent_results
        )

        if has_schemas and has_paths:
            suggestions.extend([
                "Consider adding comprehensive examples to improve documentation",
                "Review security schemes and add authentication where needed",
                "Add request/response validation rules for better API reliability",
                "Consider implementing rate limiting and caching strategies"
            ])

        if not has_schemas:
            suggestions.append("Generate comprehensive schemas for better type safety")

        if not has_paths:
            suggestions.append("Add RESTful paths to complete the API interface")

        return suggestions

    def get_available_workflows(self) -> Dict[str, str]:
        """Get list of available predefined workflows."""
        return {
            name: workflow["description"]
            for name, workflow in self._workflows.items()
        }

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        return {
            "coordinator": self.coordinator.get_agent_status(),
            "domain_analyzer": self.domain_analyzer.get_agent_status(),
            "schema_generator": self.schema_generator.get_agent_status(),
            "path_generator": self.path_generator.get_agent_status(),
            "active_workflows": len(self.coordinator.active_workflows),
            "available_workflows": list(self._workflows.keys())
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all agents."""
        health_status = {
            "overall_status": "healthy",
            "agents": {},
            "coordinator": {},
            "timestamp": datetime.utcnow().isoformat()
        }

        # Check individual agents
        agents = {
            "domain_analyzer": self.domain_analyzer,
            "schema_generator": self.schema_generator,
            "path_generator": self.path_generator
        }

        for name, agent in agents.items():
            agent_status = agent.get_agent_status()
            health_status["agents"][name] = {
                "status": "healthy" if not agent_status["is_busy"] else "busy",
                "execution_count": agent_status["execution_count"],
                "average_execution_time": agent_status["average_execution_time"]
            }

        # Check coordinator
        coordinator_status = self.coordinator.get_agent_status()
        health_status["coordinator"] = {
            "status": "healthy",
            "active_workflows": len(self.coordinator.active_workflows),
            "total_executions": coordinator_status["execution_count"]
        }

        return health_status