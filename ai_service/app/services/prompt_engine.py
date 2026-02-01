"""
Intelligent Prompt Engineering Engine for SchemaSculpt AI.
Provides advanced prompt templates, context management, and dynamic prompt optimization.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..core.logging import get_logger
from ..schemas.ai_schemas import AIRequest, OperationType


class PromptTemplate(str, Enum):
    """Available prompt templates."""

    SYSTEM_ARCHITECT = "system_architect"
    CODE_GENERATOR = "code_generator"
    VALIDATOR = "validator"
    OPTIMIZER = "optimizer"
    SECURITY_EXPERT = "security_expert"
    DOMAIN_EXPERT = "domain_expert"


@dataclass
class PromptContext:
    """Context information for prompt generation."""

    operation_history: List[str]
    spec_complexity: str
    domain_knowledge: Dict[str, Any]
    user_preferences: Dict[str, Any]
    error_patterns: List[str]
    success_patterns: List[str]


class PromptEngine:
    """
    Advanced prompt engineering engine with context awareness and optimization.
    """

    def __init__(self):
        self.logger = get_logger("prompt_engine")

        # Load prompt templates
        self._templates = self._load_prompt_templates()

        # Context memory for learning
        self._context_memory: Dict[str, PromptContext] = {}

        # Pattern recognition for optimization
        self._success_patterns = []
        self._failure_patterns = []

    def generate_intelligent_prompt(
        self, request: AIRequest, context_id: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate intelligent system and user prompts based on request and context.

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        self.logger.info(
            f"Generating intelligent prompt for operation: {request.operation_type}"
        )

        # Analyze the request to determine optimal prompt strategy
        prompt_strategy = self._analyze_prompt_strategy(request)

        # Get or create context
        context = self._get_or_create_context(context_id, request)

        # Generate system prompt
        system_prompt = self._generate_system_prompt(request, prompt_strategy, context)

        # Generate user prompt
        user_prompt = self._generate_user_prompt(request, prompt_strategy, context)

        return system_prompt, user_prompt

    def _analyze_prompt_strategy(self, request: AIRequest) -> Dict[str, Any]:
        """
        Analyze the request to determine the optimal prompting strategy.
        """
        strategy = {
            "template": self._select_template(request),
            "complexity_level": self._assess_request_complexity(request),
            "requires_chain_of_thought": self._needs_cot(request),
            "requires_examples": self._needs_examples(request),
            "requires_constraints": self._needs_constraints(request),
            "tone": self._determine_tone(request),
        }

        return strategy

    def _select_template(self, request: AIRequest) -> PromptTemplate:
        """Select the most appropriate prompt template."""
        operation_mapping = {
            OperationType.MODIFY: PromptTemplate.SYSTEM_ARCHITECT,
            OperationType.GENERATE: PromptTemplate.CODE_GENERATOR,
            OperationType.VALIDATE: PromptTemplate.VALIDATOR,
            OperationType.OPTIMIZE: PromptTemplate.OPTIMIZER,
            OperationType.ENHANCE: PromptTemplate.SYSTEM_ARCHITECT,
            OperationType.PATCH: PromptTemplate.SYSTEM_ARCHITECT,
        }

        return operation_mapping.get(
            request.operation_type, PromptTemplate.SYSTEM_ARCHITECT
        )

    def _assess_request_complexity(self, request: AIRequest) -> str:
        """Assess the complexity of the request."""
        try:
            spec_data = json.loads(request.spec_text)
            path_count = len(spec_data.get("paths", {}))
            component_count = len(spec_data.get("components", {}).get("schemas", {}))

            total_complexity = path_count + component_count

            if total_complexity < 5:
                return "simple"
            elif total_complexity < 20:
                return "medium"
            else:
                return "complex"

        except (json.JSONDecodeError, TypeError, AttributeError):
            return "unknown"

    def _needs_cot(self, request: AIRequest) -> bool:
        """Determine if chain-of-thought reasoning is needed."""
        complex_operations = [OperationType.GENERATE, OperationType.OPTIMIZE]
        return (
            request.operation_type in complex_operations
            or len(request.prompt.split()) > 20
            or "complex" in request.prompt.lower()
        )

    def _needs_examples(self, request: AIRequest) -> bool:
        """Determine if examples would be helpful."""
        return (
            request.operation_type == OperationType.GENERATE
            or "example" in request.prompt.lower()
            or "sample" in request.prompt.lower()
        )

    def _needs_constraints(self, request: AIRequest) -> bool:
        """Determine if explicit constraints are needed."""
        return (
            request.validate_output
            or request.target_paths is not None
            or "must" in request.prompt.lower()
        )

    def _determine_tone(self, request: AIRequest) -> str:
        """Determine the appropriate tone for the response."""
        if request.operation_type == OperationType.VALIDATE:
            return "precise"
        elif request.operation_type == OperationType.GENERATE:
            return "creative"
        else:
            return "professional"

    def _get_or_create_context(
        self, context_id: Optional[str], request: AIRequest
    ) -> PromptContext:
        """Get existing context or create new one."""
        if context_id and context_id in self._context_memory:
            context = self._context_memory[context_id]
            # Update with current request
            context.operation_history.append(str(request.operation_type))
            return context

        # Create new context
        context = PromptContext(
            operation_history=[str(request.operation_type)],
            spec_complexity=self._assess_request_complexity(request),
            domain_knowledge={},
            user_preferences={},
            error_patterns=[],
            success_patterns=[],
        )

        if context_id:
            self._context_memory[context_id] = context

        return context

    def _generate_system_prompt(
        self, request: AIRequest, strategy: Dict[str, Any], context: PromptContext
    ) -> str:
        """Generate an intelligent system prompt."""

        template = self._templates[strategy["template"]]

        # Base system prompt
        system_sections = [
            template["role_definition"],
            self._get_expertise_section(strategy, context),
            self._get_methodology_section(strategy),
            self._get_constraints_section(request, strategy),
            self._get_output_format_section(request, strategy),
        ]

        # Add chain-of-thought if needed
        if strategy["requires_chain_of_thought"]:
            system_sections.append(self._get_cot_section())

        # Add context awareness
        if context.operation_history:
            system_sections.append(self._get_context_section(context))

        return "\n\n".join(filter(None, system_sections))

    def _generate_user_prompt(
        self, request: AIRequest, strategy: Dict[str, Any], context: PromptContext
    ) -> str:
        """Generate an intelligent user prompt."""

        user_sections = [
            self._get_specification_analysis(request),
            self._get_task_description(request, strategy),
            self._get_specification_content(request),
            self._get_requirements_section(request, strategy),
        ]

        # Add examples if helpful
        if strategy["requires_examples"]:
            user_sections.append(self._get_examples_section(request))

        # Add success criteria
        user_sections.append(self._get_success_criteria(request, strategy))

        return "\n\n".join(filter(None, user_sections))

    def _get_expertise_section(
        self, strategy: Dict[str, Any], context: PromptContext
    ) -> str:
        """Generate expertise and capabilities section."""
        complexity = strategy["complexity_level"]

        if complexity == "complex":
            return """**Your Expertise:**
