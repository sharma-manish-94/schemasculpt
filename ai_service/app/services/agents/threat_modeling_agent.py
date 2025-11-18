"""
Threat Modeling Agent - RAG-Enhanced Offensive Security Expert

This agent thinks like a real attacker, augmented with specialized knowledge from:
- OWASP API Security Top 10
- MITRE ATT&CK patterns
- Real-world exploit techniques

RAG Enhancement: Before analyzing vulnerabilities, this agent queries the Attacker
Knowledge Base to retrieve relevant attack patterns and exploitation techniques,
transforming it from an AI tool into an AI security expert.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_agent import LLMAgent
from ...schemas.attack_path_schemas import (
    AttackPathContext,
    AttackChain,
    AttackStep,
    AttackStepType,
    AttackComplexity
)
from ...schemas.security_schemas import SecurityIssue, SecuritySeverity
from ..rag_service import RAGService

logger = logging.getLogger(__name__)


class ThreatModelingAgent(LLMAgent):
    """
    RAG-Enhanced Threat Modeling Agent - Thinks like a penetration tester

    This agent uses LLM reasoning PLUS specialized security knowledge from RAG to:
    1. Query Attacker Knowledge Base for relevant exploitation techniques
    2. Analyze individual vulnerabilities for exploitation potential
    3. Identify vulnerabilities that can be chained together
    4. Model realistic attack sequences using OWASP/MITRE patterns
    5. Assess complexity, likelihood, and impact
    """

    def __init__(self, llm_service, rag_service: Optional[RAGService] = None):
        super().__init__(
            name="ThreatModeling",
            description="RAG-enhanced agent that discovers multi-step attack chains using offensive security expertise",
            llm_service=llm_service
        )
        # Initialize or receive RAG service
        self.rag_service = rag_service or RAGService()

    def _define_capabilities(self) -> List[str]:
        """Define the capabilities of this agent"""
        return [
            "attack_chain_discovery",
            "vulnerability_correlation",
            "threat_assessment",
            "exploitation_modeling",
            "impact_analysis"
        ]

    async def execute(self, task: Dict[str, Any], context: AttackPathContext) -> Dict[str, Any]:
        """
        Execute threat modeling to find attack chains

        Args:
            task: Task parameters with optional max_chain_length
            context: Attack path MCP context with vulnerabilities

        Returns:
            Dict with:
                - attack_chains: List[AttackChain]
                - analysis_summary: str
        """
        logger.info(f"[{self.name}] Starting threat modeling analysis...")
        start_time = datetime.utcnow()

        try:
            # Update context
            context.current_stage = "analyzing_chains"
            context.current_activity = "Analyzing attack chains with AI..."
            context.progress_percentage = 40.0

            vulnerabilities = context.individual_vulnerabilities
            if not vulnerabilities:
                logger.warning(f"[{self.name}] No vulnerabilities to analyze")
                return {
                    "success": True,
                    "attack_chains": [],
                    "analysis_summary": "No vulnerabilities found to chain"
                }

            # Get analysis parameters
            max_chain_length = task.get("max_chain_length", 5)
            analysis_depth = task.get("analysis_depth", "standard")

            logger.info(
                f"[{self.name}] Analyzing {len(vulnerabilities)} vulnerabilities "
                f"for attack chains (max length: {max_chain_length})"
            )

            # RAG ENHANCEMENT: Query Attacker Knowledge Base for relevant expertise
            rag_context = await self._query_attacker_knowledge(vulnerabilities)

            # Build the analysis prompt with RAG-enhanced context
            prompt = self._build_threat_modeling_prompt(
                vulnerabilities,
                context.spec,
                max_chain_length,
                analysis_depth,
                rag_context
            )

            # Call LLM to find attack chains with retry logic
            context.current_activity = "AI is analyzing vulnerability chains..."
            context.progress_percentage = 50.0

            attack_chains = []
            max_retries = 2

            for attempt in range(max_retries):
                try:
                    logger.info(f"[{self.name}] LLM analysis attempt {attempt + 1}/{max_retries}")

                    response = await self.llm_service.generate(
                        model="mistral:7b-instruct",
                        prompt=prompt,
                        temperature=0.4,  # Lower temperature for more focused analysis
                        max_tokens=8000  # Allow detailed analysis
                    )

                    # Update token usage
                    tokens_used = response.get("tokens_used", 0)
                    context.tokens_used += tokens_used
                    self._total_tokens_used += tokens_used

                    # Parse LLM response to extract attack chains
                    llm_text = response.get("response", "")

                    # Log response details for debugging (using proper logger)
                    logger.debug(f"[{self.name}] LLM response length: {len(llm_text)} characters")
                    logger.debug(f"[{self.name}] Response preview: {llm_text[:200]}")

                    if not llm_text or len(llm_text.strip()) < 10:
                        logger.warning(f"[{self.name}] Empty or very short LLM response on attempt {attempt + 1}")
                        if attempt < max_retries - 1:
                            continue
                        else:
                            logger.error(f"[{self.name}] All retry attempts exhausted with empty responses")
                            break

                    attack_chains = self._parse_attack_chains(
                        llm_text,
                        vulnerabilities,
                        context.spec
                    )

                    # Success - break retry loop
                    if attack_chains:
                        logger.info(f"[{self.name}] Successfully parsed {len(attack_chains)} chains on attempt {attempt + 1}")
                        break
                    elif attempt < max_retries - 1:
                        logger.warning(f"[{self.name}] No chains parsed on attempt {attempt + 1}, retrying...")

                except Exception as e:
                    logger.error(f"[{self.name}] Error during LLM analysis attempt {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        logger.info(f"[{self.name}] Retrying with simplified prompt...")
                        # On retry, use simpler prompt (could be customized further)
                        continue
                    else:
                        # Last attempt failed - log and continue with empty chains
                        logger.error(f"[{self.name}] All retry attempts failed")
                        attack_chains = []

            logger.info(f"[{self.name}] Discovered {len(attack_chains)} attack chains")

            # Store in context
            context.attack_chains = attack_chains
            context.stages_completed.append("analyzing_chains")
            context.progress_percentage = 70.0

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            context.total_execution_time_ms += execution_time

            # Generate summary
            summary = self._generate_summary(attack_chains)

            return {
                "success": True,
                "attack_chains": attack_chains,
                "analysis_summary": summary,
                "tokens_used": tokens_used,
                "execution_time_ms": execution_time
            }

        except Exception as e:
            logger.error(f"[{self.name}] Error during threat modeling: {e}", exc_info=True)
            context.current_stage = "error"
            return {
                "success": False,
                "error": str(e),
                "attack_chains": []
            }

    def can_handle_task(self, task_type: str) -> bool:
        """Check if this agent can handle the given task type"""
        return task_type in [
            "threat_modeling",
            "find_attack_chains",
            "vulnerability_correlation"
        ]

    async def _query_attacker_knowledge(
        self,
        vulnerabilities: List[SecurityIssue]
    ) -> Dict[str, Any]:
        """
        Query the Attacker Knowledge Base for relevant exploitation techniques.

        This is the KEY to transforming from an AI tool to an AI security expert.
        The agent retrieves OWASP patterns and MITRE ATT&CK techniques relevant
        to the discovered vulnerabilities.
        """
        if not self.rag_service.attacker_kb_available():
            logger.warning(f"[{self.name}] Attacker KB not available. Operating without RAG enhancement.")
            return {
                "context": "",
                "sources": [],
                "available": False
            }

        try:
            # Build RAG query based on vulnerability types and OWASP categories
            vuln_types = []
            owasp_categories = []

            for vuln in vulnerabilities:
                vuln_types.append(vuln.title)
                if vuln.owasp_category:
                    owasp_categories.append(vuln.owasp_category.value)

            # Create focused query for RAG
            query_parts = []
            if owasp_categories:
                unique_owasp = list(set(owasp_categories))
                query_parts.append(f"OWASP API Security: {', '.join(unique_owasp)}")

            query_parts.append("exploitation techniques attack patterns vulnerability chaining")
            query = " ".join(query_parts)

            logger.info(f"[{self.name}] Querying Attacker KB with: '{query[:100]}...'")

            # Query the Attacker Knowledge Base
            rag_result = await self.rag_service.query_attacker_knowledge(
                query=query,
                n_results=5  # Get top 5 most relevant attack patterns
            )

            if rag_result.get("context"):
                logger.info(
                    f"[{self.name}] Retrieved {rag_result.get('total_documents', 0)} "
                    f"relevant attack patterns from Attacker KB"
                )
            else:
                logger.warning(f"[{self.name}] No relevant attack patterns found in KB")

            return {
                "context": rag_result.get("context", ""),
                "sources": rag_result.get("sources", []),
                "available": True
            }

        except Exception as e:
            logger.error(f"[{self.name}] Error querying Attacker KB: {e}")
            return {
                "context": "",
                "sources": [],
                "available": False
            }

    def _build_threat_modeling_prompt(
        self,
        vulnerabilities: List[SecurityIssue],
        spec: Dict[str, Any],  # Not used anymore - kept for backward compatibility
        max_chain_length: int,
        analysis_depth: str,
        rag_context: Dict[str, Any]
    ) -> str:
        """
        Build the RAG-enhanced prompt for threat modeling analysis.

        ARCHITECTURE: "Linter-Augmented AI Analyst" Pattern
        - Java backend finds FACTS (vulnerabilities, dependencies) - deterministic, fast
        - AI reasons about those FACTS to find attack chains - probabilistic, creative
        - We do NOT send the spec to AI - that would be slow, expensive, unreliable
        """

        # Prepare vulnerability summary - these are FACTS from Java linter
        vuln_summary = []
        for idx, vuln in enumerate(vulnerabilities, 1):
            vuln_summary.append(
                f"Finding {idx}: [{vuln.severity.value.upper()}] {vuln.title}\n"
                f"   Location: {vuln.location}\n"
                f"   OWASP Category: {vuln.owasp_category.value if vuln.owasp_category else 'N/A'}\n"
                f"   Description: {vuln.description}\n"
                f"   Recommendation: {vuln.recommendation or 'N/A'}\n"
            )

        vulnerabilities_text = "\n".join(vuln_summary)

        # NO spec parsing here! Vulnerabilities already contain all location info
        # This is the "Linter-Augmented AI Analyst" pattern:
        # - Java found the facts (vulnerabilities with locations)
        # - AI connects the facts into attack chains

        # Build RAG-enhanced knowledge section
        rag_knowledge_section = ""
        if rag_context.get("available") and rag_context.get("context"):
            rag_knowledge_section = f"""
