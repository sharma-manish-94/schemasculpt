"""
Path Generator Agent for SchemaSculpt AI.
Specializes in generating RESTful API paths and operations.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base_agent import LLMAgent
from ...schemas.ai_schemas import LLMParameters


class PathGeneratorAgent(LLMAgent):
    """
    Agent specialized in generating comprehensive RESTful API paths and operations.
    """

    def __init__(self, llm_service):
        super().__init__(
            name="PathGenerator",
            description="Generates comprehensive RESTful API paths with operations, parameters, and responses",
            llm_service=llm_service
        )

    def _define_capabilities(self) -> List[str]:
        return [
            "path_generation",
            "operation_design",
            "parameter_definition",
            "response_modeling",
            "security_integration",
            "api_versioning"
        ]

    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute path generation task."""
        try:
            await self._pre_execution_hook(task)
            start_time = datetime.utcnow()

            task_type = task.get("task_type")

            if task_type == "generate_paths":
                result = await self._generate_paths(task, context)
            elif task_type == "enhance_operations":
                result = await self._enhance_operations(task, context)
            elif task_type == "add_security":
                result = await self._add_security_schemes(task, context)
            elif task_type == "optimize_paths":
                result = await self._optimize_path_structure(task, context)
            else:
                return self._create_error_result(f"Unknown task type: {task_type}")

            execution_time = (datetime.utcnow() - start_time).total_seconds()
            await self._post_execution_hook(result, execution_time)

            return result

        except Exception as e:
            self.logger.error(f"Path generation failed: {str(e)}")
            return self._create_error_result(str(e), "PATH_GENERATION_ERROR")

    async def _generate_paths(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive RESTful paths for entities."""
        entities = task.get("input_data", {}).get("entities", [])
        schemas = task.get("input_data", {}).get("schemas", {})
        api_style = task.get("input_data", {}).get("api_style", "REST")

        # Try to get data from context if not provided
        if not entities or not schemas:
            for result in context.get("previous_results", []):
                if result.get("data", {}).get("entities") and not entities:
                    entities = result["data"]["entities"]
                if result.get("data", {}).get("schemas") and not schemas:
                    schemas = result["data"]["schemas"]

        if not entities:
            return self._create_error_result("No entities data provided for path generation")

        system_prompt = self._build_system_prompt(f"""
You are an expert RESTful API designer specializing in creating comprehensive, production-ready API paths and operations.

**API Design Principles:**
1. **RESTful Conventions**: Follow REST principles and HTTP semantics
2. **Resource-Oriented**: Design around resources, not actions
3. **Consistent Patterns**: Maintain consistent URL patterns and naming
4. **HTTP Methods**: Use appropriate HTTP verbs (GET, POST, PUT, PATCH, DELETE)
5. **Status Codes**: Include appropriate HTTP status codes
6. **Error Handling**: Comprehensive error responses

**API Style:** {api_style}

**Path Generation Guidelines:**
- Collection paths: `/entities` (plural)
- Item paths: `/entities/{{id}}`
- Nested resources: `/entities/{{id}}/subresources`
- Query parameters for filtering, sorting, pagination
- Consistent naming conventions (camelCase vs snake_case)

**Output Format:** Return a JSON object with:
{{
  "paths": {{
    "/path/pattern": {{
      "get": {{
        "summary": "Operation summary",
        "description": "Detailed description",
        "operationId": "uniqueOperationId",
        "tags": ["tag1"],
        "parameters": [
          {{
            "name": "parameter_name",
            "in": "path|query|header",
            "required": true|false,
            "schema": {{"type": "string"}},
            "description": "Parameter description"
          }}
        ],
        "responses": {{
          "200": {{
            "description": "Success response",
            "content": {{
              "application/json": {{
                "schema": {{"$ref": "#/components/schemas/SchemaName"}}
              }}
            }}
          }},
          "400": {{"description": "Bad request"}},
          "404": {{"description": "Not found"}},
          "500": {{"description": "Internal server error"}}
        }}
      }}
    }}
  }},
  "path_summary": {{
    "total_paths": 0,
    "total_operations": 0,
    "entities_covered": 0,
    "patterns_used": ["CRUD", "filtering", "pagination"]
  }},
  "api_patterns": [
    {{"pattern": "pagination", "implementation": "query parameters", "paths": ["list of paths using this pattern"]}}
  ]
}}
""")

        entity_info = "\n".join([
            f"**{entity['name']}:**\n" +
            f"- Description: {entity.get('description', 'No description')}\n" +
            f"- Attributes: {[attr['name'] for attr in entity.get('attributes', [])]}\n" +
            f"- Relationships: {[rel['target'] for rel in entity.get('relationships', [])]}\n"
            for entity in entities
        ])

        schema_info = f"**Available Schemas:** {list(schemas.keys())}" if schemas else "**No schemas provided**"

        user_message = f"""
Generate comprehensive RESTful API paths for the following entities:

{entity_info}

{schema_info}

**Requirements:**
1. Generate full CRUD operations for each entity
2. Include appropriate parameters (path, query, header)
3. Design proper response structures with status codes
4. Add filtering, sorting, and pagination for list operations
5. Include relationship-based endpoints where applicable
6. Follow {api_style} conventions
7. Reference appropriate schemas in responses

Create production-ready paths with comprehensive operation definitions.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        response = await self._call_llm(messages, LLMParameters(temperature=0.3))
        paths_data = await self._parse_llm_json_response(response)

        return self._create_success_result(paths_data, {
            "generation_type": "restful_paths",
            "tokens_used": len(response.split()),
            "entities_processed": len(entities),
            "paths_generated": len(paths_data.get("paths", {}))
        })

    async def _enhance_operations(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance existing operations with additional features."""
        existing_paths = task.get("input_data", {}).get("paths", {})
        enhancements = task.get("input_data", {}).get("enhancements", ["examples", "security", "validation"])

        if not existing_paths:
            return self._create_error_result("No paths provided for enhancement")

        system_prompt = self._build_system_prompt(f"""
You are an API enhancement specialist focused on adding advanced features to existing operations.

**Enhancement Categories:**
1. **Examples**: Add realistic request/response examples
2. **Security**: Integrate security schemes and requirements
3. **Validation**: Add comprehensive parameter validation
4. **Documentation**: Enhance descriptions and summaries
5. **Error Handling**: Improve error response definitions
6. **Performance**: Add caching headers and optimization hints

**Requested Enhancements:** {', '.join(enhancements)}

**Output Format:** Return a JSON object with:
{{
  "enhanced_paths": {{"enhanced version of input paths"}},
  "enhancements_applied": [
    {{"type": "enhancement_type", "path": "path", "operation": "method", "description": "what was added"}}
  ],
  "enhancement_summary": {{
    "examples_added": 0,
    "security_schemes_applied": 0,
    "validation_rules_added": 0,
    "documentation_improvements": 0
  }}
}}
""")

        user_message = f"""
Enhance the following API paths with the requested features:

**Current Paths:**
{json.dumps(existing_paths, indent=2)}

**Enhancement Requirements:**
{', '.join(enhancements)}

Focus on:
1. Adding realistic and helpful examples
2. Integrating appropriate security measures
3. Enhancing parameter validation
4. Improving documentation quality
5. Adding comprehensive error handling
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        response = await self._call_llm(messages, LLMParameters(temperature=0.2))
        enhancement_data = await self._parse_llm_json_response(response)

        return self._create_success_result(enhancement_data, {
            "enhancement_type": "operation_enhancement",
            "tokens_used": len(response.split()),
            "paths_enhanced": len(existing_paths),
            "enhancements_requested": enhancements
        })

    async def _add_security_schemes(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Add comprehensive security schemes to paths."""
        paths = task.get("input_data", {}).get("paths", {})
        security_requirements = task.get("input_data", {}).get("security", ["jwt", "api_key"])

        if not paths:
            return self._create_error_result("No paths provided for security enhancement")

        system_prompt = self._build_system_prompt(f"""
You are a security specialist expert in API security design and implementation.

**Security Scheme Types:**
1. **JWT Bearer Token**: Authorization: Bearer <token>
2. **API Key**: X-API-Key header or query parameter
3. **OAuth 2.0**: Various OAuth flows
4. **Basic Auth**: Username/password authentication
5. **Custom Headers**: Application-specific security headers

**Requested Security:** {', '.join(security_requirements)}

**Security Integration Guidelines:**
- Apply appropriate security to each operation
- Consider operation sensitivity levels
- Provide security scheme definitions
- Include security requirements per operation
- Add security-related error responses

**Output Format:** Return a JSON object with:
{{
  "secured_paths": {{"paths with security applied"}},
  "security_schemes": {{
    "scheme_name": {{
      "type": "http|apiKey|oauth2|openIdConnect",
      "scheme": "bearer|basic|etc",
      "bearerFormat": "JWT",
      "description": "Security scheme description"
    }}
  }},
  "security_summary": {{
    "schemes_defined": 0,
    "operations_secured": 0,
    "public_operations": 0,
    "security_levels": ["public", "authenticated", "admin"]
  }}
}}
""")

        user_message = f"""
Add comprehensive security schemes to the following API paths:

**Current Paths:**
{json.dumps(paths, indent=2)}

**Security Requirements:**
{', '.join(security_requirements)}

**Requirements:**
1. Define appropriate security schemes
2. Apply security to operations based on sensitivity
3. Include security-related error responses (401, 403)
4. Provide clear security documentation
5. Consider different access levels (public, user, admin)

Create a secure API design that balances security with usability.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        response = await self._call_llm(messages, LLMParameters(temperature=0.2))
        security_data = await self._parse_llm_json_response(response)

        return self._create_success_result(security_data, {
            "security_type": "comprehensive_security",
            "tokens_used": len(response.split()),
            "paths_secured": len(paths),
            "security_schemes": security_requirements
        })

    async def _optimize_path_structure(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize path structure for better organization and performance."""
        paths = task.get("input_data", {}).get("paths", {})
        optimization_goals = task.get("input_data", {}).get("goals", ["organization", "performance", "consistency"])

        if not paths:
            return self._create_error_result("No paths provided for optimization")

        system_prompt = self._build_system_prompt(f"""
You are a path structure optimization expert focusing on API organization and performance.

**Optimization Areas:**
1. **Organization**: Logical grouping and hierarchy
2. **Performance**: Reduce redundancy and improve efficiency
3. **Consistency**: Standardize patterns and naming
4. **Maintainability**: Improve long-term maintainability
5. **Discoverability**: Make API intuitive to use

**Optimization Goals:** {', '.join(optimization_goals)}

**Output Format:** Return a JSON object with:
{{
  "optimized_paths": {{"restructured and optimized paths"}},
  "optimizations_applied": [
    {{"type": "optimization_type", "description": "what was optimized", "impact": "benefit achieved"}}
  ],
  "structure_analysis": {{
    "path_groups": {{"group_name": ["list of related paths"]}},
    "naming_patterns": ["identified patterns"],
    "redundancy_eliminated": 0,
    "consistency_improvements": 0
  }},
  "recommendations": ["additional optimization suggestions"]
}}
""")

        user_message = f"""
Optimize the structure of the following API paths:

**Current Paths:**
{json.dumps(paths, indent=2)}

**Optimization Goals:**
{', '.join(optimization_goals)}

Focus on:
1. Improving path organization and grouping
2. Eliminating redundancy and inconsistencies
3. Standardizing naming conventions
4. Optimizing for performance and maintainability
5. Enhancing API discoverability

Provide a well-structured, efficient API design.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        response = await self._call_llm(messages, LLMParameters(temperature=0.2))
        optimization_data = await self._parse_llm_json_response(response)

        return self._create_success_result(optimization_data, {
            "optimization_type": "path_structure",
            "tokens_used": len(response.split()),
            "paths_optimized": len(paths),
            "optimization_goals": optimization_goals
        })

    def _get_required_task_fields(self) -> List[str]:
        """Get required fields for path generation tasks."""
        return ["task_type", "input_data"]