"""
Security Reporter Agent

This agent generates executive-level security reports from attack path analysis.
It acts as the "CISO" that translates technical findings into business impact.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime

from .base_agent import LLMAgent
from ...schemas.attack_path_schemas import (
    AttackPathContext,
    AttackPathAnalysisReport,
    AttackChain
)
from ...schemas.security_schemas import SecurityIssue, SecuritySeverity

logger = logging.getLogger(__name__)


class SecurityReporterAgent(LLMAgent):
    """
    Security Reporter Agent - Generates executive security reports

    This agent synthesizes all findings into actionable, prioritized reports
    suitable for technical and non-technical stakeholders.
    """

    def __init__(self, llm_service):
        super().__init__(
            name="SecurityReporter",
            description="Generates executive security reports from attack path analysis",
            llm_service=llm_service
        )

    def _define_capabilities(self) -> List[str]:
        """Define the capabilities of this agent"""
        return [
            "executive_summary_generation",
            "risk_prioritization",
            "remediation_roadmap_creation",
            "business_impact_assessment"
        ]

    async def execute(self, task: Dict[str, Any], context: AttackPathContext) -> Dict[str, Any]:
        """
        Generate comprehensive security report

        Args:
            task: Task parameters
            context: Attack path MCP context with all findings

        Returns:
            Dict with attack_path_report: AttackPathAnalysisReport
        """
        logger.info(f"[{self.name}] Generating security report...")
        start_time = datetime.utcnow()

        try:
            # Update context
            context.current_stage = "reporting"
            context.current_activity = "Generating executive report..."
            context.progress_percentage = 80.0

            attack_chains = context.attack_chains
            vulnerabilities = context.individual_vulnerabilities

            # Categorize attack chains by severity
            critical_chains = [c for c in attack_chains if c.severity == SecuritySeverity.CRITICAL]
            high_chains = [c for c in attack_chains if c.severity == SecuritySeverity.HIGH]

            # Calculate statistics
            vuln_ids_in_chains = set()
            for chain in attack_chains:
                for step in chain.steps:
                    vuln_ids_in_chains.add(step.vulnerability_id)

            vulnerabilities_in_chains = len(vuln_ids_in_chains)
            isolated_vulnerabilities = len(vulnerabilities) - vulnerabilities_in_chains

            # Determine overall risk level
            risk_level = self._determine_risk_level(
                len(critical_chains),
                len(high_chains),
                vulnerabilities_in_chains
            )

            # Calculate security score (0-100, higher is better)
            security_score = self._calculate_security_score(
                critical_chains,
                high_chains,
                attack_chains,
                vulnerabilities
            )

            # Generate executive summary using LLM
            context.current_activity = "AI is writing executive summary..."
            executive_summary = await self._generate_executive_summary(
                attack_chains,
                vulnerabilities,
                risk_level,
                security_score
            )

            # Generate top 3 risks (simplified explanations)
            top_3_risks = self._generate_top_risks(attack_chains)

            # Generate remediation roadmap
            immediate_actions, short_term, long_term = self._generate_remediation_roadmap(
                attack_chains,
                vulnerabilities
            )

            # Create the report
            report = AttackPathAnalysisReport(
                spec_hash=context.spec_hash,
                executive_summary=executive_summary,
                risk_level=risk_level,
                overall_security_score=security_score,
                critical_chains=critical_chains,
                high_priority_chains=high_chains,
                all_chains=attack_chains,
                total_chains_found=len(attack_chains),
                total_vulnerabilities=len(vulnerabilities),
                vulnerabilities_in_chains=vulnerabilities_in_chains,
                isolated_vulnerabilities=isolated_vulnerabilities,
                top_3_risks=top_3_risks,
                immediate_actions=immediate_actions,
                short_term_actions=short_term,
                long_term_actions=long_term,
                analysis_depth=task.get("analysis_depth", "standard"),
                execution_time_ms=context.total_execution_time_ms,
                tokens_used=context.tokens_used,
                context_id=context.context_id
            )

            # Update context
            context.stages_completed.append("reporting")
            context.current_stage = "completed"
            context.progress_percentage = 100.0
            context.current_activity = "Analysis complete!"

            # Calculate this agent's execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            context.total_execution_time_ms += execution_time

            logger.info(
                f"[{self.name}] Report generated successfully. "
                f"Risk Level: {risk_level}, Score: {security_score:.1f}/100"
            )

            return {
                "success": True,
                "attack_path_report": report
            }

        except Exception as e:
            logger.error(f"[{self.name}] Error generating report: {e}", exc_info=True)
            context.current_stage = "error"
            return {
                "success": False,
                "error": str(e)
            }

    def can_handle_task(self, task_type: str) -> bool:
        """Check if this agent can handle the given task type"""
        return task_type in [
            "generate_report",
            "create_executive_summary",
            "security_reporting"
        ]

    def _determine_risk_level(
        self,
        critical_count: int,
        high_count: int,
        vulns_in_chains: int
    ) -> str:
        """Determine overall risk level based on findings"""
        if critical_count > 0:
            return "CRITICAL"
        elif high_count >= 2 or vulns_in_chains >= 5:
            return "HIGH"
        elif high_count >= 1 or vulns_in_chains >= 3:
            return "MEDIUM"
        else:
            return "LOW"

    def _calculate_security_score(
        self,
        critical_chains: List[AttackChain],
        high_chains: List[AttackChain],
        all_chains: List[AttackChain],
        vulnerabilities: List[SecurityIssue]
    ) -> float:
        """Calculate security score (0-100, higher is better)"""
        # Start with perfect score
        score = 100.0

        # Deduct points for attack chains
        score -= len(critical_chains) * 25  # Each critical chain is -25 points
        score -= len(high_chains) * 10  # Each high chain is -10 points
        score -= (len(all_chains) - len(critical_chains) - len(high_chains)) * 3  # Other chains -3

        # Additional deductions for isolated high-severity vulnerabilities
        critical_vulns = [v for v in vulnerabilities if v.severity == SecuritySeverity.CRITICAL]
        high_vulns = [v for v in vulnerabilities if v.severity == SecuritySeverity.HIGH]
        score -= len(critical_vulns) * 5
        score -= len(high_vulns) * 2

        # Ensure score is within bounds
        return max(0.0, min(100.0, score))

    async def _generate_executive_summary(
        self,
        attack_chains: List[AttackChain],
        vulnerabilities: List[SecurityIssue],
        risk_level: str,
        security_score: float
    ) -> str:
        """Generate executive summary using LLM"""
        try:
            # Build context for summary
            chains_summary = []
            for chain in attack_chains[:5]:  # Top 5 chains
                chains_summary.append(
                    f"- {chain.name} ({chain.severity.value.upper()}): {chain.attack_goal}"
                )

            chains_text = "\n".join(chains_summary) if chains_summary else "None found"

            prompt = f"""You are a Chief Information Security Officer (CISO) writing an executive summary for leadership.