**EXPERT KNOWLEDGE FROM SECURITY KNOWLEDGE BASE**:
This specialized knowledge from OWASP, MITRE ATT&CK, and exploitation databases is provided to enhance your analysis:

{rag_context['context']}

Use this expert knowledge to inform your attack chain analysis. Look for patterns that match the provided OWASP categories and MITRE ATT&CK techniques.
---
"""
        else:
            logger.info(f"[{self.name}] Building prompt without RAG enhancement")

        prompt = f"""You are an expert security researcher and penetration tester with access to specialized offensive security knowledge.

{rag_knowledge_section}

**Your Mission**: Analyze the security findings below (discovered by our deterministic security linter) and identify realistic multi-step ATTACK CHAINS where these vulnerabilities can be combined.

**IMPORTANT**: You are NOT analyzing an OpenAPI spec directly. You are analyzing FACTS that have already been discovered. Think like a penetration tester connecting the dots between known vulnerabilities.

**Security Findings Discovered by Linter** ({len(vulnerabilities)} total):
{vulnerabilities_text}

**Analysis Guidelines**:
1. Look for vulnerabilities that can be used SEQUENTIALLY
2. Consider attack patterns like:
   - Information Disclosure → Privilege Escalation (e.g., exposed user IDs + insecure update endpoint)
   - Missing Auth → Data Exfiltration (e.g., unprotected endpoint exposing sensitive data)
   - IDOR → Mass Assignment (e.g., predictable IDs + unvalidated input)
   - Broken Function Level Authorization → Lateral Movement

