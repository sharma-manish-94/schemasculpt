"""
Intelligent Multi-Agent Workflow for OpenAPI Generation.
Combines LLM intelligence with deterministic logic for reliable spec generation.
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..core.logging import get_logger
from ..core.exceptions import LLMError, ValidationError
from ..schemas.ai_schemas import AIRequest, AIResponse, GenerateSpecRequest, ValidationResult, PerformanceMetrics


@dataclass
class DomainEntity:
    """Represents a domain entity extracted from requirements."""
    name: str
    properties: Dict[str, str]  # property_name -> type
    relationships: List[str]    # related entity names
    operations: List[str]       # CRUD operations needed


@dataclass
class PathOperation:
    """Represents a REST operation on a resource."""
    method: str
    path: str
    summary: str
    description: str
    parameters: List[Dict[str, Any]]
    request_body: Optional[Dict[str, Any]]
    responses: Dict[str, Dict[str, Any]]
    tags: List[str]


class IntelligentOpenAPIWorkflow:
    """
    Multi-agent workflow that breaks OpenAPI generation into focused, manageable tasks.
    """

    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.logger = get_logger("intelligent_workflow")

    async def generate_specification(self, request: GenerateSpecRequest) -> AIResponse:
        """
        Execute the complete intelligent workflow for spec generation.
        """
        start_time = datetime.utcnow()

        try:
            # Phase 1: Domain Analysis
            domain_model = await self._analyze_domain(request)

            # Phase 2: Path Structure Generation
            path_operations = self._generate_path_structure(domain_model, request)

            # Phase 3: Schema Generation
            schemas = await self._generate_schemas(domain_model, path_operations)

            # Phase 4: Assembly & Validation
            final_spec = self._assemble_specification(
                request, domain_model, path_operations, schemas
            )

            # Validate the final result
            validation_result = self._validate_specification(final_spec)

            # Build response
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return AIResponse(
                updated_spec_text=json.dumps(final_spec, indent=2),
                operation_type=request.operation_type if hasattr(request, 'operation_type') else "generate",
                validation=validation_result,
                confidence_score=0.95,  # High confidence due to deterministic assembly
                changes_summary="Generated complete OpenAPI specification using intelligent multi-agent workflow",
                applied_patches=None,
                modified_paths=list(final_spec.get('paths', {}).keys()),
                performance=PerformanceMetrics(
                    processing_time_ms=processing_time,
                    token_count=len(str(final_spec)),
                    model_used="intelligent-workflow",
                    cache_hit=False,
                    retry_count=0
                ),
                context=None,
                follow_up_suggestions=[
                    "Review generated schemas for domain-specific optimizations",
                    "Consider adding authentication and authorization",
                    "Add comprehensive examples and documentation",
                    "Implement error handling patterns"
                ]
            )

        except Exception as e:
            self.logger.error(f"Intelligent workflow failed: {str(e)}")
            raise LLMError(f"Failed to generate specification: {str(e)}")

    async def _analyze_domain(self, request: GenerateSpecRequest) -> List[DomainEntity]:
        """
        Phase 1: Use LLM to understand domain and extract entities, then apply logic to structure them.
        """
        self.logger.info("Phase 1: Analyzing domain and extracting entities")

        # LLM Task: Domain analysis
        domain_prompt = f"""
Analyze this API requirement and extract the main entities and their relationships:

Requirement: {request.prompt}
Domain: {request.domain or 'general'}
Complexity: {request.complexity_level}

Extract:
1. Main entities (nouns/resources)
2. Key properties for each entity
3. Relationships between entities
4. Required operations (Create, Read, Update, Delete)