- Advanced OpenAPI 3.0+ specification design and architecture
- Complex system integration patterns and microservices design
- Enterprise-grade API security and performance optimization
- Advanced schema design with inheritance and polymorphism
- Real-world production API patterns and best practices"""

        elif complexity == "medium":
            return """**Your Expertise:**
- OpenAPI 3.0 specification design and best practices
- RESTful API design patterns and conventions
- Schema design and validation rules
- Common security patterns and authentication schemes
- API documentation and example generation"""

        else:
            return """**Your Expertise:**
- OpenAPI 3.0 specification fundamentals
- Basic RESTful API design principles
- Simple schema definition and validation
- Standard HTTP methods and response codes"""

    def _get_methodology_section(self, strategy: Dict[str, Any]) -> str:
        """Generate methodology section based on strategy."""
        if strategy["requires_chain_of_thought"]:
            return """**Your Methodology:**
1. **Analysis Phase**: Carefully examine the current specification and requirements
2. **Design Phase**: Plan the optimal approach considering best practices and constraints
3. **Implementation Phase**: Apply changes systematically with attention to detail
4. **Validation Phase**: Verify the result meets all requirements and standards
5. **Optimization Phase**: Ensure the result is clean, efficient, and maintainable

Think through each phase explicitly in your reasoning."""

        else:
            return """**Your Methodology:**
