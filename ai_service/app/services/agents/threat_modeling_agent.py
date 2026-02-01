"""
Threat Modeling Agent - RAG-Enhanced Offensive Security Expert

This agent thinks like a real attacker, augmented with specialized knowledge from:
- OWASP API Security Top 10
- MITRE ATT&CK patterns
- Real-world exploit techniques

RAG Enhancement: Before analyzing vulnerabilities, this agent queries the Attacker
Knowledge Base to retrieve relevant attack patterns and exploitation techniques,
transforming it from an AI tool into an AI security expert.

Code-Aware Enhancement: For enriched analysis requests, this agent uses source code
context (from RepoMind) to confirm spec-based findings and generate highly
accurate, implementation-specific attack chains.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...schemas.attack_path_schemas import (
    AttackChain,
    AttackComplexity,
    AttackPathContext,
    AttackStep,
    AttackStepType,
    EnrichedSecurityFinding,
)
from ...schemas.security_schemas import SecurityIssue, SecuritySeverity
from ..rag_service import RAGService
from .base_agent import LLMAgent

logger = logging.getLogger(__name__)


class ThreatModelingAgent(LLMAgent):
    """
    RAG and Code-Aware Threat Modeling Agent - Thinks like a penetration tester.
    """

    def __init__(self, llm_service, rag_service: Optional[RAGService] = None):
        super().__init__(
            name="ThreatModeling",
            description="Discovers multi-step attack chains using RAG and code-aware analysis.",
            llm_service=llm_service,
        )
        self.rag_service = rag_service or RAGService()

    async def execute(
        self, task: Dict[str, Any], context: AttackPathContext
    ) -> Dict[str, Any]:
        logger.info(f"[{self.name}] Starting threat modeling analysis...")
        start_time = datetime.utcnow()

        try:
            context.current_stage = "analyzing_chains"
            context.current_activity = "Analyzing attack chains with AI..."
            context.progress_percentage = 40.0

            is_enriched = task.get("is_enriched", False)
            vulnerabilities = context.individual_vulnerabilities

            if not vulnerabilities:
                return {
                    "success": True,
                    "attack_chains": [],
                    "analysis_summary": "No vulnerabilities found.",
                }

            rag_context = await self._query_attacker_knowledge(vulnerabilities)

            if is_enriched:
                logger.info(
                    f"[{self.name}] Building Code-Aware prompt with enriched findings."
                )
                prompt = self._build_code_aware_prompt(context, task, rag_context)
            else:
                logger.info(
                    f"[{self.name}] Building standard prompt from spec findings."
                )
                prompt = self._build_threat_modeling_prompt(
                    vulnerabilities, task, rag_context
                )

            # ... (rest of the execute method remains largely the same)
            context.current_activity = "AI is analyzing vulnerability chains..."
            context.progress_percentage = 50.0

            response = await self.llm_service.generate(
                model="mistral:7b-instruct",
                prompt=prompt,
                temperature=0.4,
                max_tokens=8000,
            )

            context.tokens_used += response.get("tokens_used", 0)
            llm_text = response.get("response", "")

            attack_chains = self._parse_attack_chains(llm_text, vulnerabilities)
            logger.info(f"[{self.name}] Discovered {len(attack_chains)} attack chains.")

            context.attack_chains = attack_chains
            context.stages_completed.append("analyzing_chains")
            context.progress_percentage = 70.0

            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            context.total_execution_time_ms += execution_time

            return {
                "success": True,
                "attack_chains": attack_chains,
                "analysis_summary": self._generate_summary(attack_chains),
                "tokens_used": response.get("tokens_used", 0),
                "execution_time_ms": execution_time,
            }

        except Exception as e:
            logger.error(
                f"[{self.name}] Error during threat modeling: {e}", exc_info=True
            )
            context.current_stage = "error"
            return {"success": False, "error": str(e), "attack_chains": []}

    def _build_code_aware_prompt(
        self,
        context: AttackPathContext,
        task: Dict[str, Any],
        rag_context: Dict[str, Any],
    ) -> str:
        """Builds a prompt that includes source code context for each finding."""

        enriched_findings_text = []
        for vuln in context.individual_vulnerabilities:
            code_ctx = context.code_context_map.get(vuln.endpoint)

            code_section = "No code context available."
            if code_ctx and code_ctx.code_snippet:
                code_section = f"""