Respond with a simple JSON structure:
{{
  "entities": [
    {{
      "name": "EntityName",
      "properties": {{"property1": "string", "property2": "integer"}},
      "relationships": ["RelatedEntity1", "RelatedEntity2"],
      "operations": ["create", "read", "update", "delete"]
    }}
  ]
}}
"""

        # Get LLM analysis
        llm_request = AIRequest(
            spec_text="{}",  # Empty spec for domain analysis
            prompt=domain_prompt,
            operation_type="analyze"
        )

        llm_response = await self.llm_service._call_llm_with_retry(
            [{"role": "user", "content": domain_prompt}],
            request.llm_parameters if hasattr(request, 'llm_parameters') else None
        )

        # Logic Task: Parse and structure the analysis
        try:
            domain_data = json.loads(llm_response)
            entities = []

            for entity_data in domain_data.get('entities', []):
                entity = DomainEntity(
                    name=self._normalize_entity_name(entity_data.get('name', 'Unknown')),
                    properties=entity_data.get('properties', {}),
                    relationships=entity_data.get('relationships', []),
                    operations=self._standardize_operations(entity_data.get('operations', []))
                )
                entities.append(entity)

            # Apply domain-specific intelligence
            entities = self._enhance_entities_with_domain_logic(entities, request.domain)

            return entities

        except json.JSONDecodeError:
            # Fallback: Create a simple entity from the prompt
            self.logger.warning("LLM response not valid JSON, using fallback analysis")
            return self._fallback_domain_analysis(request)

    def _generate_path_structure(self, entities: List[DomainEntity], request: GenerateSpecRequest) -> List[PathOperation]:
        """
        Phase 2: Generate RESTful path structure using deterministic logic.
        """
        self.logger.info("Phase 2: Generating RESTful path structure")

        operations = []

        for entity in entities:
            resource_name = self._pluralize(entity.name.lower())
            single_resource = entity.name.lower()

            # Collection operations
            if 'read' in entity.operations:
                operations.append(PathOperation(
                    method='get',
                    path=f'/{resource_name}',
                    summary=f'List all {resource_name}',
                    description=f'Retrieve a list of {resource_name} with optional filtering and pagination',
                    parameters=self._generate_list_parameters(),
                    request_body=None,
                    responses=self._generate_list_responses(entity.name),
                    tags=[entity.name]
                ))

            if 'create' in entity.operations:
                operations.append(PathOperation(
                    method='post',
                    path=f'/{resource_name}',
                    summary=f'Create a new {single_resource}',
                    description=f'Create a new {single_resource} with the provided data',
                    parameters=[],
                    request_body=self._generate_create_request_body(entity.name),
                    responses=self._generate_create_responses(entity.name),
                    tags=[entity.name]
                ))

            # Individual resource operations
            if any(op in entity.operations for op in ['read', 'update', 'delete']):
                resource_path = f'/{resource_name}/{{id}}'

                if 'read' in entity.operations:
                    operations.append(PathOperation(
                        method='get',
                        path=resource_path,
                        summary=f'Get a {single_resource} by ID',
                        description=f'Retrieve a specific {single_resource} by its ID',
                        parameters=self._generate_id_parameter(),
                        request_body=None,
                        responses=self._generate_get_responses(entity.name),
                        tags=[entity.name]
                    ))

                if 'update' in entity.operations:
                    operations.append(PathOperation(
                        method='put',
                        path=resource_path,
                        summary=f'Update a {single_resource}',
                        description=f'Update an existing {single_resource} with new data',
                        parameters=self._generate_id_parameter(),
                        request_body=self._generate_update_request_body(entity.name),
                        responses=self._generate_update_responses(entity.name),
                        tags=[entity.name]
                    ))

                if 'delete' in entity.operations:
                    operations.append(PathOperation(
                        method='delete',
                        path=resource_path,
                        summary=f'Delete a {single_resource}',
                        description=f'Remove a {single_resource} from the system',
                        parameters=self._generate_id_parameter(),
                        request_body=None,
                        responses=self._generate_delete_responses(),
                        tags=[entity.name]
                    ))

        return operations

    async def _generate_schemas(self, entities: List[DomainEntity], operations: List[PathOperation]) -> Dict[str, Any]:
        """
        Phase 3: Generate JSON schemas with LLM assistance and logical validation.
        """
        self.logger.info("Phase 3: Generating JSON schemas")

        schemas = {}

        for entity in entities:
            # LLM Task: Generate schema properties
            schema_prompt = f"""
Generate a JSON schema for the entity "{entity.name}" with these properties: {entity.properties}

The schema should be a valid JSON Schema object with:
- Appropriate data types
- Validation rules (minLength, maxLength, format, etc.)
- Required fields
- Description for each property

