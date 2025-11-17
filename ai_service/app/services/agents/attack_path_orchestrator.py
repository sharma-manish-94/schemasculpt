"""
Attack Path Orchestrator

This is the "Planner" agent that coordinates the entire attack path simulation workflow.
It manages the MCP (Model Context Protocol) and orchestrates all other agents.
"""

import logging
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime

from .vulnerability_scanner_agent import VulnerabilityScannerAgent
from .threat_modeling_agent import ThreatModelingAgent
from .security_reporter_agent import SecurityReporterAgent
from ...schemas.attack_path_schemas import (
    AttackPathContext,
    AttackPathAnalysisRequest,
    AttackPathAnalysisReport
)

logger = logging.getLogger(__name__)


class AttackPathOrchestrator:
    """
    Attack Path Orchestrator - The "Planner" agent

    This orchestrator manages the entire attack path simulation workflow:
    1. Initialize MCP context
    2. Run VulnerabilityScanner to find individual issues
    3. Run ThreatModelingAgent to find attack chains
    4. Run SecurityReporter to generate final report
    5. Handle progress updates and error recovery
    """

    def __init__(self, llm_service):
        """
        Initialize the orchestrator with all required agents

        Args:
            llm_service: LLM service for agents that need it
        """
        self.scanner_agent = VulnerabilityScannerAgent()
        self.threat_agent = ThreatModelingAgent(llm_service)
        self.reporter_agent = SecurityReporterAgent(llm_service)

        logger.info("[AttackPathOrchestrator] Initialized with all agents")

    async def run_attack_path_analysis(
        self,
        request: AttackPathAnalysisRequest,
        progress_callback: Optional[callable] = None
    ) -> AttackPathAnalysisReport:
        """
        Run complete attack path simulation analysis

        Args:
            request: Analysis request with spec and parameters
            progress_callback: Optional callback for progress updates (for WebSocket)
                              Signature: async def callback(stage: str, progress: float, message: str)

        Returns:
            AttackPathAnalysisReport with all findings

        Raises:
            Exception if any stage fails critically
        """
        logger.info("[AttackPathOrchestrator] Starting attack path analysis")
        start_time = datetime.utcnow()

        try:
            # Parse the spec
            import yaml
            import json

            try:
                spec = json.loads(request.spec_text)
            except json.JSONDecodeError:
                spec = yaml.safe_load(request.spec_text)

            # Generate spec hash for caching
            spec_hash = hashlib.sha256(request.spec_text.encode()).hexdigest()

            # Initialize MCP context
            context = AttackPathContext(
                goal="Find critical multi-step attack paths",
                spec=spec,
                spec_hash=spec_hash,
                current_stage="initialized",
                progress_percentage=0.0,
                current_activity="Initializing attack path simulation..."
            )

            logger.info(f"[AttackPathOrchestrator] MCP Context created: {context.context_id}")

            # Send initial progress
            if progress_callback:
                await progress_callback(
                    context.current_stage,
                    context.progress_percentage,
                    context.current_activity
                )

            # ====================================================================
            # STAGE 1: Vulnerability Scanning
            # ====================================================================
            logger.info("[AttackPathOrchestrator] Stage 1: Vulnerability Scanning")
            context.current_stage = "scanning"
            context.current_activity = "Scanning for security vulnerabilities..."
            context.progress_percentage = 5.0

            if progress_callback:
                await progress_callback(
                    context.current_stage,
                    context.progress_percentage,
                    context.current_activity
                )

            scanner_task = {"task_type": "vulnerability_scan"}
            scanner_result = await self.scanner_agent.execute(scanner_task, context)

            if not scanner_result.get("success"):
                raise Exception(f"Scanner failed: {scanner_result.get('error')}")

            logger.info(
                f"[AttackPathOrchestrator] Scanner found "
                f"{len(context.individual_vulnerabilities)} vulnerabilities"
            )

            if progress_callback:
                await progress_callback(
                    context.current_stage,
                    context.progress_percentage,
                    f"Found {len(context.individual_vulnerabilities)} vulnerabilities"
                )

            # ====================================================================
            # STAGE 2: Threat Modeling (Attack Chain Discovery)
            # ====================================================================
            logger.info("[AttackPathOrchestrator] Stage 2: Threat Modeling")
            context.current_stage = "analyzing_chains"
            context.current_activity = "Analyzing attack chains..."
            context.progress_percentage = 35.0

            if progress_callback:
                await progress_callback(
                    context.current_stage,
                    context.progress_percentage,
                    context.current_activity
                )

            threat_task = {
                "task_type": "threat_modeling",
                "max_chain_length": request.max_chain_length,
                "analysis_depth": request.analysis_depth
            }
            threat_result = await self.threat_agent.execute(threat_task, context)

            if not threat_result.get("success"):
                logger.warning(
                    f"[AttackPathOrchestrator] Threat modeling had issues: "
                    f"{threat_result.get('error')}"
                )
                # Continue anyway - we can still report isolated vulnerabilities

            logger.info(
                f"[AttackPathOrchestrator] Threat agent found "
                f"{len(context.attack_chains)} attack chains"
            )

            if progress_callback:
                await progress_callback(
                    context.current_stage,
                    context.progress_percentage,
                    f"Found {len(context.attack_chains)} attack chains"
                )

            # ====================================================================
            # STAGE 3: Report Generation
            # ====================================================================
            logger.info("[AttackPathOrchestrator] Stage 3: Report Generation")
            context.current_stage = "reporting"
            context.current_activity = "Generating security report..."
            context.progress_percentage = 75.0

            if progress_callback:
                await progress_callback(
                    context.current_stage,
                    context.progress_percentage,
                    context.current_activity
                )

            reporter_task = {
                "task_type": "generate_report",
                "analysis_depth": request.analysis_depth
            }
            reporter_result = await self.reporter_agent.execute(reporter_task, context)

            if not reporter_result.get("success"):
                raise Exception(f"Reporter failed: {reporter_result.get('error')}")

            report: AttackPathAnalysisReport = reporter_result["attack_path_report"]

            logger.info(
                f"[AttackPathOrchestrator] Analysis complete! "
                f"Risk: {report.risk_level}, Score: {report.overall_security_score:.1f}/100"
            )

            # Final progress update
            if progress_callback:
                await progress_callback(
                    "completed",
                    100.0,
                    "Attack path analysis complete!"
                )

            # Calculate total execution time
            total_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            report.execution_time_ms = total_time

            return report

        except Exception as e:
            logger.error(f"[AttackPathOrchestrator] Critical error: {e}", exc_info=True)

            # Send error progress update
            if progress_callback:
                await progress_callback(
                    "error",
                    0.0,
                    f"Analysis failed: {str(e)}"
                )

            raise

    def get_analysis_stages(self) -> Dict[str, str]:
        """Get descriptions of all analysis stages for UI display"""
        return {
            "initialized": "Initializing attack path simulation...",
            "scanning": "Scanning for security vulnerabilities...",
            "analyzing_chains": "Analyzing attack chains with AI...",
            "reporting": "Generating executive security report...",
            "completed": "Analysis complete!",
            "error": "Analysis encountered an error"
        }
