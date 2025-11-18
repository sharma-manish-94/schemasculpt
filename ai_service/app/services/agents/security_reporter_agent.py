"""
Security Reporter Agent - RAG-Enhanced CISO Perspective

This agent generates executive-level security reports with expertise from:
- CVSS risk scoring methodology
- DREAD risk assessment framework
- Compliance frameworks (GDPR, HIPAA, PCI-DSS)

RAG Enhancement: Queries the Governance Knowledge Base to provide accurate
risk scores, business impact assessments, and compliance implications.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_agent import LLMAgent
from ...schemas.attack_path_schemas import (
    AttackPathContext,
    AttackPathAnalysisReport,
    AttackChain
)
from ...schemas.security_schemas import SecurityIssue, SecuritySeverity
from ..rag_service import RAGService

logger = logging.getLogger(__name__)


class SecurityReporterAgent(LLMAgent):
    """
    RAG-Enhanced Security Reporter Agent - Thinks like a CISO

    This agent synthesizes findings with governance/compliance expertise from RAG to:
    1. Query Governance KB for CVSS scoring and risk frameworks
    2. Generate accurate risk assessments using DREAD methodology
    3. Identify compliance implications (GDPR, HIPAA, PCI-DSS)
    4. Produce executive reports with business impact analysis
    """

    def __init__(self, llm_service, rag_service: Optional[RAGService] = None):
        super().__init__(
            name="SecurityReporter",
            description="RAG-enhanced agent that generates executive security reports with governance expertise",
            llm_service=llm_service
        )
        # Initialize or receive RAG service
        self.rag_service = rag_service or RAGService()

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

            # RAG ENHANCEMENT: Query Governance Knowledge Base
            governance_context = await self._query_governance_knowledge(
                attack_chains,
                vulnerabilities,
                risk_level
            )

            # Generate executive summary using LLM with RAG-enhanced governance context
            context.current_activity = "AI is writing executive summary..."
            executive_summary = await self._generate_executive_summary(
                attack_chains,
                vulnerabilities,
                risk_level,
                security_score,
                governance_context
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

    async def _query_governance_knowledge(
        self,
        attack_chains: List[AttackChain],
        vulnerabilities: List[SecurityIssue],
        risk_level: str
    ) -> Dict[str, Any]:
        """
        Query the Governance Knowledge Base for risk assessment expertise.

        This retrieves CVSS scoring guidelines, DREAD methodology, and
        compliance requirements (GDPR, HIPAA, PCI-DSS) relevant to the findings.
        """
        if not self.rag_service.governance_kb_available():
            logger.warning(f"[{self.name}] Governance KB not available. Operating without RAG enhancement.")
            return {
                "context": "",
                "sources": [],
                "available": False
            }

        try:
            # Build query based on risk level and vulnerability types
            query_parts = [
                f"risk level {risk_level}",
                "CVSS scoring",
                "DREAD framework",
                "business impact assessment"
            ]

            # Add compliance queries if data exposure risks exist
            has_data_risk = any(
                "data" in chain.business_impact.lower() or
                "privacy" in chain.business_impact.lower()
                for chain in attack_chains
            )

            if has_data_risk:
                query_parts.extend(["GDPR", "data protection", "compliance"])

            query = " ".join(query_parts)

            logger.info(f"[{self.name}] Querying Governance KB with: '{query[:100]}...'")

            # Query the Governance Knowledge Base
            rag_result = await self.rag_service.query_governance_knowledge(
                query=query,
                n_results=4  # Get top 4 governance documents
            )

            if rag_result.get("context"):
                logger.info(
                    f"[{self.name}] Retrieved {rag_result.get('total_documents', 0)} "
                    f"relevant governance documents from KB"
                )
            else:
                logger.warning(f"[{self.name}] No relevant governance knowledge found in KB")

            return {
                "context": rag_result.get("context", ""),
                "sources": rag_result.get("sources", []),
                "available": True
            }

        except Exception as e:
            logger.error(f"[{self.name}] Error querying Governance KB: {e}")
            return {
                "context": "",
                "sources": [],
                "available": False
            }

    async def _generate_executive_summary(
        self,
        attack_chains: List[AttackChain],
        vulnerabilities: List[SecurityIssue],
        risk_level: str,
        security_score: float,
        governance_context: Dict[str, Any]
    ) -> str:
        """Generate RAG-enhanced executive summary using LLM with governance expertise"""
        try:
            # Build detailed context for summary with step-by-step attack flows
            chains_detail = []
            for idx, chain in enumerate(attack_chains[:3], 1):  # Top 3 chains with full details
                steps_text = []
                for step_num, step in enumerate(chain.steps, 1):
                    steps_text.append(
                        f"  Step {step_num}: {step.description}"
                    )

                chain_detail = f"""Attack Chain {idx}: {chain.name} ({chain.severity.value.upper()})
Goal: {chain.attack_goal}
Exploitation Steps:
{chr(10).join(steps_text)}
Business Impact: {chain.business_impact}
Complexity: {chain.complexity}"""
                chains_detail.append(chain_detail)

            chains_text = "\n\n".join(chains_detail) if chains_detail else "None found"

            # Build RAG-enhanced governance section
            governance_section = ""
            if governance_context.get("available") and governance_context.get("context"):
                governance_section = f"""
**GOVERNANCE & RISK ASSESSMENT EXPERTISE**:
Use this specialized knowledge from CVSS, DREAD, and compliance frameworks to inform your report:

{governance_context['context']}

