"""
Attack Path Simulation Data Structures

This module defines the data models for the AI-powered attack path simulation agent.
The attack path simulation finds multi-step attack chains by analyzing how individual
vulnerabilities can be combined by a real attacker.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .security_schemas import OWASPCategory, SecurityIssue, SecuritySeverity


class AttackStepType(str, Enum):
    """Types of steps in an attack chain"""

    RECONNAISSANCE = "reconnaissance"  # Information gathering
    INITIAL_ACCESS = "initial_access"  # First foothold
    PRIVILEGE_ESCALATION = "privilege_escalation"  # Gain higher privileges
    DATA_EXFILTRATION = "data_exfiltration"  # Steal sensitive data
    LATERAL_MOVEMENT = "lateral_movement"  # Move to other resources
    PERSISTENCE = "persistence"  # Maintain access
    DEFENSE_EVASION = "defense_evasion"  # Avoid detection


class AttackComplexity(str, Enum):
    """How difficult is the attack to execute"""

    LOW = "low"  # Minimal skill, easily exploitable
    MEDIUM = "medium"  # Moderate skill required
    HIGH = "high"  # Advanced techniques needed
    CRITICAL = "critical"  # Requires sophisticated expertise


class AttackStep(BaseModel):
    """Represents a single step in a multi-step attack chain"""

    step_number: int = Field(description="Order of this step in the chain")
    step_type: AttackStepType = Field(description="Type of attack step")
    vulnerability_id: str = Field(description="ID of the vulnerability being exploited")
    endpoint: str = Field(description="API endpoint being targeted")
    http_method: str = Field(description="HTTP method (GET, POST, PUT, etc.)")

    description: str = Field(description="What the attacker does in this step")
    technical_detail: str = Field(description="Technical explanation of exploitation")

    # Example exploitation
    example_request: Optional[str] = Field(None, description="Example HTTP request")
    example_payload: Optional[Dict[str, Any]] = Field(
        None, description="Example malicious payload"
    )
    expected_response: Optional[str] = Field(
        None, description="What attacker gets back"
    )

    # What's gained
    information_gained: List[str] = Field(
        default_factory=list, description="Information/access gained from this step"
    )

    # Prerequisites
    requires_authentication: bool = Field(description="Does this step need auth?")
    requires_previous_steps: List[int] = Field(
        default_factory=list, description="Which previous steps must succeed first"
    )


class AttackChain(BaseModel):
    """Represents a complete multi-step attack path"""

    chain_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(description="Descriptive name for this attack chain")

    # Severity assessment
    severity: SecuritySeverity = Field(description="Overall severity of this chain")
    complexity: AttackComplexity = Field(description="How hard to execute")
    likelihood: float = Field(
        ge=0.0, le=1.0, description="Probability of successful exploitation (0-1)"
    )
    impact_score: float = Field(
        ge=0.0, le=10.0, description="Business impact if exploited (0-10)"
    )

    # Attack details
    steps: List[AttackStep] = Field(description="Ordered list of attack steps")
    attack_goal: str = Field(description="What the attacker achieves")
    attacker_profile: str = Field(
        description="Skill level required (e.g., 'Script Kiddie', 'Advanced Persistent Threat')"
    )

    # MITRE ATT&CK mapping
    mitre_tactics: List[str] = Field(
        default_factory=list, description="MITRE ATT&CK tactics used"
    )

    # Business context
    business_impact: str = Field(description="Impact in business terms")
    affected_assets: List[str] = Field(
        default_factory=list, description="What resources/data are compromised"
    )

    # Mapping to OWASP
    owasp_categories: List[OWASPCategory] = Field(
        default_factory=list, description="OWASP API categories involved"
    )

    # References
    cve_references: List[str] = Field(
        default_factory=list, description="Related CVEs if applicable"
    )
    external_references: List[str] = Field(
        default_factory=list,
        description="External resources/articles about this attack pattern",
    )

    # Remediation
    remediation_priority: str = Field(description="IMMEDIATE, HIGH, MEDIUM, LOW")
    remediation_steps: List[str] = Field(
        default_factory=list, description="How to fix all vulnerabilities in this chain"
    )
    compensating_controls: List[str] = Field(
        default_factory=list,
        description="Temporary mitigations if can't fix immediately",
    )


class AttackPathContext(BaseModel):
    """
    Model Context Protocol (MCP) - The shared "war room" whiteboard
    for all agents in the attack path simulation.
    """

    context_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Input
    goal: str = Field(
        default="Find critical multi-step attack paths",
        description="What we're trying to discover",
    )
    spec: Dict[str, Any] = Field(description="The OpenAPI specification being analyzed")
    spec_hash: str = Field(description="Hash of spec for caching")

    # Agent outputs
    individual_vulnerabilities: List[SecurityIssue] = Field(
        default_factory=list,
        description="Single vulnerabilities found by Scanner Agent",
    )
    attack_chains: List[AttackChain] = Field(
        default_factory=list,
        description="Multi-step attack paths found by Threat Agent",
    )

    # Workflow state
    current_stage: str = Field(
        default="initialized",
        description="scanning | analyzing_chains | reporting | completed | error",
    )
    stages_completed: List[str] = Field(
        default_factory=list, description="Stages that have finished"
    )

    # Execution metadata
    total_execution_time_ms: float = Field(default=0.0)
    tokens_used: int = Field(default=0)

    # Progress tracking (for WebSocket updates)
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    current_activity: str = Field(default="Starting attack path simulation...")


class AttackPathAnalysisRequest(BaseModel):
    """Request for attack path simulation analysis"""

    spec_text: str = Field(description="OpenAPI spec (JSON or YAML)")
    analysis_depth: str = Field(
        default="comprehensive",
        description="quick | standard | comprehensive | exhaustive",
    )
    focus_areas: List[str] = Field(
        default_factory=list,
        description="Optional: specific endpoints/areas to focus on",
    )
    exclude_low_severity: bool = Field(
        default=False, description="Skip chains with only LOW severity vulnerabilities"
    )
    max_chain_length: int = Field(
        default=5, ge=2, le=10, description="Maximum steps in an attack chain"
    )


class AttackPathAnalysisReport(BaseModel):
    """Final report from the attack path simulation"""

    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    spec_hash: str = Field(description="Hash of analyzed spec")

    # Executive summary
    executive_summary: str = Field(
        description="High-level summary for executives/managers"
    )
    risk_level: str = Field(description="CRITICAL | HIGH | MEDIUM | LOW")
    overall_security_score: float = Field(
        ge=0.0, le=100.0, description="Overall security posture (0-100)"
    )

    # Findings
    critical_chains: List[AttackChain] = Field(
        default_factory=list,
        description="Most dangerous attack chains (CRITICAL severity)",
    )
    high_priority_chains: List[AttackChain] = Field(
        default_factory=list, description="High severity chains"
    )
    all_chains: List[AttackChain] = Field(
        default_factory=list, description="All discovered attack chains"
    )

    # Statistics
    total_chains_found: int = Field(description="Total attack chains discovered")
    total_vulnerabilities: int = Field(description="Individual vulnerabilities found")
    vulnerabilities_in_chains: int = Field(
        description="How many vulnerabilities are part of chains"
    )
    isolated_vulnerabilities: int = Field(
        description="Vulnerabilities not part of any chain"
    )

    # Top risks
    top_3_risks: List[str] = Field(
        default_factory=list, description="Top 3 attack chains explained simply"
    )

    # Remediation roadmap
    immediate_actions: List[str] = Field(
        default_factory=list, description="What to fix right now"
    )
    short_term_actions: List[str] = Field(
        default_factory=list, description="Fix within 1-2 weeks"
    )
    long_term_actions: List[str] = Field(
        default_factory=list, description="Architectural improvements"
    )

    # Metadata
    analysis_depth: str = Field(description="Level of analysis performed")
    execution_time_ms: float = Field(description="Time taken for analysis")
    tokens_used: int = Field(description="LLM tokens consumed")

    # Context for caching/debugging
    context_id: str = Field(description="ID of the AttackPathContext used")
