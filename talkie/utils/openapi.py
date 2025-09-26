"""Module for OpenAPI specification handling."""

import json
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urljoin


class OpenAPIClient:
    """Client for working with OpenAPI specifications."""

    def __init__(self, spec: Union[str, Dict[str, Any]]):
        """Initialize OpenAPI client.

        Args:
            spec: OpenAPI specification (URL, file path, or dict)
        """
        if isinstance(spec, str):
            # Load from URL or file
            self.spec = self._load_spec(spec)
        else:
            self.spec = spec

        self.base_url = self._get_base_url()
        self.paths = self.spec.get("paths", {})
        self.operations = self._extract_operations()

    def _load_spec(self, spec_source: str) -> Dict[str, Any]:
        """Load OpenAPI specification from source.

        Args:
            spec_source: URL or file path to spec

        Returns:
            Dict[str, Any]: Parsed specification
        """
        # In a real implementation, this would load from URL or file
        # For now, return a mock specification
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "API",
                "version": "1.0.0"
            },
            "servers": [
                {"url": "https://api.example.com"}
            ],
            "paths": {}
        }

    def _get_base_url(self) -> str:
        """Get base URL from specification.

        Returns:
            str: Base URL
        """
        servers = self.spec.get("servers", [])
        if servers:
            return servers[0].get("url", "")
        return ""

    def _extract_operations(self) -> List[Dict[str, Any]]:
        """Extract all operations from specification.

        Returns:
            List[Dict[str, Any]]: List of operations
        """
        operations = []

        for path, path_item in self.paths.items():
            for method, operation in path_item.items():
                http_methods = [
                    "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"
                ]
                if method.upper() in http_methods:
                    operations.append({
                        "path": path,
                        "method": method.upper(),
                        "operation": operation
                    })

        return operations

    def get_operation(self, path: str, method: str) -> Optional[Dict[str, Any]]:
        """Get specific operation.

        Args:
            path: API path
            method: HTTP method

        Returns:
            Optional[Dict[str, Any]]: Operation details
        """
        path_item = self.paths.get(path)
        if path_item:
            return path_item.get(method.lower())
        return None

    def get_operations_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get operations by tag.

        Args:
            tag: Tag name

        Returns:
            List[Dict[str, Any]]: Operations with tag
        """
        tagged_operations = []

        for operation in self.operations:
            op_tags = operation.get("operation", {}).get("tags", [])
            if tag in op_tags:
                tagged_operations.append(operation)

        return tagged_operations

    def generate_request_example(
        self,
        path: str,
        method: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate request example for operation.

        Args:
            path: API path
            method: HTTP method
            parameters: Request parameters

        Returns:
            Dict[str, Any]: Request example
        """
        operation = self.get_operation(path, method)
        if not operation:
            return {}

        example = {
            "method": method.upper(),
            "url": urljoin(self.base_url, path),
            "headers": {
                "Content-Type": "application/json"
            }
        }

        # Add parameters
        if parameters:
            if method.upper() in ["GET", "DELETE"]:
                # Add as query parameters
                example["params"] = parameters
            else:
                # Add as request body
                example["data"] = parameters

        return example

    def validate_request(
        self,
        path: str,
        method: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Validate request against specification.

        Args:
            path: API path
            method: HTTP method
            parameters: Request parameters

        Returns:
            List[str]: Validation errors
        """
        errors = []
        operation = self.get_operation(path, method)

        if not operation:
            errors.append(f"Operation {method.upper()} {path} not found")
            return errors

        # Check required parameters
        required_params = operation.get("parameters", [])
        for param in required_params:
            if param.get("required", False):
                param_name = param.get("name")
                if param_name and (not parameters or param_name not in parameters):
                    errors.append(f"Required parameter '{param_name}' missing")

        return errors

    def get_schema(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """Get schema definition.

        Args:
            schema_name: Schema name

        Returns:
            Optional[Dict[str, Any]]: Schema definition
        """
        schemas = self.spec.get("components", {}).get("schemas", {})
        return schemas.get(schema_name)

    def get_endpoints(self) -> List[str]:
        """Get all available endpoints.

        Returns:
            List[str]: List of endpoint paths
        """
        return list(self.paths.keys())

    def get_methods_for_path(self, path: str) -> List[str]:
        """Get available methods for path.

        Args:
            path: API path

        Returns:
            List[str]: Available HTTP methods
        """
        path_item = self.paths.get(path, {})
        methods = []

        for method in ["get", "post", "put", "delete", "patch", "head", "options"]:
            if method in path_item:
                methods.append(method.upper())

        return methods

    def export_spec(self, output_file: str) -> None:
        """Export specification to file.

        Args:
            output_file: Output file path
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.spec, f, indent=2, ensure_ascii=False)

    def get_info(self) -> Dict[str, Any]:
        """Get API information.

        Returns:
            Dict[str, Any]: API info
        """
        return self.spec.get("info", {})

    def get_servers(self) -> List[Dict[str, str]]:
        """Get server information.

        Returns:
            List[Dict[str, str]]: Server list
        """
        return self.spec.get("servers", [])


def load_openapi_spec(spec_source: str) -> OpenAPIClient:
    """Load OpenAPI specification.

    Args:
        spec_source: URL or file path to specification

    Returns:
        OpenAPIClient: OpenAPI client instance
    """
    return OpenAPIClient(spec_source)


def validate_openapi_spec(spec: Dict[str, Any]) -> List[str]:
    """Validate OpenAPI specification.

    Args:
        spec: OpenAPI specification

    Returns:
        List[str]: Validation errors
    """
    errors = []

    # Check required fields
    if "openapi" not in spec:
        errors.append("Missing 'openapi' field")

    if "info" not in spec:
        errors.append("Missing 'info' field")
    else:
        info = spec["info"]
        if "title" not in info:
            errors.append("Missing 'info.title' field")
        if "version" not in info:
            errors.append("Missing 'info.version' field")

    if "paths" not in spec:
        errors.append("Missing 'paths' field")

    return errors


def generate_client_code(spec: Dict[str, Any], language: str = "python") -> str:
    """Generate client code from specification.

    Args:
        spec: OpenAPI specification
        language: Target language

    Returns:
        str: Generated client code
    """
    if language == "python":
        return _generate_python_client(spec)
    return f"Client generation for {language} not implemented"


def _generate_python_client(spec: Dict[str, Any]) -> str:
    """Generate Python client code.

    Args:
        spec: OpenAPI specification

    Returns:
        str: Python client code
    """
    client_code = [
        "import requests",
        "from typing import Dict, Any, Optional",
        "",
        "class APIClient:",
        "    def __init__(self, base_url: str):",
        "        self.base_url = base_url",
        "        self.session = requests.Session()",
        "",
        "    def request(self, method: str, path: str, **kwargs):",
        "        url = self.base_url + path",
        "        return self.session.request(method, url, **kwargs)",
        ""
    ]

    # Add methods for each operation
    paths = spec.get("paths", {})
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                operation_id = operation.get(
                    "operationId", f"{method}_{path.replace('/', '_')}"
                )
                client_code.append(
                    f"    def {operation_id}(self, **kwargs):"
                )
                request_line = (
                    f"        return self.request('{method.upper()}', "
                    f"'{path}', **kwargs)"
                )
                client_code.append(request_line)
                client_code.append("")

    return "\n".join(client_code)