Apply this framework knowledge to provide accurate risk scores and compliance implications in your summary.
---
"""
            else:
                logger.info(f"[{self.name}] Building summary without RAG enhancement")

            prompt = f"""You are a Senior Security Consultant from a top penetration testing firm with expertise in risk assessment and compliance, writing an executive summary for a security assessment report.

{governance_section}

**Security Assessment Results**:
- Overall Risk Level: {risk_level}
- Security Score: {security_score:.1f}/100
- Exploitable Attack Chains: {len(attack_chains)}
- Total Vulnerabilities: {len(vulnerabilities)}

**Detailed Attack Chain Analysis**:
{chains_text}

**Your Task**: Write a professional executive summary (3-4 paragraphs) that:

1. **Opening Statement**: Start with a clear security verdict - is this API safe for production? State the overall risk level upfront.

2. **Attack Chain Explanation**: For the MOST CRITICAL attack chain found, explain the step-by-step exploitation path in business-friendly terms:
   - What does the attacker do first?
   - How do they chain vulnerabilities together?
   - What access/data do they gain at each step?
   - What is the final impact?
   Think like a penetration tester explaining to a CEO exactly HOW their API would be compromised.

3. **Business Impact**: Translate technical findings into business consequences:
   - What data could be stolen or modified?
   - What financial/regulatory/reputational damage could occur?
   - What compliance violations (GDPR, PCI-DSS, etc.) might this cause?

4. **Recommendation**: Provide specific, actionable guidance:
   - Should deployment be blocked?
   - What's the timeline for fixes (immediate, 7 days, 30 days)?
   - What's the risk if deployed as-is?

**Style Guide**:
- Write like a professional security consultant (authoritative but not alarmist)
- Use specific examples from the attack chains found
- Avoid generic statements - reference the ACTUAL vulnerabilities discovered
- Be concise but thorough
- No technical jargon (SQL injection → "database manipulation", XSS → "malicious code injection")

Write ONLY the executive summary text. No JSON, no markdown headers, no lists - just flowing paragraphs.
"""

            response = await self.llm_service.generate(
                model="mistral:7b-instruct",
                prompt=prompt,
                temperature=0.7,  # Balanced for professional yet natural language
                max_tokens=1200  # Increased for detailed explanation
            )

            summary = response.get("response", "").strip()

            # Update token usage
            tokens_used = response.get("tokens_used", 0)
            self._total_tokens_used += tokens_used

            return summary if summary else self._fallback_executive_summary(
                risk_level,
                len(attack_chains),
                len(vulnerabilities),
                attack_chains
            )

        except Exception as e:
            logger.error(f"[{self.name}] Error generating executive summary: {e}")
            return self._fallback_executive_summary(
                risk_level,
                len(attack_chains),
                len(vulnerabilities),
                attack_chains
            )

    def _fallback_executive_summary(
        self,
        risk_level: str,
        chain_count: int,
        vuln_count: int,
        attack_chains: List[AttackChain] = None
    ) -> str:
        """Generate a detailed executive summary without LLM"""
        # Get the most critical chain for detailed explanation
        most_critical = None
        if attack_chains:
            sorted_chains = sorted(
                attack_chains,
                key=lambda c: (
                    c.severity == SecuritySeverity.CRITICAL,
                    c.severity == SecuritySeverity.HIGH,
                    c.impact_score
                ),
                reverse=True
            )
            most_critical = sorted_chains[0] if sorted_chains else None

        if risk_level == "CRITICAL":
            base = f"Our security assessment has identified CRITICAL vulnerabilities in this API that pose an immediate risk to your organization. "

            if most_critical:
                attack_explanation = (
                    f"The most severe issue is a {len(most_critical.steps)}-step attack chain: {most_critical.name}. "
                    f"An attacker could {most_critical.attack_goal.lower()}, leading to {most_critical.business_impact.lower()}. "
                )
            else:
                attack_explanation = (
                    f"We identified {chain_count} exploitable attack chain(s) where vulnerabilities can be chained "
                    f"together to compromise the API. "
                )

            recommendation = (
                f"These vulnerabilities could result in unauthorized data access, privilege escalation, or complete "
                f"system compromise. Recommendation: Do not deploy this API to production until all critical issues "
                f"are resolved and verified through security testing."
            )
            return base + attack_explanation + recommendation

        elif risk_level == "HIGH":
            base = f"Our assessment identified HIGH-severity security issues requiring prompt attention. "

            if most_critical:
                attack_explanation = (
                    f"The primary concern is {most_critical.name}, where an attacker could {most_critical.attack_goal.lower()} "
                    f"by exploiting {len(most_critical.steps)} interconnected vulnerabilities. "
                )
            else:
                attack_explanation = (
                    f"We found {chain_count} attack chain(s) and {vuln_count} individual vulnerabilities. "
                )

            recommendation = (
                f"While not immediately critical, these issues significantly increase your risk exposure to data "
                f"breaches and compliance violations. Recommendation: Fix all high-priority issues within 7-14 days "
                f"of deployment and conduct security verification testing."
            )
            return base + attack_explanation + recommendation

        else:
            base = f"Our security analysis shows this API has moderate security concerns that should be addressed. "

            if most_critical:
                attack_explanation = (
                    f"We identified potential attack scenarios including {most_critical.name}, though the complexity "
                    f"of exploitation ({most_critical.complexity}) reduces immediate risk. "
                )
            else:
                attack_explanation = (
                    f"We found {chain_count} attack chain(s) that could be exploited under specific conditions. "
                )

            recommendation = (
                f"These vulnerabilities are manageable and should be remediated to strengthen your security posture. "
                f"Recommendation: Include all identified fixes in your next development cycle and establish ongoing "
                f"security testing practices."
            )
            return base + attack_explanation + recommendation

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