3. For each attack chain you find:
   - Describe each step clearly
   - Explain what the attacker gains at each step
   - Explain how one step enables the next
   - Assess the overall severity and likelihood

4. Prioritize chains that:
   - Have CRITICAL or HIGH impact
   - Are REALISTIC (actually exploitable)
   - Require LOW to MEDIUM complexity
   - Lead to: privilege escalation, data breach, account takeover, or financial fraud

5. Maximum chain length: {max_chain_length} steps

**Output Format** (valid JSON only):
{{
  "attack_chains": [
    {{
      "name": "Descriptive name of attack",
      "attack_goal": "What attacker achieves (e.g., Privilege Escalation to Admin)",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "complexity": "low|medium|high",
      "likelihood": 0.0-1.0,
      "impact_score": 0.0-10.0,
      "attacker_profile": "Script Kiddie|Skilled Attacker|Advanced Persistent Threat",
      "business_impact": "Business consequence description",
      "steps": [
        {{
          "step_number": 1,
          "step_type": "reconnaissance|initial_access|privilege_escalation|data_exfiltration|lateral_movement",
          "vulnerability_id": "ID from vulnerabilities list",
          "endpoint": "/path/to/endpoint",
          "http_method": "GET|POST|PUT|DELETE",
          "description": "What attacker does",
          "technical_detail": "How to exploit",
          "example_request": "Sample HTTP request (optional)",
          "example_payload": {{"key": "malicious value"}},
          "expected_response": "What attacker gets back",
          "information_gained": ["user_id", "role", "access_token"],
          "requires_authentication": true|false,
          "requires_previous_steps": [list of step numbers]
        }}
      ],
      "remediation_steps": ["Fix 1", "Fix 2"],
      "remediation_priority": "IMMEDIATE|HIGH|MEDIUM|LOW"
    }}
  ],
  "analysis_notes": "Any additional insights or patterns you noticed"
}}

