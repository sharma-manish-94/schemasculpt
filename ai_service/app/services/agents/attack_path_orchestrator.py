"""
Attack Path Orchestrator - RAG-Enhanced Workflow Coordinator

This is the "Planner" agent that coordinates the entire attack path simulation workflow.
It manages the MCP (Model Context Protocol) and orchestrates all RAG-enhanced agents.

RAG Enhancement: Provides shared RAG service to all agents, enabling them to query
specialized knowledge bases (Attacker KB + Governance KB) throughout the analysis.
"""

import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ...schemas.attack_path_schemas import (
    AttackPathAnalysisReport,
    AttackPathAnalysisRequest,
    AttackPathContext,
    EnrichedSecurityFindingsRequest,
)
from ..rag_service import RAGService
from .security_reporter_agent import SecurityReporterAgent
from .threat_modeling_agent import ThreatModelingAgent
from .vulnerability_scanner_agent import VulnerabilityScannerAgent

logger = logging.getLogger(__name__)


class AttackPathOrchestrator:
    """
    RAG-Enhanced Attack Path Orchestrator - The "Planner" agent

    This orchestrator manages the entire attack path simulation workflow with RAG:
    1. Initialize shared RAG service (Attacker KB + Governance KB)
    2. Initialize MCP context
    3. Run VulnerabilityScanner to find individual issues
    4. Run RAG-enhanced ThreatModelingAgent to find attack chains
    5. Run RAG-enhanced SecurityReporter to generate final report
    6. Handle progress updates and error recovery
    """

    def __init__(self, llm_service):
        """
        Initialize the orchestrator with all required agents and RAG service

        Args:
            llm_service: LLM service for agents that need it
        """
        logger.info("[AttackPathOrchestrator] Initializing RAG service...")
        self.rag_service = RAGService()

        self.scanner_agent = VulnerabilityScannerAgent()
        self.threat_agent = ThreatModelingAgent(llm_service, self.rag_service)
        self.reporter_agent = SecurityReporterAgent(llm_service, self.rag_service)

        if self.rag_service.is_available():
            attacker_kb_status = (
                "✓" if self.rag_service.attacker_kb_available() else "✗"
            )
            governance_kb_status = (
                "✓" if self.rag_service.governance_kb_available() else "✗"
            )
            logger.info(
                f"[AttackPathOrchestrator] RAG-Enhanced mode enabled! "
                f"Attacker KB: {attacker_kb_status}, Governance KB: {governance_kb_status}"
            )
        else:
            logger.warning(
                "[AttackPathOrchestrator] RAG service not available. Operating in basic mode."
            )
        logger.info("[AttackPathOrchestrator] Initialized with all agents")

    async def run_analysis_from_enriched_findings(
        self, request: EnrichedSecurityFindingsRequest
    ) -> AttackPathAnalysisReport:
        """
        Run Code-Aware attack path analysis from findings already enriched with code context.
        """
        logger.info(
            "[AttackPathOrchestrator] Starting Code-Aware analysis from enriched findings"
        )
        start_time = datetime.utcnow()

        try:
            # Initialize context with the enriched findings
            context = AttackPathContext(
                goal="Find critical multi-step attack paths based on code-aware findings",
                spec={},  # Spec is not needed as findings are pre-computed
                spec_hash="enriched-analysis",
                individual_vulnerabilities=[
                    f.original_finding for f in request.findings
                ],
                code_context_map={
                    f.original_finding.endpoint: f.code_context
                    for f in request.findings
                    if f.original_finding.endpoint and f.code_context
                },
                current_stage="initialized",
                progress_percentage=0.0,
                current_activity="Initializing code-aware analysis...",
            )
            context.stages_completed.append("scanning")  # Skip scanning stage

            logger.info(
                f"[AttackPathOrchestrator] MCP Context created: {context.context_id}"
            )

            # STAGE 1 is SKIPPED (Vulnerability Scanning)
            logger.info(
                "[AttackPathOrchestrator] Stage 1: Skipped (using pre-computed findings)"
            )
            context.progress_percentage = 33.0

            # STAGE 2: Threat Modeling (Attack Chain Discovery)
            logger.info("[AttackPathOrchestrator] Stage 2: Threat Modeling")
            context.current_stage = "analyzing_chains"
            context.current_activity = "Analyzing attack chains with code context..."
            context.progress_percentage = 35.0

            threat_task = {
                "task_type": "threat_modeling",
                "max_chain_length": request.max_chain_length,
                "analysis_depth": request.analysis_depth,
                "is_enriched": True,
            }
            threat_result = await self.threat_agent.execute(threat_task, context)

            if not threat_result.get("success"):
                logger.warning(
                    f"Threat modeling had issues: {threat_result.get('error')}"
                )

            logger.info(
                f"Threat agent found {len(context.attack_chains)} attack chains"
            )

            # STAGE 3: Report Generation
            logger.info("[AttackPathOrchestrator] Stage 3: Report Generation")
            context.current_stage = "reporting"
            context.current_activity = "Generating code-aware security report..."
            context.progress_percentage = 75.0

            reporter_task = {
                "task_type": "generate_report",
                "analysis_depth": request.analysis_depth,
                "is_enriched": True,
            }
            reporter_result = await self.reporter_agent.execute(reporter_task, context)

            if not reporter_result.get("success"):
                raise Exception(f"Reporter failed: {reporter_result.get('error')}")

            report: AttackPathAnalysisReport = reporter_result["attack_path_report"]
            logger.info(
                f"Analysis complete! Risk: {report.risk_level}, Score: {report.overall_security_score:.1f}/100"
            )

            total_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            report.execution_time_ms = total_time

            return report

        except Exception as e:
            logger.error(
                f"[AttackPathOrchestrator] Critical error in enriched analysis: {e}",
                exc_info=True,
            )
            raise

    async def run_attack_path_analysis(
        self,
        request: AttackPathAnalysisRequest,
        progress_callback: Optional[callable] = None,
    ) -> AttackPathAnalysisReport:
        """
        Run complete attack path simulation analysis
        """
        logger.info("[AttackPathOrchestrator] Starting attack path analysis")
        start_time = datetime.utcnow()

        try:
            import json

            import yaml

            try:
                spec = json.loads(request.spec_text)
            except json.JSONDecodeError:
                spec = yaml.safe_load(request.spec_text)

            spec_hash = hashlib.sha256(request.spec_text.encode()).hexdigest()
            context = AttackPathContext(
                goal="Find critical multi-step attack paths",
                spec=spec,
                spec_hash=spec_hash,
                current_stage="initialized",
                progress_percentage=0.0,
                current_activity="Initializing attack path simulation...",
            )

            logger.info(
                f"[AttackPathOrchestrator] MCP Context created: {context.context_id}"
            )

            if progress_callback:
                await progress_callback(
                    context.current_stage,
                    context.progress_percentage,
                    context.current_activity,
                )

            # STAGE 1: Vulnerability Scanning
            logger.info("[AttackPathOrchestrator] Stage 1: Vulnerability Scanning")
            context.current_stage = "scanning"
            context.current_activity = "Scanning for security vulnerabilities..."
            context.progress_percentage = 5.0

            if progress_callback:
                await progress_callback(
                    context.current_stage,
                    context.progress_percentage,
                    context.current_activity,
                )

            scanner_task = {"task_type": "vulnerability_scan"}
            scanner_result = await self.scanner_agent.execute(scanner_task, context)

            if not scanner_result.get("success"):
                raise Exception(f"Scanner failed: {scanner_result.get('error')}")

            logger.info(
                f"Scanner found {len(context.individual_vulnerabilities)} vulnerabilities"
            )

            if progress_callback:
                await progress_callback(
                    context.current_stage,
                    context.progress_percentage,
                    f"Found {len(context.individual_vulnerabilities)} vulnerabilities",
                )

            # STAGE 2: Threat Modeling (Attack Chain Discovery)
            logger.info("[AttackPathOrchestrator] Stage 2: Threat Modeling")
            context.current_stage = "analyzing_chains"
            context.current_activity = "Analyzing attack chains..."
            context.progress_percentage = 35.0

            if progress_callback:
                await progress_callback(
                    context.current_stage,
                    context.progress_percentage,
                    context.current_activity,
                )

            threat_task = {
                "task_type": "threat_modeling",
                "max_chain_length": request.max_chain_length,
                "analysis_depth": request.analysis_depth,
            }
            threat_result = await self.threat_agent.execute(threat_task, context)

            if not threat_result.get("success"):
                logger.warning(
                    f"Threat modeling had issues: {threat_result.get('error')}"
                )

            logger.info(
                f"Threat agent found {len(context.attack_chains)} attack chains"
            )

            if progress_callback:
                await progress_callback(
                    context.current_stage,
                    context.progress_percentage,
                    f"Found {len(context.attack_chains)} attack chains",
                )

            # STAGE 3: Report Generation
            logger.info("[AttackPathOrchestrator] Stage 3: Report Generation")
            context.current_stage = "reporting"
            context.current_activity = "Generating security report..."
            context.progress_percentage = 75.0

            if progress_callback:
                await progress_callback(
                    context.current_stage,
                    context.progress_percentage,
                    context.current_activity,
                )

            reporter_task = {
                "task_type": "generate_report",
                "analysis_depth": request.analysis_depth,
            }
            reporter_result = await self.reporter_agent.execute(reporter_task, context)

            if not reporter_result.get("success"):
                raise Exception(f"Reporter failed: {reporter_result.get('error')}")

            report: AttackPathAnalysisReport = reporter_result["attack_path_report"]
            logger.info(
                f"Analysis complete! Risk: {report.risk_level}, Score: {report.overall_security_score:.1f}/100"
            )

            if progress_callback:
                await progress_callback(
                    "completed", 100.0, "Attack path analysis complete!"
                )

            total_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            report.execution_time_ms = total_time
            return report

        except Exception as e:
            logger.error(f"[AttackPathOrchestrator] Critical error: {e}", exc_info=True)
            if progress_callback:
                await progress_callback("error", 0.0, f"Analysis failed: {str(e)}")
            raise

    def get_analysis_stages(self) -> Dict[str, str]:
        """Get descriptions of all analysis stages for UI display"""
        return {
            "initialized": "Initializing attack path simulation...",
            "scanning": "Scanning for security vulnerabilities...",
            "analyzing_chains": "Analyzing attack chains with AI...",
            "reporting": "Generating executive security report...",
            "completed": "Analysis complete!",
            "error": "Analysis encountered an error",
        }
