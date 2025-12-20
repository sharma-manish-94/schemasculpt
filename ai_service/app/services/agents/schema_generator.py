"""
Schema Generator Agent for SchemaSculpt AI.
Specializes in generating OpenAPI schemas from entity definitions.
"""

import json
from datetime import datetime
from typing import Any, Dict, List

from ...schemas.ai_schemas import LLMParameters
from .base_agent import LLMAgent


class SchemaGeneratorAgent(LLMAgent):
    """
    Agent specialized in generating comprehensive OpenAPI schemas.
    """

    def __init__(self, llm_service):
        super().__init__(
            name="SchemaGenerator",
            description="Generates comprehensive OpenAPI schemas with validation, examples, and documentation",
            llm_service=llm_service,
        )

    def _define_capabilities(self) -> List[str]:
        return [
            "schema_generation",
            "validation_rules",
            "example_generation",
            "schema_optimization",
            "inheritance_modeling",
            "polymorphism_support",
        ]

    async def execute(
        self, task: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute schema generation task."""
        try:
            await self._pre_execution_hook(task)
            start_time = datetime.utcnow()

            task_type = task.get("task_type")

            if task_type == "generate_schemas":
                result = await self._generate_schemas(task, context)
            elif task_type == "optimize_schemas":
                result = await self._optimize_schemas(task, context)
            elif task_type == "add_validation":
                result = await self._add_validation_rules(task, context)
            elif task_type == "generate_examples":
                result = await self._generate_examples(task, context)
            else:
                return self._create_error_result(f"Unknown task type: {task_type}")

            execution_time = (datetime.utcnow() - start_time).total_seconds()
            await self._post_execution_hook(result, execution_time)

            return result

        except Exception as e:
            self.logger.error(f"Schema generation failed: {str(e)}")
            return self._create_error_result(str(e), "SCHEMA_GENERATION_ERROR")

    async def _generate_schemas(
        self, task: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate OpenAPI schemas from entity definitions."""
        entities = task.get("input_data", {}).get("entities", [])
        generation_options = task.get("input_data", {}).get("options", {})

        if not entities:
            # Try to get from context
            for result in context.get("previous_results", []):
                if result.get("data", {}).get("entities"):
                    entities = result["data"]["entities"]
                    break

        if not entities:
            return self._create_error_result(
                "No entities data provided for schema generation"
            )

        system_prompt = self._build_system_prompt(
            f"""
You are an expert OpenAPI schema architect specializing in creating comprehensive, production-ready schemas.

**Schema Generation Principles:**
1. **Type Safety**: Use precise data types and formats
2. **Validation**: Include appropriate validation constraints
3. **Documentation**: Provide clear descriptions and examples
4. **Consistency**: Maintain consistent naming and patterns
5. **Extensibility**: Design for future extensibility
6. **Performance**: Consider serialization efficiency

**Advanced Features to Include:**
- JSON Schema validation (min/max, patterns, enums)
- Conditional schemas (oneOf, anyOf, allOf)
- Schema composition and inheritance
- Comprehensive examples
- Clear descriptions for all properties

**Output Format:** Return a JSON object with:
{{
  "schemas": {{
    "EntityName": {{
      "type": "object",
      "required": ["requiredField1", "requiredField2"],
      "properties": {{
        "propertyName": {{
          "type": "string",
          "description": "Property description",
          "example": "example value",
          "format": "email|uuid|date-time|etc",
          "validation_constraints": "if applicable"
        }}
      }},
      "description": "Schema description",
      "additionalProperties": false
    }}
  }},
  "schema_count": 0,
  "complexity_analysis": {{
    "total_properties": 0,
    "validation_rules": 0,
    "relationships": 0,
    "inheritance_chains": 0
  }},
  "recommendations": ["list of optimization recommendations"]
}}
"""
        )

        options_text = f"""
**Generation Options:**
- Include Examples: {generation_options.get('include_examples', True)}
- Strict Validation: {generation_options.get('strict_validation', True)}
- Additional Properties: {generation_options.get('additional_properties', False)}
- Schema Format: {generation_options.get('format', 'OpenAPI 3.0')}
"""

        entities_text = "\n".join(
            [
                f"**{entity['name']}:**\n"
                + f"Description: {entity.get('description', 'No description')}\n"
                + f"Attributes: {json.dumps(entity.get('attributes', []), indent=2)}\n"
                + f"Relationships: {json.dumps(entity.get('relationships', []), indent=2)}\n"
                for entity in entities
            ]
        )

        user_message = f"""
Generate comprehensive OpenAPI schemas for the following entities:

{options_text}

**Entities to Process:**
{entities_text}

Create production-ready schemas with:
1. Appropriate data types and formats
2. Validation constraints based on business rules
3. Clear documentation and examples
4. Proper handling of relationships
5. Schema composition where beneficial
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = await self._call_llm(messages, LLMParameters(temperature=0.2))
        schema_data = await self._parse_llm_json_response(response)

        return self._create_success_result(
            schema_data,
            {
                "generation_type": "comprehensive_schemas",
                "tokens_used": len(response.split()),
                "entities_processed": len(entities),
                "schemas_generated": len(schema_data.get("schemas", {})),
            },
        )

    async def _optimize_schemas(
        self, task: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize existing schemas for performance and maintainability."""
        existing_schemas = task.get("input_data", {}).get("schemas", {})
        optimization_goals = task.get("input_data", {}).get(
            "goals", ["performance", "maintainability"]
        )

        if not existing_schemas:
            return self._create_error_result("No schemas provided for optimization")

        system_prompt = self._build_system_prompt(
            f"""
You are a schema optimization expert focusing on performance, maintainability, and best practices.

**Optimization Areas:**
1. **Performance**: Reduce schema complexity and validation overhead
2. **Maintainability**: Improve schema organization and reusability
3. **Validation Efficiency**: Optimize constraint checking
4. **Size Reduction**: Minimize schema size while preserving functionality
5. **Composition**: Use allOf, oneOf, anyOf effectively
6. **Inheritance**: Create proper schema hierarchies

**Optimization Goals:** {', '.join(optimization_goals)}

**Output Format:** Return a JSON object with:
{{
  "optimized_schemas": {{"same structure as input but optimized"}},
  "optimizations_applied": [
    {{"type": "optimization_type", "schema": "schema_name", "description": "what was optimized", "impact": "performance|size|maintainability"}}
  ],
  "metrics": {{
    "size_reduction_percent": 0,
    "complexity_reduction": 0,
    "validation_efficiency_gain": 0
  }},
  "recommendations": ["additional optimization suggestions"]
}}
"""
        )

        user_message = f"""
Optimize the following OpenAPI schemas:

**Current Schemas:**
{json.dumps(existing_schemas, indent=2)}

**Optimization Goals:**
{', '.join(optimization_goals)}

Focus on:
1. Reducing redundancy through schema composition
2. Improving validation performance
3. Enhancing maintainability
4. Preserving all functionality
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = await self._call_llm(messages, LLMParameters(temperature=0.1))
        optimization_data = await self._parse_llm_json_response(response)

        return self._create_success_result(
            optimization_data,
            {
                "optimization_type": "schema_optimization",
                "tokens_used": len(response.split()),
                "schemas_optimized": len(existing_schemas),
                "optimizations_count": len(
                    optimization_data.get("optimizations_applied", [])
                ),
            },
        )

    async def _add_validation_rules(
        self, task: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add comprehensive validation rules to schemas."""
        schemas = task.get("input_data", {}).get("schemas", {})
        business_rules = task.get("input_data", {}).get("business_rules", [])

        if not schemas:
            return self._create_error_result(
                "No schemas provided for validation enhancement"
            )

        system_prompt = self._build_system_prompt(
            f"""
You are a validation specialist expert in JSON Schema validation and business rule implementation.

**Validation Categories:**
1. **Data Type Validation**: Ensure proper types and formats
2. **Range Validation**: Min/max values, lengths, counts
3. **Pattern Validation**: Regular expressions for specific formats
4. **Business Logic**: Custom validation rules
5. **Cross-Field Validation**: Dependencies between fields
6. **Conditional Validation**: Rules that apply under specific conditions

**Business Rules to Consider:**
{json.dumps(business_rules, indent=2) if business_rules else "No specific business rules provided"}

**Output Format:** Return a JSON object with:
{{
  "enhanced_schemas": {{"schemas with added validation rules"}},
  "validation_summary": {{
    "rules_added": 0,
    "validation_types": ["type", "format", "pattern", "range", "business"],
    "complexity_increase": "low|medium|high"
  }},
  "business_rules_implemented": [
    {{"rule": "business rule description", "schema": "affected schema", "implementation": "how it was implemented"}}
  ],
  "validation_examples": [
    {{"schema": "schema_name", "valid_example": {{}}, "invalid_example": {{}}, "error_message": "expected error"}}
  ]
}}
"""
        )

        user_message = f"""
Add comprehensive validation rules to the following schemas:

**Current Schemas:**
{json.dumps(schemas, indent=2)}

**Requirements:**
1. Add appropriate type and format validation
2. Include range and pattern constraints where applicable
3. Implement business logic validation
4. Add clear error messages
5. Provide validation examples

Focus on creating robust validation that catches common errors while maintaining usability.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = await self._call_llm(messages, LLMParameters(temperature=0.2))
        validation_data = await self._parse_llm_json_response(response)

        return self._create_success_result(
            validation_data,
            {
                "enhancement_type": "validation_rules",
                "tokens_used": len(response.split()),
                "schemas_enhanced": len(schemas),
                "business_rules_processed": len(business_rules),
            },
        )

    async def _generate_examples(
        self, task: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive examples for schemas."""
        schemas = task.get("input_data", {}).get("schemas", {})
        example_types = task.get("input_data", {}).get(
            "types", ["valid", "invalid", "edge_cases"]
        )

        if not schemas:
            return self._create_error_result(
                "No schemas provided for example generation"
            )

        system_prompt = self._build_system_prompt(
            f"""
You are an example generation specialist creating realistic, comprehensive examples for API schemas.

**Example Categories:**
1. **Valid Examples**: Perfect examples that pass all validation
2. **Invalid Examples**: Examples that fail validation with clear reasons
3. **Edge Cases**: Boundary conditions and special cases
4. **Realistic Data**: Examples that reflect real-world usage
5. **Diverse Scenarios**: Various use cases and contexts

**Example Types Requested:** {', '.join(example_types)}

**Output Format:** Return a JSON object with:
{{
  "schema_examples": {{
    "SchemaName": {{
      "valid_examples": [
        {{"description": "example description", "data": {{}}, "use_case": "when to use this"}}
      ],
      "invalid_examples": [
        {{"description": "why invalid", "data": {{}}, "expected_errors": ["list of validation errors"]}}
      ],
      "edge_cases": [
        {{"description": "edge case description", "data": {{}}, "notes": "special considerations"}}
      ]
    }}
  }},
  "example_statistics": {{
    "total_examples": 0,
    "valid_examples": 0,
    "invalid_examples": 0,
    "edge_cases": 0
  }},
  "quality_metrics": {{
    "diversity_score": "1-10",
    "realism_score": "1-10",
    "coverage_score": "1-10"
  }}
}}
"""
        )

        user_message = f"""
Generate comprehensive examples for the following schemas:

**Schemas:**
{json.dumps(schemas, indent=2)}

**Requirements:**
1. Create realistic, diverse examples
2. Include both valid and invalid cases
3. Cover edge cases and boundary conditions
4. Provide clear explanations for each example
5. Ensure examples reflect real-world usage patterns

Generate examples that help developers understand proper schema usage.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = await self._call_llm(messages, LLMParameters(temperature=0.4))
        examples_data = await self._parse_llm_json_response(response)

        return self._create_success_result(
            examples_data,
            {
                "generation_type": "schema_examples",
                "tokens_used": len(response.split()),
                "schemas_processed": len(schemas),
                "example_types": example_types,
            },
        )

    def _get_required_task_fields(self) -> List[str]:
        """Get required fields for schema generation tasks."""
        return ["task_type", "input_data"]