- Analyze the current specification structure and requirements
- Apply industry best practices and OpenAPI standards
- Ensure all changes maintain specification integrity
- Validate the result for correctness and completeness"""

    def _get_constraints_section(
        self, request: AIRequest, strategy: Dict[str, Any]
    ) -> str:
        """Generate constraints section."""
        constraints = ["**Critical Constraints:**"]

        # Universal constraints
        constraints.extend(
            [
                "- Output ONLY valid JSON without any commentary or markdown formatting",
                "- Preserve existing specification structure unless explicitly asked to change",
                "- Maintain all existing references and relationships",
                "- Follow OpenAPI 3.0+ specification standards strictly",
            ]
        )

        # Request-specific constraints
        if request.validate_output:
            constraints.append("- Ensure the output passes OpenAPI validation")

        if request.preserve_formatting:
            constraints.append("- Maintain consistent formatting and style")

        if request.target_paths:
            constraints.append(
                f"- Focus changes on specified paths: {', '.join(request.target_paths)}"
            )

        # Strategy-specific constraints
        if strategy["tone"] == "precise":
            constraints.append("- Be extremely precise and conservative with changes")
        elif strategy["tone"] == "creative":
            constraints.append("- Be creative while maintaining specification validity")

        return "\n".join(constraints)

    def _get_output_format_section(
        self, request: AIRequest, strategy: Dict[str, Any]
    ) -> str:
        """Generate output format requirements."""
        return """**Output Format Requirements:**
- Return a complete, valid OpenAPI JSON specification
- No placeholders, truncation, or "..." abbreviations
- All required OpenAPI fields must be present
- JSON must be properly formatted and parseable
- No additional text, explanations, or markdown code blocks"""

    def _get_cot_section(self) -> str:
        """Generate chain-of-thought section."""
        return """**Chain-of-Thought Process:**
Before providing your final answer, think through your approach:
1. What exactly is being requested?
2. What are the current specification's key characteristics?
3. What changes are needed to fulfill the request?
4. How can I ensure the changes maintain specification integrity?
5. What potential issues should I watch out for?

Work through this reasoning step by step, then provide your final specification."""

    def _get_context_section(self, context: PromptContext) -> str:
        """Generate context awareness section."""
        recent_ops = context.operation_history[-3:]  # Last 3 operations
        return f"""**Context Awareness:**
Recent operations in this session: {' → '.join(recent_ops)}
Specification complexity level: {context.spec_complexity}

Use this context to maintain consistency with previous operations."""

    def _get_specification_analysis(self, request: AIRequest) -> str:
        """Analyze and describe the current specification."""
        try:
            spec_data = json.loads(request.spec_text)

            analysis = ["**Current Specification Analysis:**"]

            # Basic info
            version = spec_data.get("openapi", "unknown")
            title = spec_data.get("info", {}).get("title", "Unknown API")
            analysis.append(f"- API: {title}")
            analysis.append(f"- OpenAPI Version: {version}")

            # Paths analysis
            paths = spec_data.get("paths", {})
            analysis.append(f"- Total Endpoints: {len(paths)}")

            if paths:
                methods = set()
                for path_obj in paths.values():
                    methods.update(path_obj.keys())
                analysis.append(f"- HTTP Methods: {', '.join(sorted(methods)).upper()}")

            # Components analysis
            components = spec_data.get("components", {})
            schemas = components.get("schemas", {})
            if schemas:
                analysis.append(f"- Schema Components: {len(schemas)}")

            security = components.get("securitySchemes", {})
            if security:
                analysis.append(f"- Security Schemes: {len(security)}")

            return "\n".join(analysis)

        except json.JSONDecodeError:
            return "**Current Specification Analysis:**\n- Status: Invalid JSON format detected"
        except Exception:
            return "**Current Specification Analysis:**\n- Status: Analysis failed"

    def _get_task_description(
        self, request: AIRequest, strategy: Dict[str, Any]
    ) -> str:
        """Generate task description section."""
        return f"""**Your Task:**
{request.prompt}

**Operation Type:** {request.operation_type.value.title()}
**Complexity Level:** {strategy["complexity_level"].title()}"""

    def _get_specification_content(self, request: AIRequest) -> str:
        """Format the specification content."""
        return f"""**Current Specification:**