Respond with only the JSON schema object, no additional text.
"""

            try:
                llm_response = await self.llm_service._call_llm_with_retry(
                    [{"role": "user", "content": schema_prompt}],
                    None
                )

                # Logic Task: Validate and enhance the schema
                schema = self._validate_and_enhance_schema(llm_response, entity)
                schemas[entity.name] = schema

            except Exception as e:
                self.logger.warning(f"LLM schema generation failed for {entity.name}, using fallback")
                schemas[entity.name] = self._generate_fallback_schema(entity)

        # Add common schemas
        schemas.update(self._generate_common_schemas())

        return schemas

    def _assemble_specification(self, request: GenerateSpecRequest, entities: List[DomainEntity],
                              operations: List[PathOperation], schemas: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 4: Assemble the complete OpenAPI specification using deterministic logic.
        """
        self.logger.info("Phase 4: Assembling final OpenAPI specification")

        # Build paths
        paths = {}
        for operation in operations:
            if operation.path not in paths:
                paths[operation.path] = {}

            # Build operation object
            op_obj = {
                "summary": operation.summary,
                "description": operation.description,
                "operationId": self._generate_operation_id(operation),
                "tags": operation.tags,
                "responses": operation.responses
            }

            if operation.parameters:
                op_obj["parameters"] = operation.parameters

            if operation.request_body:
                op_obj["requestBody"] = operation.request_body

            paths[operation.path][operation.method] = op_obj

        # Assemble final specification
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": self._generate_title(request),
                "version": "1.0.0",
                "description": self._generate_description(request, entities)
            },
            "paths": paths,
            "components": {
                "schemas": schemas
            }
        }

        # Add optional sections
        if request.include_security:
            spec["security"] = self._generate_security_schemes()

        return spec

    def _validate_specification(self, spec: Dict[str, Any]) -> ValidationResult:
        """
        Final validation using comprehensive logic checks.
        """
        errors = []
        warnings = []
        suggestions = []

        # Validate structure
        required_fields = ['openapi', 'info', 'paths']
        for field in required_fields:
            if field not in spec:
                errors.append(f"Missing required field: {field}")

        # Validate paths
        if 'paths' in spec:
            for path, path_obj in spec['paths'].items():
                if not path.startswith('/'):
                    errors.append(f"Path {path} must start with /")

                for method, operation in path_obj.items():
                    if method not in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                        continue

                    if not isinstance(operation, dict):
                        errors.append(f"Operation {method} in {path} must be an object")
                    elif 'responses' not in operation:
                        errors.append(f"Operation {method} in {path} missing responses")

        # Validate schema references
        if 'components' in spec and 'schemas' in spec['components']:
            refs = self._find_all_refs(spec)
            available_schemas = spec['components']['schemas'].keys()

            for ref in refs:
                if ref.startswith('#/components/schemas/'):
                    schema_name = ref.replace('#/components/schemas/', '')
                    if schema_name not in available_schemas:
                        errors.append(f"Reference {ref} points to non-existent schema")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )

    # Helper methods for each phase
    def _normalize_entity_name(self, name: str) -> str:
        """Normalize entity names to PascalCase."""
        return ''.join(word.capitalize() for word in re.split(r'[_\s-]+', name))

    def _standardize_operations(self, operations: List[str]) -> List[str]:
        """Standardize operation names."""
        standard_ops = []
        for op in operations:
            op_lower = op.lower()
            if op_lower in ['create', 'post', 'add', 'insert']:
                standard_ops.append('create')
            elif op_lower in ['read', 'get', 'fetch', 'retrieve', 'list']:
                standard_ops.append('read')
            elif op_lower in ['update', 'put', 'patch', 'modify', 'edit']:
                standard_ops.append('update')
            elif op_lower in ['delete', 'remove', 'destroy']:
                standard_ops.append('delete')
        return list(set(standard_ops))

    def _pluralize(self, word: str) -> str:
        """Simple pluralization logic."""
        if word.endswith('y'):
            return word[:-1] + 'ies'
        elif word.endswith(('s', 'sh', 'ch', 'x', 'z')):
            return word + 'es'
        else:
            return word + 's'

    def _generate_list_parameters(self) -> List[Dict[str, Any]]:
        """Generate standard list/pagination parameters."""
        return [
            {
                "name": "limit",
                "in": "query",
                "required": False,
                "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                "description": "Number of items to return"
            },
            {
                "name": "offset",
                "in": "query",
                "required": False,
                "schema": {"type": "integer", "minimum": 0, "default": 0},
                "description": "Number of items to skip"
            }
        ]

    def _generate_id_parameter(self) -> List[Dict[str, Any]]:
        """Generate standard ID path parameter."""
        return [
            {
                "name": "id",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "description": "Resource ID"
            }
        ]

    def _generate_create_request_body(self, entity_name: str) -> Dict[str, Any]:
        """Generate request body for create operations."""
        return {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{entity_name}"}
                }
            }
        }

    def _generate_update_request_body(self, entity_name: str) -> Dict[str, Any]:
        """Generate request body for update operations."""
        return {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{entity_name}"}
                }
            }
        }

    def _generate_list_responses(self, entity_name: str) -> Dict[str, Dict[str, Any]]:
        """Generate responses for list operations."""
        return {
            "200": {
                "description": "Successful response",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "array",
                            "items": {"$ref": f"#/components/schemas/{entity_name}"}
                        }
                    }
                }
            },
            "400": {"description": "Bad request"},
            "500": {"description": "Internal server error"}
        }

    def _generate_create_responses(self, entity_name: str) -> Dict[str, Dict[str, Any]]:
        """Generate responses for create operations."""
        return {
            "201": {
                "description": "Resource created successfully",
                "content": {
                    "application/json": {
                        "schema": {"$ref": f"#/components/schemas/{entity_name}"}
                    }
                }
            },
            "400": {"description": "Bad request"},
            "409": {"description": "Resource already exists"},
            "500": {"description": "Internal server error"}
        }

    def _generate_get_responses(self, entity_name: str) -> Dict[str, Dict[str, Any]]:
        """Generate responses for get operations."""
        return {
            "200": {
                "description": "Successful response",
                "content": {
                    "application/json": {
                        "schema": {"$ref": f"#/components/schemas/{entity_name}"}
                    }
                }
            },
            "404": {"description": "Resource not found"},
            "500": {"description": "Internal server error"}
        }

    def _generate_update_responses(self, entity_name: str) -> Dict[str, Dict[str, Any]]:
        """Generate responses for update operations."""
        return {
            "200": {
                "description": "Resource updated successfully",
                "content": {
                    "application/json": {
                        "schema": {"$ref": f"#/components/schemas/{entity_name}"}
                    }
                }
            },
            "404": {"description": "Resource not found"},
            "400": {"description": "Bad request"},
            "500": {"description": "Internal server error"}
        }

    def _generate_delete_responses(self) -> Dict[str, Dict[str, Any]]:
        """Generate responses for delete operations."""
        return {
            "204": {"description": "Resource deleted successfully"},
            "404": {"description": "Resource not found"},
            "500": {"description": "Internal server error"}
        }

    def _generate_operation_id(self, operation: PathOperation) -> str:
        """Generate camelCase operation ID."""
        path_parts = [part for part in operation.path.split('/') if part and not part.startswith('{')]
        method_name = operation.method

        if method_name == 'get' and operation.path.endswith('}'):
            method_name = 'getById'
        elif method_name == 'get':
            method_name = 'list'
        elif method_name == 'post':
            method_name = 'create'
        elif method_name == 'put':
            method_name = 'update'
        elif method_name == 'delete':
            method_name = 'delete'

        return method_name + ''.join(word.capitalize() for word in path_parts)

    def _validate_and_enhance_schema(self, llm_response: str, entity: DomainEntity) -> Dict[str, Any]:
        """Validate and enhance LLM-generated schema."""
        try:
            schema = json.loads(llm_response)

            # Ensure required structure
            if 'type' not in schema:
                schema['type'] = 'object'

            if 'properties' not in schema:
                schema['properties'] = {}

            # Add ID field if not present
            if 'id' not in schema['properties']:
                schema['properties']['id'] = {
                    "type": "string",
                    "format": "uuid",
                    "description": f"Unique identifier for the {entity.name}"
                }

            # Ensure required field
            if 'required' not in schema:
                schema['required'] = ['id']
            elif 'id' not in schema['required']:
                schema['required'].append('id')

            # Add metadata
            schema['additionalProperties'] = False
            if 'description' not in schema:
                schema['description'] = f"Schema for {entity.name} entity"

            return schema

        except json.JSONDecodeError:
            return self._generate_fallback_schema(entity)

    def _generate_fallback_schema(self, entity: DomainEntity) -> Dict[str, Any]:
        """Generate a fallback schema when LLM fails."""
        properties = {
            "id": {
                "type": "string",
                "format": "uuid",
                "description": f"Unique identifier for the {entity.name}"
            }
        }

        for prop_name, prop_type in entity.properties.items():
            properties[prop_name] = {
                "type": self._normalize_json_type(prop_type),
                "description": f"{prop_name.replace('_', ' ').title()}"
            }

        return {
            "type": "object",
            "required": ["id"],
            "properties": properties,
            "additionalProperties": False,
            "description": f"Schema for {entity.name} entity"
        }

    def _normalize_json_type(self, type_hint: str) -> str:
        """Normalize type hints to JSON Schema types."""
        type_lower = type_hint.lower()
        if type_lower in ['str', 'string', 'text']:
            return 'string'
        elif type_lower in ['int', 'integer', 'number']:
            return 'integer'
        elif type_lower in ['float', 'double', 'decimal']:
            return 'number'
        elif type_lower in ['bool', 'boolean']:
            return 'boolean'
        elif type_lower in ['list', 'array']:
            return 'array'
        elif type_lower in ['dict', 'object']:
            return 'object'
        else:
            return 'string'

    def _generate_common_schemas(self) -> Dict[str, Any]:
        """Generate common utility schemas."""
        return {
            "Error": {
                "type": "object",
                "required": ["code", "message"],
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Error code"
                    },
                    "message": {
                        "type": "string",
                        "description": "Error message"
                    },
                    "details": {
                        "type": "object",
                        "description": "Additional error details"
                    }
                }
            }
        }

    def _generate_title(self, request: GenerateSpecRequest) -> str:
        """Generate API title from request."""
        if hasattr(request, 'project_name') and request.project_name:
            return f"{request.project_name} API"
        elif request.domain:
            return f"{request.domain.title()} API"
        else:
            return "Generated API"

    def _generate_description(self, request: GenerateSpecRequest, entities: List[DomainEntity]) -> str:
        """Generate API description."""
        entity_names = [entity.name for entity in entities]
        return f"API for managing {', '.join(entity_names)} in the {request.domain or 'application'} domain."

    def _enhance_entities_with_domain_logic(self, entities: List[DomainEntity], domain: Optional[str]) -> List[DomainEntity]:
        """Apply domain-specific enhancements to entities."""
        if not domain:
            return entities

        # Add common fields based on domain
        common_fields = {
            "ecommerce": {"created_at": "string", "updated_at": "string"},
            "user-management": {"created_at": "string", "last_login": "string"},
            "library": {"created_at": "string", "status": "string"},
            "productivity": {"created_at": "string", "priority": "integer"}
        }

        if domain.lower() in common_fields:
            fields_to_add = common_fields[domain.lower()]
            for entity in entities:
                entity.properties.update(fields_to_add)

        return entities

    def _fallback_domain_analysis(self, request: GenerateSpecRequest) -> List[DomainEntity]:
        """Fallback domain analysis when LLM fails."""
        # Extract nouns from prompt as potential entities
        words = re.findall(r'\b[A-Za-z]+\b', request.prompt)
        potential_entities = [word for word in words if len(word) > 3 and word.lower() not in
                            ['create', 'manage', 'system', 'application', 'service']]

        if not potential_entities:
            potential_entities = ['Item']  # Ultimate fallback

        entities = []
        for entity_name in potential_entities[:3]:  # Limit to 3 entities
            entity = DomainEntity(
                name=self._normalize_entity_name(entity_name),
                properties={
                    "name": "string",
                    "description": "string",
                    "created_at": "string"
                },
                relationships=[],
                operations=["create", "read", "update", "delete"]
            )
            entities.append(entity)

        return entities

    def _generate_security_schemes(self) -> List[Dict[str, Any]]:
        """Generate basic security schemes."""
        return [
            {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        ]

    def _find_all_refs(self, obj, refs=None) -> List[str]:
        """Recursively find all $ref references."""
        if refs is None:
            refs = []

        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == '$ref' and isinstance(value, str):
                    refs.append(value)
                else:
                    self._find_all_refs(value, refs)
        elif isinstance(obj, list):
            for item in obj:
                self._find_all_refs(item, refs)

        return refs