"""
Prance-based OpenAPI Spec Validator.

Provides an implementation of ISpecValidator using prance and openapi-spec-validator.
Runs blocking validation operations in a thread pool to avoid blocking the event loop.
"""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any, Dict, List, Optional

from app.domain.interfaces.spec_validator import ISpecValidator
from app.domain.models.value_objects import ValidationError, ValidationResult

logger = logging.getLogger(__name__)

# Thread pool for running blocking operations
_executor = ThreadPoolExecutor(max_workers=4)


class PranceSpecValidator(ISpecValidator):
    """
    Prance-based implementation of ISpecValidator.

    Features:
    - JSON and YAML format support
    - Basic structure validation
    - Schema reference validation
    - Comprehensive validation via prance
    - Thread pool execution for non-blocking async

    Usage:
        validator = PranceSpecValidator()
        result = await validator.validate(spec_text)
        if result.is_valid:
            spec = await validator.parse(spec_text)
    """

    def __init__(self):
        """Initialize the validator."""
        self._prance_available = self._check_prance_available()

    def _check_prance_available(self) -> bool:
        """Check if prance is available."""
        try:
            import prance  # noqa: F401

            return True
        except ImportError:
            logger.warning("prance not installed. Advanced validation unavailable.")
            return False

    def detect_format(self, spec_text: str) -> str:
        """Detect the format of a specification (JSON or YAML)."""
        stripped = spec_text.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            return "json"
        return "yaml"

    def _parse_spec_sync(self, spec_text: str) -> Dict[str, Any]:
        """Parse spec synchronously (runs in thread pool)."""
        format_type = self.detect_format(spec_text)

        if format_type == "json":
            return json.loads(spec_text)
        else:
            import yaml

            return yaml.safe_load(spec_text)

    def _validate_basic_structure(
        self, spec_data: Dict[str, Any]
    ) -> tuple[List[ValidationError], List[ValidationError]]:
        """Validate basic OpenAPI structure."""
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []

        # Required fields
        required_fields = ["openapi", "info", "paths"]
        for field in required_fields:
            if field not in spec_data:
                errors.append(
                    ValidationError(
                        message=f"Missing required field: {field}",
                        path=f"/{field}",
                        severity="error",
                    )
                )

        # Version validation
        if "openapi" in spec_data:
            version = spec_data["openapi"]
            if not isinstance(version, str):
                errors.append(
                    ValidationError(
                        message="openapi version must be a string",
                        path="/openapi",
                        severity="error",
                    )
                )
            elif not version.startswith("3."):
                warnings.append(
                    ValidationError(
                        message=f"OpenAPI version {version} is not 3.x",
                        path="/openapi",
                        severity="warning",
                    )
                )

        # Info validation
        if "info" in spec_data:
            info = spec_data["info"]
            if isinstance(info, dict):
                if "title" not in info:
                    errors.append(
                        ValidationError(
                            message="Missing required field: info.title",
                            path="/info/title",
                            severity="error",
                        )
                    )
                if "version" not in info:
                    errors.append(
                        ValidationError(
                            message="Missing required field: info.version",
                            path="/info/version",
                            severity="error",
                        )
                    )

        return errors, warnings

    def _validate_paths(
        self, spec_data: Dict[str, Any]
    ) -> tuple[List[ValidationError], List[ValidationError]]:
        """Validate paths section."""
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []

        paths = spec_data.get("paths", {})
        if not paths:
            return errors, warnings

        valid_methods = {
            "get",
            "post",
            "put",
            "delete",
            "options",
            "head",
            "patch",
            "trace",
        }
        path_level_fields = {"summary", "description", "parameters", "servers"}

        for path, path_obj in paths.items():
            if not path.startswith("/"):
                errors.append(
                    ValidationError(
                        message="Path must start with /",
                        path=f"/paths/{path}",
                        severity="error",
                    )
                )

            if not isinstance(path_obj, dict):
                errors.append(
                    ValidationError(
                        message="Path item must be an object",
                        path=f"/paths/{path}",
                        severity="error",
                    )
                )
                continue

            for method, operation in path_obj.items():
                if method.startswith("x-"):
                    continue  # Extension field

                if method in valid_methods:
                    if not isinstance(operation, dict):
                        errors.append(
                            ValidationError(
                                message="Operation must be an object",
                                path=f"/paths/{path}/{method}",
                                severity="error",
                            )
                        )
                    elif "responses" not in operation:
                        errors.append(
                            ValidationError(
                                message="Operation missing required 'responses' field",
                                path=f"/paths/{path}/{method}",
                                severity="error",
                            )
                        )
                elif method not in path_level_fields and method != "$ref":
                    warnings.append(
                        ValidationError(
                            message=f"Unknown field '{method}' at path level",
                            path=f"/paths/{path}",
                            severity="warning",
                        )
                    )

        return errors, warnings

    def _validate_refs(
        self, spec_data: Dict[str, Any]
    ) -> tuple[List[ValidationError], List[ValidationError]]:
        """Validate $ref references."""
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []

        refs = self._find_all_refs(spec_data)
        components_schemas = spec_data.get("components", {}).get("schemas", {})

        for ref, path in refs:
            if ref.startswith("#/components/schemas/"):
                schema_name = ref.replace("#/components/schemas/", "")
                if schema_name not in components_schemas:
                    errors.append(
                        ValidationError(
                            message=f"Reference points to non-existent schema: {schema_name}",
                            path=path,
                            severity="error",
                        )
                    )

        return errors, warnings

    def _find_all_refs(
        self, obj: Any, path: str = "", refs: Optional[List[tuple]] = None
    ) -> List[tuple]:
        """Find all $ref values in the spec."""
        if refs is None:
            refs = []

        if isinstance(obj, dict):
            if "$ref" in obj:
                refs.append((obj["$ref"], path))
            for key, value in obj.items():
                self._find_all_refs(value, f"{path}/{key}", refs)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                self._find_all_refs(item, f"{path}/{i}", refs)

        return refs

    def _validate_with_prance_sync(
        self, spec_data: Dict[str, Any]
    ) -> tuple[List[ValidationError], List[ValidationError]]:
        """Run prance validation synchronously."""
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []

        if not self._prance_available:
            warnings.append(
                ValidationError(
                    message="Advanced validation unavailable (prance not installed)",
                    severity="warning",
                )
            )
            return errors, warnings

        try:
            from prance import ResolvingParser

            # This will raise an exception if the spec is invalid
            ResolvingParser(spec_dict=spec_data)
        except Exception as e:
            warnings.append(
                ValidationError(
                    message=f"Prance validation warning: {str(e)}",
                    severity="warning",
                )
            )

        return errors, warnings

    def _validate_sync(self, spec_text: str, strict: bool) -> ValidationResult:
        """Run full validation synchronously."""
        all_errors: List[ValidationError] = []
        all_warnings: List[ValidationError] = []

        try:
            # Parse spec
            spec_data = self._parse_spec_sync(spec_text)

            # Basic structure validation
            errors, warnings = self._validate_basic_structure(spec_data)
            all_errors.extend(errors)
            all_warnings.extend(warnings)

            # Path validation
            errors, warnings = self._validate_paths(spec_data)
            all_errors.extend(errors)
            all_warnings.extend(warnings)

            # Reference validation
            errors, warnings = self._validate_refs(spec_data)
            all_errors.extend(errors)
            all_warnings.extend(warnings)

            # Prance validation
            errors, warnings = self._validate_with_prance_sync(spec_data)
            all_errors.extend(errors)
            all_warnings.extend(warnings)

            # Detect spec version
            spec_version = spec_data.get("openapi", "unknown")

        except json.JSONDecodeError as e:
            all_errors.append(
                ValidationError(
                    message=f"Invalid JSON: {str(e)}",
                    line=e.lineno if hasattr(e, "lineno") else None,
                    column=e.colno if hasattr(e, "colno") else None,
                    severity="error",
                )
            )
            spec_version = None
        except Exception as e:
            all_errors.append(
                ValidationError(
                    message=f"Validation error: {str(e)}",
                    severity="error",
                )
            )
            spec_version = None

        # If strict mode, treat warnings as errors
        if strict:
            all_errors.extend(all_warnings)
            all_warnings = []

        is_valid = len(all_errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=all_errors,
            warnings=all_warnings,
            spec_version=spec_version,
        )

    async def validate(
        self,
        spec_text: str,
        strict: bool = False,
    ) -> ValidationResult:
        """Validate an OpenAPI specification."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, partial(self._validate_sync, spec_text, strict)
        )

    async def parse(
        self,
        spec_text: str,
        resolve_refs: bool = True,
    ) -> Dict[str, Any]:
        """Parse an OpenAPI specification into a dictionary."""
        loop = asyncio.get_event_loop()

        def parse_with_refs():
            spec_data = self._parse_spec_sync(spec_text)

            if resolve_refs and self._prance_available:
                try:
                    from prance import ResolvingParser

                    parser = ResolvingParser(spec_dict=spec_data)
                    return parser.specification
                except Exception:
                    pass

            return spec_data

        return await loop.run_in_executor(_executor, parse_with_refs)

    async def get_endpoints(
        self,
        spec_text: str,
    ) -> List[Dict[str, Any]]:
        """Extract all endpoints from an OpenAPI specification."""

        def extract_endpoints():
            spec_data = self._parse_spec_sync(spec_text)
            endpoints = []

            paths = spec_data.get("paths", {})
            valid_methods = {
                "get",
                "post",
                "put",
                "delete",
                "options",
                "head",
                "patch",
                "trace",
            }

            for path, path_obj in paths.items():
                if not isinstance(path_obj, dict):
                    continue

                for method, operation in path_obj.items():
                    if method not in valid_methods:
                        continue

                    if not isinstance(operation, dict):
                        continue

                    endpoints.append(
                        {
                            "path": path,
                            "method": method.upper(),
                            "operationId": operation.get("operationId"),
                            "summary": operation.get("summary"),
                            "description": operation.get("description"),
                            "tags": operation.get("tags", []),
                            "parameters": operation.get("parameters", []),
                            "requestBody": operation.get("requestBody"),
                            "responses": operation.get("responses", {}),
                            "security": operation.get("security"),
                        }
                    )

            return endpoints

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, extract_endpoints)

    async def get_schemas(
        self,
        spec_text: str,
    ) -> Dict[str, Any]:
        """Extract all schemas from an OpenAPI specification."""

        def extract_schemas():
            spec_data = self._parse_spec_sync(spec_text)
            return spec_data.get("components", {}).get("schemas", {})

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, extract_schemas)

    async def get_security_schemes(
        self,
        spec_text: str,
    ) -> Dict[str, Any]:
        """Extract security schemes from an OpenAPI specification."""

        def extract_security():
            spec_data = self._parse_spec_sync(spec_text)
            return spec_data.get("components", {}).get("securitySchemes", {})

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, extract_security)