**Analysis Results**:
- Overall Risk Level: {risk_level}
- Security Score: {security_score:.1f}/100
- Attack Chains Found: {len(attack_chains)}
- Total Vulnerabilities: {len(vulnerabilities)}

**Top Attack Chains**:
{chains_text}

**Your Task**: Write a 3-4 paragraph executive summary that:
1. Opens with the bottom line: is this API safe to deploy?
2. Highlights the most critical attack chains in business terms (avoid jargon)
3. Explains the potential business impact (data breaches, financial loss, reputation damage)
4. Provides a clear recommendation (fix before deployment, fix within X days, etc.)

Keep it concise, non-technical, and action-oriented. This will be read by executives who need to make risk decisions.

Write ONLY the executive summary text. No JSON, no markdown headers, just the paragraphs.
"""

            response = await self.llm_service.generate(
                model="mistral:7b-instruct",
                prompt=prompt,
                temperature=0.6,  # Slightly higher for natural language
                max_tokens=1000
            )

            summary = response.get("response", "").strip()

            # Update token usage
            tokens_used = response.get("tokens_used", 0)
            self._total_tokens_used += tokens_used

            return summary if summary else self._fallback_executive_summary(
                risk_level,
                len(attack_chains),
                len(vulnerabilities)
            )

        except Exception as e:
            logger.error(f"[{self.name}] Error generating executive summary: {e}")
            return self._fallback_executive_summary(
                risk_level,
                len(attack_chains),
                len(vulnerabilities)
            )

    def _fallback_executive_summary(
        self,
        risk_level: str,
        chain_count: int,
        vuln_count: int
    ) -> str:
        """Generate a simple executive summary without LLM"""
        if risk_level == "CRITICAL":
            return (
                f"This API has CRITICAL security vulnerabilities. We identified {chain_count} "
                f"attack chain(s) that could be exploited by attackers to gain unauthorized access, "
                f"escalate privileges, or steal sensitive data. These vulnerabilities pose an immediate "
                f"risk to the business and must be addressed before deployment. "
                f"Recommendation: Do not deploy until critical issues are resolved."
            )
        elif risk_level == "HIGH":
            return (
                f"This API has HIGH-severity security issues. We found {chain_count} attack chain(s) "
                f"and {vuln_count} individual vulnerabilities that could be exploited. While not immediately "
                f"critical, these issues significantly increase the risk of security incidents. "
                f"Recommendation: Fix high-priority issues within 7-14 days of deployment."
            )
        else:
            return (
                f"This API has a moderate security posture with {chain_count} attack chain(s) identified. "
                f"The vulnerabilities found are manageable but should be addressed to strengthen overall "
                f"security. Recommendation: Include fixes in the next development cycle."
            )

    def _generate_top_risks(self, attack_chains: List[AttackChain]) -> List[str]:
        """Generate simplified top 3 risk explanations"""
        top_risks = []

        # Sort by severity and impact
        sorted_chains = sorted(
            attack_chains,
            key=lambda c: (
                c.severity == SecuritySeverity.CRITICAL,
                c.severity == SecuritySeverity.HIGH,
                c.impact_score
            ),
            reverse=True
        )

        for chain in sorted_chains[:3]:
            risk_text = (
                f"{chain.name}: "
                f"An attacker can {chain.attack_goal.lower()} by chaining {len(chain.steps)} "
                f"vulnerabilities together. This could result in {chain.business_impact.lower()}."
            )
            top_risks.append(risk_text)

        return top_risks

    def _generate_remediation_roadmap(
        self,
        attack_chains: List[AttackChain],
        vulnerabilities: List[SecurityIssue]
    ) -> tuple:
        """Generate prioritized remediation roadmap"""
        immediate = []
        short_term = []
        long_term = []

        # Immediate actions: Fix critical chains
        critical_chains = [c for c in attack_chains if c.severity == SecuritySeverity.CRITICAL]
        for chain in critical_chains:
            for step in chain.remediation_steps[:2]:  # Top 2 fixes per chain
                if step not in immediate:
                    immediate.append(step)

        # Short-term: Fix high-severity chains and isolated critical vulnerabilities
        high_chains = [c for c in attack_chains if c.severity == SecuritySeverity.HIGH]
        for chain in high_chains:
            for step in chain.remediation_steps[:1]:
                if step not in short_term and step not in immediate:
                    short_term.append(step)

        # Add critical isolated vulnerabilities to short-term
        critical_isolated = [
            v for v in vulnerabilities
            if v.severity == SecuritySeverity.CRITICAL
        ]
        for vuln in critical_isolated[:3]:
            if vuln.recommendation and vuln.recommendation not in immediate:
                short_term.append(vuln.recommendation)

        # Long-term: Architectural improvements
        long_term = [
            "Implement comprehensive API authentication and authorization framework",
            "Add automated security testing to CI/CD pipeline",
            "Conduct regular security audits and penetration testing",
            "Implement API rate limiting and abuse prevention",
            "Add comprehensive API logging and monitoring"
        ]

        return (
            immediate[:5],  # Top 5 immediate actions
            short_term[:5],  # Top 5 short-term actions
            long_term[:5]  # Top 5 long-term actions
        )