**CRITICAL**: Return ONLY valid JSON. No markdown, no explanations outside JSON, no code blocks. Just raw JSON.
"""

        return prompt

    def _parse_attack_chains(
        self,
        llm_response: str,
        vulnerabilities: List[SecurityIssue],
        spec: Dict[str, Any]
    ) -> List[AttackChain]:
        """Parse LLM response into AttackChain objects"""
        try:
            # Clean up response - remove markdown code blocks if present
            response_text = llm_response.strip()

            logger.info(f"[{self.name}] Parsing LLM response (length: {len(response_text)} chars)")
            logger.debug(f"[{self.name}] First 500 chars: {response_text[:500]}")

            if response_text.startswith("```"):
                # Remove markdown code block markers
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
                response_text = response_text.replace("```json", "").replace("```", "").strip()
                logger.debug(f"[{self.name}] Removed markdown code blocks")

            # Parse JSON
            try:
                data = json.loads(response_text)
            except json.JSONDecodeError as je:
                logger.error(f"[{self.name}] JSON parsing failed: {je}")
                logger.error(f"[{self.name}] Response text: {response_text[:1000]}")
                return []

            attack_chains_data = data.get("attack_chains", [])
            logger.info(f"[{self.name}] Found {len(attack_chains_data)} chains in LLM response")

            if not attack_chains_data:
                logger.warning(f"[{self.name}] No attack_chains key in response or empty list")
                logger.debug(f"[{self.name}] Response data keys: {list(data.keys())}")
                return []

            attack_chains = []
            for chain_idx, chain_data in enumerate(attack_chains_data):
                try:
                    logger.debug(f"[{self.name}] Parsing chain {chain_idx + 1}: {chain_data.get('name', 'unknown')}")

                    # Validate required chain fields
                    required_chain_fields = ["name", "attack_goal", "severity", "complexity", "steps"]
                    missing_fields = [f for f in required_chain_fields if f not in chain_data]
                    if missing_fields:
                        logger.warning(
                            f"[{self.name}] Chain {chain_idx + 1} missing required fields: {missing_fields}. Skipping."
                        )
                        continue

                    # Parse steps
                    steps = []
                    for step_idx, step_data in enumerate(chain_data.get("steps", [])):
                        try:
                            # Validate required step fields
                            required_step_fields = [
                                "step_number", "step_type", "vulnerability_id",
                                "endpoint", "http_method", "description", "technical_detail"
                            ]
                            missing_step_fields = [f for f in required_step_fields if f not in step_data]
                            if missing_step_fields:
                                logger.warning(
                                    f"[{self.name}] Chain {chain_idx + 1}, step {step_idx + 1} "
                                    f"missing fields: {missing_step_fields}. Using defaults."
                                )

                            # Convert step_type string to enum (handle variations)
                            step_type_str = step_data.get("step_type", "initial_access").lower()
                            step_type_map = {
                                "reconnaissance": AttackStepType.RECONNAISSANCE,
                                "initial_access": AttackStepType.INITIAL_ACCESS,
                                "privilege_escalation": AttackStepType.PRIVILEGE_ESCALATION,
                                "data_exfiltration": AttackStepType.DATA_EXFILTRATION,
                                "lateral_movement": AttackStepType.LATERAL_MOVEMENT,
                                "persistence": AttackStepType.PERSISTENCE,
                                "defense_evasion": AttackStepType.DEFENSE_EVASION,
                                "exploitation": AttackStepType.INITIAL_ACCESS  # Fallback for generic "exploitation"
                            }
                            step_type = step_type_map.get(step_type_str, AttackStepType.INITIAL_ACCESS)

                            step = AttackStep(
                                step_number=step_data.get("step_number", step_idx + 1),
                                step_type=step_type,
                                vulnerability_id=step_data.get("vulnerability_id", "unknown"),
                                endpoint=step_data.get("endpoint", "/unknown"),
                                http_method=step_data.get("http_method", "GET"),
                                description=step_data.get("description", "No description provided"),
                                technical_detail=step_data.get("technical_detail", "No technical details provided"),
                                example_request=step_data.get("example_request"),
                                example_payload=step_data.get("example_payload"),
                                expected_response=step_data.get("expected_response"),
                                information_gained=step_data.get("information_gained", []),
                                requires_authentication=step_data.get("requires_authentication", False),
                                requires_previous_steps=step_data.get("requires_previous_steps", [])
                            )
                            steps.append(step)

                        except Exception as step_error:
                            logger.warning(
                                f"[{self.name}] Failed to parse step {step_idx + 1} in chain {chain_idx + 1}: {step_error}. Skipping step."
                            )
                            continue

                    # Validate that we have at least one step
                    if not steps:
                        logger.warning(
                            f"[{self.name}] Chain {chain_idx + 1} '{chain_data.get('name', 'unknown')}' "
                            f"has no valid steps. Skipping chain."
                        )
                        continue

                    # Determine OWASP categories from vulnerabilities
                    owasp_categories = []
                    for step in steps:
                        vuln = next((v for v in vulnerabilities if v.id == step.vulnerability_id), None)
                        if vuln and vuln.owasp_category:
                            if vuln.owasp_category not in owasp_categories:
                                owasp_categories.append(vuln.owasp_category)

                    # Create attack chain
                    # Convert severity string to enum (handle both uppercase and lowercase)
                    severity_str = chain_data["severity"].upper()
                    severity_map = {
                        "CRITICAL": SecuritySeverity.CRITICAL,
                        "HIGH": SecuritySeverity.HIGH,
                        "MEDIUM": SecuritySeverity.MEDIUM,
                        "LOW": SecuritySeverity.LOW,
                        "INFO": SecuritySeverity.INFO
                    }
                    severity = severity_map.get(severity_str, SecuritySeverity.MEDIUM)

                    # Convert complexity (handle variations)
                    complexity_str = chain_data["complexity"].lower()
                    complexity_map = {
                        "low": AttackComplexity.LOW,
                        "medium": AttackComplexity.MEDIUM,
                        "high": AttackComplexity.HIGH,
                        "critical": AttackComplexity.CRITICAL
                    }
                    complexity = complexity_map.get(complexity_str, AttackComplexity.MEDIUM)

                    chain = AttackChain(
                        name=chain_data["name"],
                        severity=severity,
                        complexity=complexity,
                        likelihood=chain_data.get("likelihood", 0.5),
                        impact_score=chain_data.get("impact_score", 7.0),
                        steps=steps,
                        attack_goal=chain_data["attack_goal"],
                        attacker_profile=chain_data.get("attacker_profile", "Skilled Attacker"),
                        business_impact=chain_data.get("business_impact", ""),
                        owasp_categories=owasp_categories,
                        remediation_priority=chain_data.get("remediation_priority", "HIGH"),
                        remediation_steps=chain_data.get("remediation_steps", [])
                    )
                    attack_chains.append(chain)

                except Exception as e:
                    logger.error(f"[{self.name}] Error parsing chain {chain_idx + 1}: {e}", exc_info=True)
                    logger.error(f"[{self.name}] Chain data: {json.dumps(chain_data, indent=2)[:500]}")
                    continue

            logger.info(f"[{self.name}] Successfully parsed {len(attack_chains)} attack chains")
            return attack_chains

        except json.JSONDecodeError as e:
            logger.error(f"[{self.name}] Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response was: {llm_response[:500]}")
            return []
        except Exception as e:
            logger.error(f"[{self.name}] Error parsing attack chains: {e}", exc_info=True)
            logger.error(f"Full response: {llm_response[:1000]}")
            return []

    def _generate_summary(self, attack_chains: List[AttackChain]) -> str:
        """Generate a summary of discovered attack chains"""
        if not attack_chains:
            return "No attack chains discovered. Individual vulnerabilities may exist but cannot be easily chained."

        critical = [c for c in attack_chains if c.severity == SecuritySeverity.CRITICAL]
        high = [c for c in attack_chains if c.severity == SecuritySeverity.HIGH]

        summary_parts = [
            f"Discovered {len(attack_chains)} attack chain(s):",
            f"- {len(critical)} CRITICAL severity chains",
            f"- {len(high)} HIGH severity chains",
        ]

        if critical:
            summary_parts.append("\nMost Critical Chain:")
            summary_parts.append(f"  {critical[0].name}: {critical[0].attack_goal}")

        return "\n".join(summary_parts)
