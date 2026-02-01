"""
Domain Analyzer Agent for SchemaSculpt AI.
Specializes in analyzing API domains and extracting business requirements.
"""

import json
from datetime import datetime
from typing import Any, Dict, List

from ...schemas.ai_schemas import LLMParameters
from .base_agent import LLMAgent


class DomainAnalyzerAgent(LLMAgent):
    """
    Agent specialized in analyzing API domains and business requirements.
    """

    def __init__(self, llm_service):
        super().__init__(
            name="DomainAnalyzer",
            description="Analyzes API domains, business requirements, and extracts entities and relationships",
            llm_service=llm_service,
        )

    def _define_capabilities(self) -> List[str]:
        return [
            "domain_analysis",
            "entity_extraction",
            "relationship_mapping",
            "business_requirement_analysis",
            "api_pattern_recognition",
        ]

    async def execute(
        self, task: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute domain analysis task."""
        try:
            await self._pre_execution_hook(task)
            start_time = datetime.utcnow()

            task_type = task.get("task_type")

            if task_type == "analyze_domain":
                result = await self._analyze_domain(task, context)
            elif task_type == "extract_entities":
                result = await self._extract_entities(task, context)
            elif task_type == "map_relationships":
                result = await self._map_relationships(task, context)
            else:
                return self._create_error_result(f"Unknown task type: {task_type}")

            execution_time = (datetime.utcnow() - start_time).total_seconds()
            await self._post_execution_hook(result, execution_time)

            return result

        except Exception as e:
            self.logger.error(f"Domain analysis failed: {str(e)}")
            return self._create_error_result(str(e), "DOMAIN_ANALYSIS_ERROR")

    async def _analyze_domain(
        self, task: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze the domain and business requirements."""
        user_prompt = task.get("input_data", {}).get("prompt", "")
        domain = task.get("input_data", {}).get("domain")

        system_prompt = self._build_system_prompt(
            """
You are an expert business analyst and API domain specialist. Your task is to analyze user requirements and provide comprehensive domain analysis.

**Analysis Framework:**
1. **Domain Identification**: Identify the primary business domain and sub-domains
2. **Stakeholder Analysis**: Identify key stakeholders and their needs
3. **Business Process Mapping**: Map key business processes and workflows
4. **Data Flow Analysis**: Understand how data flows through the system
5. **Integration Requirements**: Identify external systems and integrations
6. **Compliance Considerations**: Note any regulatory or compliance requirements

**Output Format:** Return a JSON object with the following structure:
{{
  "domain": "primary domain name",
  "sub_domains": ["list of sub-domains"],
  "stakeholders": [
    {{"name": "stakeholder name", "role": "role description", "needs": ["list of needs"]}}
  ],
  "business_processes": [
    {{"name": "process name", "description": "process description", "steps": ["list of steps"]}}
  ],
  "data_entities": ["list of primary data entities"],
  "integrations": ["list of external integrations needed"],
  "compliance_requirements": ["list of compliance considerations"],
  "complexity_assessment": "simple/medium/complex",
  "recommended_patterns": ["list of recommended API patterns"]
}}
"""
        )

        user_message = f"""
Analyze the following API requirements:

**User Request:** {user_prompt}
**Specified Domain:** {domain or "Not specified"}

Provide a comprehensive domain analysis following the specified format.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = await self._call_llm(messages, LLMParameters(temperature=0.3))
        analysis_data = await self._parse_llm_json_response(response)

        return self._create_success_result(
            analysis_data,
            {"analysis_type": "domain_analysis", "tokens_used": len(response.split())},
        )

    async def _extract_entities(
        self, task: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract entities and their properties from the domain analysis."""
        user_prompt = task.get("input_data", {}).get("prompt", "")
        domain_analysis = context.get("previous_results", [])

        # Extract domain context from previous analysis if available
        domain_context = ""
        if domain_analysis:
            for result in domain_analysis:
                if result.get("data", {}).get("domain"):
                    domain_context = f"Domain: {result['data']['domain']}\n"
                    if result["data"].get("business_processes"):
                        domain_context += f"Business Processes: {', '.join([p['name'] for p in result['data']['business_processes']])}\n"

        system_prompt = self._build_system_prompt(
            f"""
You are an expert data modeler and entity relationship specialist. Your task is to extract entities and their properties from business requirements.

{domain_context}

**Entity Extraction Guidelines:**
1. **Core Entities**: Identify primary business objects (nouns in requirements)
2. **Attributes**: Determine key properties for each entity
3. **Data Types**: Suggest appropriate data types for each attribute
4. **Relationships**: Identify how entities relate to each other
5. **Validation Rules**: Suggest validation constraints where applicable

**Output Format:** Return a JSON object with:
{{
  "entities": [
    {{
      "name": "EntityName",
      "description": "Entity description",
      "attributes": [
        {{
          "name": "attributeName",
          "type": "string|integer|boolean|array|object",
          "description": "attribute description",
          "required": true|false,
          "format": "email|uuid|date-time|etc (optional)",
          "validation": {{"min": 1, "max": 100}} // optional constraints
        }}
      ],
      "relationships": [
        {{"type": "one-to-many|many-to-one|many-to-many", "target": "TargetEntity", "description": "relationship description"}}
      ]
    }}
  ],
  "entity_count": 0,
  "complexity_score": "1-10",
  "suggested_patterns": ["list of recommended patterns"]
}}
"""
        )

        user_message = f"""
Extract entities and their properties from the following requirements:

{user_prompt}

Focus on identifying:
- Core business objects
- Their key attributes and data types
- Relationships between entities
- Validation requirements
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = await self._call_llm(messages, LLMParameters(temperature=0.2))
        entities_data = await self._parse_llm_json_response(response)

        return self._create_success_result(
            entities_data,
            {
                "analysis_type": "entity_extraction",
                "tokens_used": len(response.split()),
                "entity_count": len(entities_data.get("entities", [])),
            },
        )

    async def _map_relationships(
        self, task: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Map relationships between entities and create dependency graph."""
        entities_data = task.get("input_data", {}).get("entities", [])

        if not entities_data:
            # Try to get from context
            for result in context.get("previous_results", []):
                if result.get("data", {}).get("entities"):
                    entities_data = result["data"]["entities"]
                    break

        if not entities_data:
            return self._create_error_result(
                "No entities data provided for relationship mapping"
            )

        system_prompt = self._build_system_prompt(
            """
You are an expert system architect specializing in entity relationship modeling and dependency analysis.

**Relationship Mapping Tasks:**
1. **Dependency Analysis**: Identify dependencies between entities
2. **Cardinality Definition**: Define relationship cardinalities
3. **Cascade Rules**: Determine cascade delete/update rules
4. **Join Strategies**: Suggest optimal join strategies
5. **Performance Considerations**: Identify potential performance impacts

**Output Format:** Return a JSON object with:
{{
  "relationship_matrix": {{
    "EntityA": {{"EntityB": "one-to-many", "EntityC": "many-to-one"}},
    "EntityB": {{"EntityA": "many-to-one"}}
  }},
  "dependency_graph": [
    {{"from": "EntityA", "to": "EntityB", "type": "depends_on", "strength": "strong|weak"}}
  ],
  "cascade_rules": [
    {{"entity": "EntityA", "action": "delete", "cascades_to": ["EntityB"], "rule": "cascade|restrict|set_null"}}
  ],
  "join_recommendations": [
    {{"entities": ["EntityA", "EntityB"], "strategy": "inner|left|right", "performance": "low|medium|high"}}
  ],
  "complexity_warnings": ["list of potential complexity issues"]
}}
"""
        )

        entity_list = [entity["name"] for entity in entities_data]
        entity_descriptions = "\n".join(
            [
                f"- {entity['name']}: {entity.get('description', 'No description')}"
                for entity in entities_data
            ]
        )

        user_message = f"""
Map relationships between the following entities:

**Entities:**
{entity_descriptions}

**Detailed Entity Information:**
{json.dumps(entities_data, indent=2)}

Provide comprehensive relationship mapping and dependency analysis.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = await self._call_llm(messages, LLMParameters(temperature=0.2))
        relationship_data = await self._parse_llm_json_response(response)

        return self._create_success_result(
            relationship_data,
            {
                "analysis_type": "relationship_mapping",
                "tokens_used": len(response.split()),
                "entities_analyzed": len(entity_list),
            },
        )

    def _get_required_task_fields(self) -> List[str]:
        """Get required fields for domain analysis tasks."""
        return ["task_type", "input_data"]
