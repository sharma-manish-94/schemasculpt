"""
Enhanced Mock Data Generation Service.
Generates realistic, context-aware test data based on OpenAPI schemas.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core.logging import get_logger
from ..schemas.ai_schemas import AIRequest, OperationType

logger = get_logger("mock_data_service")


class MockDataService:
    """
    Service for generating realistic mock data from OpenAPI schemas.
    Uses AI to create contextually appropriate, diverse test data.
    """

    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.logger = logger

        # Domain-specific data patterns
        self.data_patterns = {
            "email": [
                "john.doe@example.com",
                "jane.smith@company.io",
                "admin@test.org",
                "user{}@demo.com",
            ],
            "phone": [
                "+1-555-0{:03d}-{:04d}",
                "(555) {:03d}-{:04d}",
                "555.{:03d}.{:04d}",
            ],
            "name": {
                "first": [
                    "John",
                    "Jane",
                    "Michael",
                    "Sarah",
                    "David",
                    "Emma",
                    "Chris",
                    "Lisa",
                ],
                "last": [
                    "Smith",
                    "Johnson",
                    "Williams",
                    "Brown",
                    "Jones",
                    "Garcia",
                    "Miller",
                    "Davis",
                ],
            },
            "company": [
                "Acme Corp",
                "TechStart Inc",
                "Global Solutions",
                "Innovation Labs",
                "Digital Ventures",
                "Cloud Systems",
                "Data Dynamics",
                "Smart Tech",
            ],
            "address": {
                "street": [
                    "{} {} Street",
                    "{} {} Avenue",
                    "{} {} Road",
                    "{} {} Boulevard",
                ],
                "city": [
                    "New York",
                    "San Francisco",
                    "Chicago",
                    "Boston",
                    "Seattle",
                    "Austin",
                ],
                "state": ["NY", "CA", "IL", "MA", "WA", "TX"],
                "country": ["USA", "United States", "US"],
            },
        }

    async def generate_mock_response(
        self,
        operation_spec: Dict[str, Any],
        response_schema: Dict[str, Any],
        spec_context: Dict[str, Any],
        variation: int = 1,
        use_ai: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a realistic mock response for an OpenAPI operation.

        Args:
            operation_spec: The operation specification
            response_schema: The response schema to conform to
            spec_context: Full OpenAPI spec for context
            variation: Variation number for diverse responses (1-N)
            use_ai: Whether to use AI for generation (fallback to patterns if False)

        Returns:
            Generated mock data conforming to the schema
        """
        self.logger.info(f"Generating mock response (variation {variation})")

        if use_ai:
            try:
                return await self._generate_ai_response(
                    operation_spec, response_schema, spec_context, variation
                )
            except Exception as e:
                self.logger.warning(
                    f"AI generation failed: {e}, falling back to pattern-based"
                )
                return await self._generate_pattern_response(response_schema, variation)
        else:
            return await self._generate_pattern_response(response_schema, variation)

    async def _generate_ai_response(
        self,
        operation_spec: Dict[str, Any],
        response_schema: Dict[str, Any],
        spec_context: Dict[str, Any],
        variation: int,
    ) -> Dict[str, Any]:
        """Generate response using AI for maximum realism."""

        # Extract operation details
        operation_summary = operation_spec.get("summary", "API operation")
        operation_desc = operation_spec.get("description", "")
        tags = operation_spec.get("tags", [])

        # Build context-aware prompt
        prompt = f"""Generate realistic JSON mock data for this API endpoint.

**Operation**: {operation_summary}
**Description**: {operation_desc}
**Tags**: {', '.join(tags) if tags else 'General'}
**Variation**: #{variation}

**Response Schema**:
```json
{json.dumps(response_schema, indent=2)}
```

**Requirements**:
1. Generate realistic, diverse data that looks production-quality
2. Follow the schema constraints exactly (required fields, types, formats, patterns)
3. Use contextually appropriate values based on the operation purpose
4. For arrays, include 2-5 varied items
5. For strings with patterns/formats, respect them (email, date-time, uuid, etc.)
6. Make relationships between fields logical (e.g., if there's a user with email, name should match)
7. Use realistic business data, not placeholder text
8. Return ONLY the raw JSON object, no markdown, no explanations

**Example Good Practices**:
- Email: Use realistic domains and names
- Dates: Use recent, realistic dates
- IDs: Use realistic formats (UUIDs, incremental numbers)
- Names: Use real-sounding names from diverse backgrounds
- Amounts: Use realistic business values
- Status: Use appropriate states for the context
"""

        ai_request = AIRequest(
            spec_text=json.dumps(spec_context, indent=2),
            prompt=prompt,
            operation_type=OperationType.GENERATE,
        )

        result = await self.llm_service.process_ai_request(ai_request)

        # Parse the AI response
        try:
            # Try to extract JSON from the response
            response_text = result.updated_spec_text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = (
                    "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
                )
                if response_text.startswith("json"):
                    response_text = response_text[4:].strip()

            generated_data = json.loads(response_text)

            self.logger.info("Successfully generated AI-powered mock data")
            return generated_data

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse AI response as JSON: {e}")
            raise

    async def _generate_pattern_response(
        self, response_schema: Dict[str, Any], variation: int
    ) -> Dict[str, Any]:
        """
        Generate response using deterministic patterns.
        Fallback when AI is unavailable or disabled.
        """
        self.logger.info("Generating pattern-based mock data")

        return self._generate_from_schema(response_schema, variation)

    def _generate_from_schema(
        self, schema: Dict[str, Any], variation: int, depth: int = 0
    ) -> Any:
        """
        Recursively generate data from a JSON schema.

        Args:
            schema: JSON Schema object
            variation: Variation number for diversity
            depth: Current recursion depth (prevents infinite loops)
        """
        # Prevent infinite recursion
        if depth > 10:
            return None

        # Handle $ref references
        if "$ref" in schema:
            # For now, return a placeholder - in production, resolve refs
            return {"$ref": schema["$ref"]}

        schema_type = schema.get("type", "object")

        # Handle different schema types
        if schema_type == "object":
            return self._generate_object(schema, variation, depth)
        elif schema_type == "array":
            return self._generate_array(schema, variation, depth)
        elif schema_type == "string":
            return self._generate_string(schema, variation)
        elif schema_type == "integer":
            return self._generate_integer(schema, variation)
        elif schema_type == "number":
            return self._generate_number(schema, variation)
        elif schema_type == "boolean":
            return variation % 2 == 0
        elif schema_type == "null":
            return None
        else:
            return None

    def _generate_object(
        self, schema: Dict[str, Any], variation: int, depth: int
    ) -> Dict[str, Any]:
        """Generate an object from schema."""
        result = {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for prop_name, prop_schema in properties.items():
            # Generate required fields and some optional ones
            if prop_name in required or random.random() > 0.3:
                result[prop_name] = self._generate_from_schema(
                    prop_schema, variation, depth + 1
                )

        return result

    def _generate_array(
        self, schema: Dict[str, Any], variation: int, depth: int
    ) -> List[Any]:
        """Generate an array from schema."""
        items_schema = schema.get("items", {})
        min_items = schema.get("minItems", 2)
        max_items = schema.get("maxItems", 5)

        # Generate 2-5 items with some variation
        count = min(max_items, max(min_items, 2 + (variation % 4)))

        return [
            self._generate_from_schema(items_schema, variation + i, depth + 1)
            for i in range(count)
        ]

    def _generate_string(self, schema: Dict[str, Any], variation: int) -> str:
        """Generate a string value based on format and pattern."""
        format_type = schema.get("format")
        pattern = schema.get("pattern")
        enum_values = schema.get("enum")

        # Handle enum
        if enum_values:
            return enum_values[variation % len(enum_values)]

        # Handle specific formats
        if format_type == "email":
            names = self.data_patterns["name"]["first"]
            name = names[variation % len(names)].lower()
            domains = ["example.com", "test.io", "demo.org", "company.com"]
            return f"{name}.user{variation}@{domains[variation % len(domains)]}"

        elif format_type == "date-time":
            base_date = datetime.now() - timedelta(days=variation * 7)
            return base_date.isoformat() + "Z"

        elif format_type == "date":
            base_date = datetime.now() - timedelta(days=variation * 7)
            return base_date.strftime("%Y-%m-%d")

        elif format_type == "uuid":
            import uuid

            # Generate deterministic UUID based on variation
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"test-{variation}"))

        elif format_type == "uri" or format_type == "url":
            return f"https://api.example.com/resource/{variation}"

        # Handle patterns (simplified)
        if pattern:
            # For now, return a pattern indicator
            return f"matches-pattern-{variation}"

        # Check field name for hints
        field_name = schema.get("title", "").lower()

        if "email" in field_name:
            return self._generate_string({"format": "email"}, variation)
        elif "phone" in field_name:
            return f"+1-555-0{(100 + variation):03d}-{(1000 + variation):04d}"
        elif "name" in field_name:
            first_names = self.data_patterns["name"]["first"]
            last_names = self.data_patterns["name"]["last"]
            return f"{first_names[variation % len(first_names)]} {last_names[variation % len(last_names)]}"
        elif "company" in field_name or "organization" in field_name:
            companies = self.data_patterns["company"]
            return companies[variation % len(companies)]
        elif "city" in field_name:
            cities = self.data_patterns["address"]["city"]
            return cities[variation % len(cities)]
        elif "country" in field_name:
            return "United States"
        elif "description" in field_name or "text" in field_name:
            return f"This is a sample {field_name} for testing purposes (variation {variation})"
        elif "id" in field_name:
            return f"id-{1000 + variation}"
        elif "status" in field_name:
            statuses = ["active", "pending", "completed", "cancelled"]
            return statuses[variation % len(statuses)]

        # Default string
        min_length = schema.get("minLength", 5)
        max_length = schema.get("maxLength", 50)
        target_length = min(max_length, max(min_length, 20))

        return f"sample-string-{variation}".ljust(target_length, "-")[:target_length]

    def _generate_integer(self, schema: Dict[str, Any], variation: int) -> int:
        """Generate an integer value."""
        minimum = schema.get("minimum", 0)
        maximum = schema.get("maximum", 1000)
        multiple_of = schema.get("multipleOf")

        value = minimum + (variation * 7) % (maximum - minimum + 1)

        if multiple_of:
            value = (value // multiple_of) * multiple_of

        return value

    def _generate_number(self, schema: Dict[str, Any], variation: int) -> float:
        """Generate a number (float) value."""
        minimum = schema.get("minimum", 0.0)
        maximum = schema.get("maximum", 1000.0)

        range_size = maximum - minimum
        value = minimum + (variation * 7.3) % range_size

        return round(value, 2)

    async def generate_test_variations(
        self,
        operation_spec: Dict[str, Any],
        response_schema: Dict[str, Any],
        spec_context: Dict[str, Any],
        count: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple variations of mock data for testing.

        Args:
            operation_spec: The operation specification
            response_schema: The response schema
            spec_context: Full OpenAPI spec
            count: Number of variations to generate

        Returns:
            List of generated mock responses
        """
        variations = []

        for i in range(1, count + 1):
            try:
                data = await self.generate_mock_response(
                    operation_spec,
                    response_schema,
                    spec_context,
                    variation=i,
                    use_ai=(i == 1),  # Use AI for first variation, patterns for rest
                )
                variations.append(data)
            except Exception as e:
                self.logger.error(f"Failed to generate variation {i}: {e}")
                # Continue with other variations

        return variations