```json
{request.spec_text}
```"""

    def _get_requirements_section(
        self, request: AIRequest, strategy: Dict[str, Any]
    ) -> str:
        """Generate requirements section."""
        requirements = ["**Specific Requirements:**"]

        # Operation-specific requirements
        if request.operation_type == OperationType.MODIFY:
            requirements.append("- Make only the requested modifications")
            requirements.append("- Preserve all unrelated parts of the specification")

        elif request.operation_type == OperationType.GENERATE:
            requirements.append("- Create a complete, production-ready specification")
            requirements.append("- Include comprehensive schemas and examples")

        elif request.operation_type == OperationType.VALIDATE:
            requirements.append("- Identify and fix all validation issues")
            requirements.append("- Provide detailed error explanations")

        # LLM parameter considerations
        if request.llm_parameters.temperature < 0.3:
            requirements.append("- Prioritize accuracy and consistency over creativity")
        elif request.llm_parameters.temperature > 0.7:
            requirements.append("- Feel free to be creative while maintaining validity")

        return "\n".join(requirements)

    def _get_examples_section(self, request: AIRequest) -> str:
        """Generate examples section if needed."""
        if request.operation_type == OperationType.GENERATE:
            return """**Example Patterns to Follow:**
- Use descriptive operationIds (e.g., "getUserById", "createProduct")
- Include comprehensive response schemas with examples
- Add appropriate HTTP status codes (200, 201, 400, 404, 500)
- Use consistent naming conventions (camelCase for properties)
- Include request/response examples where applicable"""

        return ""

    def _get_success_criteria(
        self, request: AIRequest, strategy: Dict[str, Any]
    ) -> str:
        """Define success criteria for the task."""
        criteria = ["**Success Criteria:**"]

        criteria.extend(
            [
                "✓ Valid OpenAPI 3.0+ JSON specification",
                "✓ All requested changes implemented correctly",
                "✓ No broken references or invalid schemas",
                "✓ Consistent with OpenAPI best practices",
            ]
        )

        if request.validate_output:
            criteria.append("✓ Passes OpenAPI specification validation")

        if strategy["complexity_level"] == "complex":
            criteria.append("✓ Handles complex relationships and dependencies")

        return "\n".join(criteria)

    def _load_prompt_templates(self) -> Dict[str, Dict[str, str]]:
        """Load prompt templates for different roles."""
        return {
            PromptTemplate.SYSTEM_ARCHITECT: {
                "role_definition": "You are an expert OpenAPI System Architect with deep knowledge of API design patterns, microservices architecture, and enterprise integration patterns."
            },
            PromptTemplate.CODE_GENERATOR: {
                "role_definition": "You are an expert API Code Generator specializing in creating comprehensive, production-ready OpenAPI specifications from requirements."
            },
            PromptTemplate.VALIDATOR: {
                "role_definition": "You are an OpenAPI Validation Specialist with expertise in specification correctness, schema validation, and compliance checking."
            },
            PromptTemplate.OPTIMIZER: {
                "role_definition": "You are an API Performance Optimizer focused on creating efficient, scalable, and maintainable OpenAPI specifications."
            },
            PromptTemplate.SECURITY_EXPERT: {
                "role_definition": "You are an API Security Expert specializing in secure API design, authentication schemes, and security best practices."
            },
            PromptTemplate.DOMAIN_EXPERT: {
                "role_definition": "You are a Domain Expert with deep knowledge of industry-specific API patterns and business requirements."
            },
        }

    def learn_from_feedback(
        self, prompt_id: str, success: bool, feedback: Optional[str] = None
    ):
        """Learn from user feedback to improve future prompts."""
        if success:
            self._success_patterns.append(
                {
                    "prompt_id": prompt_id,
                    "timestamp": datetime.utcnow(),
                    "feedback": feedback,
                }
            )
        else:
            self._failure_patterns.append(
                {
                    "prompt_id": prompt_id,
                    "timestamp": datetime.utcnow(),
                    "feedback": feedback,
                }
            )

        self.logger.info(f"Learned from feedback - Success: {success}, ID: {prompt_id}")

    def get_prompt_statistics(self) -> Dict[str, Any]:
        """Get statistics about prompt performance."""
        return {
            "total_success_patterns": len(self._success_patterns),
            "total_failure_patterns": len(self._failure_patterns),
            "success_rate": (
                len(self._success_patterns)
                / (len(self._success_patterns) + len(self._failure_patterns))
                if (self._success_patterns or self._failure_patterns)
                else 0
            ),
            "active_contexts": len(self._context_memory),
        }