**Code Context from RepoMind:**
- File: {code_ctx.file_path}
- Complexity: {code_ctx.complexity or 'N/A'} | Test Cases: {code_ctx.test_count or 'N/A'}
- Code Snippet:
```{code_ctx.language or 'java'}
{code_ctx.code_snippet}
```
"""

            finding_text = f"""
---
Finding: [{vuln.severity.value}] {vuln.title}
   Location: {vuln.endpoint}
   Description (from spec): {vuln.description}
   {code_section}
---
"""
            enriched_findings_text.append(finding_text)

        rag_knowledge_section = self._get_rag_section(rag_context)

        return f"""You are an expert security researcher and penetration tester...

{rag_knowledge_section}

**Your Mission**: Analyze the security findings below. Each finding includes the original issue from the API spec AND the actual source code that implements it. Use the source code as GROUND TRUTH to confirm the vulnerability and assess its real-world exploitability.

**Security Findings (Enriched with Code Context):**
{''.join(enriched_findings_text)}

**Analysis Guidelines**:
1. For each finding, first analyze the Code Snippet to confirm if the vulnerability is real.
2. Generate attack chains by combining CONFIRMED vulnerabilities.
3. Your reasoning MUST be based on the provided code. Refer to specific lines or logic.
   - Example: "The BOLA is confirmed because the code on line 42, `orderRepository.findById(orderId)`, fetches the order without any user ID comparison."
   - Example: "The Mass Assignment is confirmed because the controller on line 31 accepts the full `User` object, which includes the `role` field."

... (rest of the prompt is the same as the original, defining output format etc.)

**CRITICAL**: Return ONLY valid JSON. No markdown, no explanations outside JSON.
"""

    def _build_threat_modeling_prompt(
        self,
        vulnerabilities: List[SecurityIssue],
        task: Dict[str, Any],
        rag_context: Dict[str, Any],
    ) -> str:
        """Builds the original RAG-enhanced prompt for spec-only findings."""

        vuln_summary = []
        for idx, vuln in enumerate(vulnerabilities, 1):
            vuln_summary.append(
                f"Finding {idx}: [{vuln.severity.value.upper()}] {vuln.title}\n"
                f"   Location: {vuln.location}\n"
                f"   Description: {vuln.description}\n"
            )
        vulnerabilities_text = "\n".join(vuln_summary)

        rag_knowledge_section = self._get_rag_section(rag_context)

        max_chain_length = task.get("max_chain_length", 5)

        return f"""You are an expert security researcher...

{rag_knowledge_section}

**Your Mission**: Analyze the security findings below (discovered by our linter) and identify realistic multi-step ATTACK CHAINS.

**Security Findings Discovered by Linter** ({len(vulnerabilities)} total):
{vulnerabilities_text}

... (rest of the original prompt)

**CRITICAL**: Return ONLY valid JSON. No markdown, no explanations outside JSON.
"""

    def _get_rag_section(self, rag_context: Dict[str, Any]) -> str:
        if rag_context.get("available") and rag_context.get("context"):
            return f"""
**EXPERT KNOWLEDGE FROM SECURITY KNOWLEDGE BASE**:
{rag_context['context']}
Use this expert knowledge to inform your attack chain analysis.
---
"""
        return ""

    # ... The rest of the methods (_query_attacker_knowledge, _parse_attack_chains, _generate_summary, can_handle_task) remain the same.
    # I will omit them here for brevity but in a real replacement, they would be included.
    async def _query_attacker_knowledge(
        self, vulnerabilities: List[SecurityIssue]
    ) -> Dict[str, Any]:
        """
        Query the Attacker Knowledge Base for relevant exploitation techniques.
        """
        if not self.rag_service.attacker_kb_available():
            logger.warning(
                f"[{self.name}] Attacker KB not available. Operating without RAG enhancement."
            )
            return {"context": "", "sources": [], "available": False}
        # ... implementation ...
        return {"context": "mock rag context", "sources": [], "available": True}

    def _parse_attack_chains(
        self, llm_response: str, vulnerabilities: List[SecurityIssue]
    ) -> List[AttackChain]:
        # ... implementation ...
        return []

    def _generate_summary(self, attack_chains: List[AttackChain]) -> str:
        # ... implementation ...
        return "Summary of chains"

    def can_handle_task(self, task_type: str) -> bool:
        """Check if this agent can handle the given task type"""
        return task_type in [
            "threat_modeling",
            "find_attack_chains",
            "vulnerability_correlation",
        ]
