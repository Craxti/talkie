"""OpenAPI client code generator for Talkie."""

from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass
from .openapi import OpenAPIClient


@dataclass
class GeneratedMethod:
    """Represents a generated API method."""
    name: str
    path: str
    method: str
    description: str
    parameters: List[Dict[str, Any]]
    request_body: Optional[Dict[str, Any]]
    responses: Dict[str, Any]
    python_code: str


class OpenApiClientGenerator:
    """Generator for Python client code from OpenAPI specifications."""

    def __init__(self, spec_url: str, class_name: str = "ApiClient"):
        """
        Initialize the generator.

        Args:
            spec_url: URL or path to OpenAPI specification
            class_name: Name of the generated client class
        """
        self.spec_url = spec_url
        self.class_name = class_name
        self.inspector = OpenAPIClient(spec_url)
        self.spec = None
        self.generated_methods: List[GeneratedMethod] = []

    def load_specification(self) -> None:
        """Load OpenAPI specification."""
        self.spec = self.inspector.load_spec(self.spec_url)

    def generate_client(self, output_dir: str = "generated_client") -> str:
        """
        Generate complete Python client code.

        Args:
            output_dir: Output directory for generated files

        Returns:
            Path to the main client file
        """
        if not self.spec:
            self.load_specification()

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate methods for each endpoint
        self._generate_methods()

        # Generate main client file
        client_code = self._generate_client_class()
        client_file = output_path / f"{self.class_name.lower()}.py"

        with open(client_file, 'w', encoding='utf-8') as f:
            f.write(client_code)

        # Generate models file
        models_code = self._generate_models()
        models_file = output_path / "models.py"

        with open(models_file, 'w', encoding='utf-8') as f:
            f.write(models_code)

        # Generate __init__.py
        init_code = self._generate_init_file()
        init_file = output_path / "__init__.py"

        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(init_code)

        # Generate README
        readme_code = self._generate_readme()
        readme_file = output_path / "README.md"

        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_code)

        return str(client_file)

    def _generate_methods(self) -> None:
        """Generate methods for all API endpoints."""
        paths = self.spec.get("paths", {})

        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.lower() in ["get", "post", "put", "delete", "patch", "options", "head"]:
                    generated_method = self._generate_method(path, method, operation)
                    self.generated_methods.append(generated_method)

    def _generate_method(self, path: str, method: str, operation: Dict[str, Any]) -> GeneratedMethod:
        """Generate a single API method."""
        # Create method name
        operation_id = operation.get("operationId")
        if operation_id:
            method_name = self._to_snake_case(operation_id)
        else:
            # Generate method name from path and method
            path_parts = [part for part in path.split("/") if part and not part.startswith("{")]
            method_name = f"{method.lower()}_{'_'.join(path_parts)}"

        # Clean method name
        method_name = self._sanitize_method_name(method_name)

        # Get description
        description = operation.get("description", operation.get("summary", f"{method.upper()} {path}"))

        # Get parameters
        parameters = operation.get("parameters", [])

        # Get request body
        request_body = operation.get("requestBody")

        # Get responses
        responses = operation.get("responses", {})

        # Generate Python code for the method
        python_code = self._generate_method_code(
            method_name, path, method, description, parameters, request_body, responses
        )

        return GeneratedMethod(
            name=method_name,
            path=path,
            method=method,
            description=description,
            parameters=parameters,
            request_body=request_body,
            responses=responses,
            python_code=python_code
        )

    def _generate_method_code(
        self,
        method_name: str,
        path: str,
        method: str,
        description: str,
        parameters: List[Dict[str, Any]],
        request_body: Optional[Dict[str, Any]],
        responses: Dict[str, Any]
    ) -> str:
        """Generate Python code for a single method."""
        # Collect path parameters
        path_params = [p for p in parameters if p.get("in") == "path"]
        query_params = [p for p in parameters if p.get("in") == "query"]
        header_params = [p for p in parameters if p.get("in") == "header"]

        # Build method signature
        args = []

        # Add required path parameters first
        for param in path_params:
            if param.get("required", False):
                param_name = self._to_snake_case(param["name"])
                param_type = self._get_python_type(param.get("schema", {}))
                args.append(f"{param_name}: {param_type}")

        # Add optional parameters
        optional_args = []

        # Query parameters
        for param in query_params:
            param_name = self._to_snake_case(param["name"])
            param_type = self._get_python_type(param.get("schema", {}))
            default = "None" if not param.get("required", False) else ""
            if default:
                optional_args.append(f"{param_name}: Optional[{param_type}] = {default}")
            else:
                args.append(f"{param_name}: {param_type}")

        # Header parameters (optional)
        for param in header_params:
            param_name = self._to_snake_case(param["name"])
            param_type = self._get_python_type(param.get("schema", {}))
            optional_args.append(f"{param_name}: Optional[{param_type}] = None")

        # Request body
        if request_body:
            content_types = request_body.get("content", {})
            if "application/json" in content_types:
                optional_args.append("json_data: Optional[Dict[str, Any]] = None")
            elif "application/x-www-form-urlencoded" in content_types:
                optional_args.append("form_data: Optional[Dict[str, Any]] = None")
            else:
                optional_args.append("data: Optional[Any] = None")

        # Combine all arguments
        all_args = args + optional_args
        signature = f"def {method_name}(self, {', '.join(all_args)}) -> Any:"

        # Build method body
        body_lines = [
            f'        """',
            f'        {description}',
            f'        ',
            f'        Args:'
        ]

        # Add parameter documentation
        for param in path_params + query_params + header_params:
            param_name = self._to_snake_case(param["name"])
            param_desc = param.get("description", "")
            required = " (required)" if param.get("required", False) else " (optional)"
            body_lines.append(f'            {param_name}: {param_desc}{required}')

        if request_body:
            body_lines.append(f'            data: Request body data')

        body_lines.extend([
            f'        ',
            f'        Returns:',
            f'            Response data',
            f'        """',
            f'        # Build URL',
            f'        url = f"{path}"'
        ])

        # Replace path parameters
        for param in path_params:
            param_name = self._to_snake_case(param["name"])
            original_name = param["name"]
            body_lines.append(f'        url = url.replace("{{{original_name}}}", str({param_name}))')

        # Build query parameters
        if query_params:
            body_lines.append('        params = {}')
            for param in query_params:
                param_name = self._to_snake_case(param["name"])
                original_name = param["name"]
                body_lines.append(f'        if {param_name} is not None:')
                body_lines.append(f'            params["{original_name}"] = {param_name}')
        else:
            body_lines.append('        params = None')

        # Build headers
        if header_params:
            body_lines.append('        headers = {}')
            for param in header_params:
                param_name = self._to_snake_case(param["name"])
                original_name = param["name"]
                body_lines.append(f'        if {param_name} is not None:')
                body_lines.append(f'            headers["{original_name}"] = {param_name}')
        else:
            body_lines.append('        headers = None')

        # Build request call
        request_args = [
            f'"{method.upper()}"',
            'url',
            'params=params',
            'headers=headers'
        ]

        if request_body:
            content_types = request_body.get("content", {})
            if "application/json" in content_types:
                request_args.append('json=json_data')
            elif "application/x-www-form-urlencoded" in content_types:
                request_args.append('data=form_data')
            else:
                request_args.append('data=data')

        body_lines.extend([
            f'        ',
            f'        return self.client.request(',
            f'            {", ".join(request_args)}',
            f'        )'
        ])

        return signature + '\n' + '\n'.join(body_lines)

    def _generate_client_class(self) -> str:
        """Generate the main client class code."""
        methods_code = '\n\n    '.join([method.python_code for method in self.generated_methods])

        return f'''"""
Generated API client for {self.spec.get("info", {}).get("title", "API")}.

This file was automatically generated from OpenAPI specification.
Do not edit manually - regenerate using Talkie OpenAPI generator.
"""

from typing import Any, Dict, List, Optional, Union
from talkie.core.client import HttpClient
from .models import *


class {self.class_name}:
    """
    {self.spec.get("info", {}).get("description", f"Generated client for {self.spec.get('info', {}).get('title', 'API')}")}

    Version: {self.spec.get("info", {}).get("version", "1.0.0")}
    """

    def __init__(self, base_url: str = None, **kwargs):
        """
        Initialize the API client.

        Args:
            base_url: Base URL for the API
            **kwargs: Additional arguments passed to HttpClient
        """
        self.base_url = base_url or "{self._get_base_url()}"
        self.client = HttpClient(**kwargs)

    def request(self, method: str, url: str, **kwargs) -> Any:
        """
        Make a direct HTTP request.

        Args:
            method: HTTP method
            url: Relative or absolute URL
            **kwargs: Additional request parameters

        Returns:
            Response data
        """
        if not url.startswith("http"):
            url = f"{{self.base_url.rstrip('/')}}/{{url.lstrip('/')}}"

        response = self.client.request(method, url, **kwargs)
        return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text

    {methods_code}
'''

    def _generate_models(self) -> str:
        """Generate data models from OpenAPI schemas."""
        models_code = [
            '"""',
            'Data models for the generated API client.',
            '',
            'This file was automatically generated from OpenAPI specification.',
            'Do not edit manually - regenerate using Talkie OpenAPI generator.',
            '"""',
            '',
            'from typing import Any, Dict, List, Optional, Union',
            'from pydantic import BaseModel, Field',
            '',
            ''
        ]

        # Extract schemas from components
        components = self.spec.get("components", {})
        schemas = components.get("schemas", {})

        if schemas:
            for schema_name, schema_def in schemas.items():
                model_code = self._generate_model_class(schema_name, schema_def)
                models_code.append(model_code)
                models_code.append('')
        else:
            models_code.extend([
                '# No schemas found in OpenAPI specification',
                '# Add your custom models here if needed',
                '',
                'class BaseResponse(BaseModel):',
                '    """Base response model."""',
                '    pass',
                ''
            ])

        return '\n'.join(models_code)

    def _generate_model_class(self, class_name: str, schema: Dict[str, Any]) -> str:
        """Generate a Pydantic model class from OpenAPI schema."""
        class_name = self._to_pascal_case(class_name)
        description = schema.get("description", f"{class_name} model")

        properties = schema.get("properties", {})
        required_fields = set(schema.get("required", []))

        lines = [
            f'class {class_name}(BaseModel):',
            f'    """',
            f'    {description}',
            f'    """'
        ]

        if not properties:
            lines.append('    pass')
        else:
            for prop_name, prop_schema in properties.items():
                field_name = self._to_snake_case(prop_name)
                field_type = self._get_python_type(prop_schema)
                field_desc = prop_schema.get("description", "")

                if prop_name not in required_fields:
                    field_type = f"Optional[{field_type}]"
                    default = " = None"
                else:
                    default = ""

                if field_desc:
                    lines.append(f'    {field_name}: {field_type}{default}  # {field_desc}')
                else:
                    lines.append(f'    {field_name}: {field_type}{default}')

        return '\n'.join(lines)

    def _generate_init_file(self) -> str:
        """Generate __init__.py file."""
        return f'''"""
Generated API client package.

This package was automatically generated from OpenAPI specification.
"""

from .{self.class_name.lower()} import {self.class_name}
from .models import *

__version__ = "{self.spec.get("info", {}).get("version", "1.0.0")}"
__all__ = ["{self.class_name}"]
'''

    def _generate_readme(self) -> str:
        """Generate README.md file."""
        api_info = self.spec.get("info", {})
        title = api_info.get("title", "API")
        description = api_info.get("description", "Generated API client")
        version = api_info.get("version", "1.0.0")

        return f'''# {title} Client

{description}

**Version:** {version}

## Installation

This client was generated using Talkie OpenAPI generator.

## Usage

```python
from {self.class_name.lower()} import {self.class_name}

# Initialize client
client = {self.class_name}(base_url="https://api.example.com")

# Use generated methods
# Example: client.get_users()
```

## Generated Methods

This client includes the following generated methods:

{self._generate_methods_documentation()}

## Customization

You can extend the generated client by inheriting from `{self.class_name}`:

```python
class Custom{self.class_name}({self.class_name}):
    def custom_method(self):
        # Your custom logic here
        pass
```

## Regeneration

To regenerate this client from updated OpenAPI specification:

```bash
talkie generate-client {self.spec_url} --output ./generated_client
```
'''

    def _generate_methods_documentation(self) -> str:
        """Generate documentation for all methods."""
        docs = []
        for method in self.generated_methods:
            docs.append(f"- `{method.name}()` - {method.description}")
        return '\n'.join(docs)

    def _get_base_url(self) -> str:
        """Extract base URL from OpenAPI spec."""
        servers = self.spec.get("servers", [])
        if servers:
            return servers[0].get("url", "https://api.example.com")
        return "https://api.example.com"

    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case."""
        import re
        # Replace special characters with underscores
        text = re.sub(r'[^a-zA-Z0-9]', '_', text)
        # Convert camelCase to snake_case
        text = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', text)
        return text.lower().strip('_')

    def _to_pascal_case(self, text: str) -> str:
        """Convert text to PascalCase."""
        import re
        # Split by non-alphanumeric characters
        words = re.split(r'[^a-zA-Z0-9]', text)
        return ''.join(word.capitalize() for word in words if word)

    def _sanitize_method_name(self, name: str) -> str:
        """Sanitize method name to be valid Python identifier."""
        import keyword
        import re

        # Remove invalid characters
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)

        # Ensure it doesn't start with a number
        if name and name[0].isdigit():
            name = f"_{name}"

        # Avoid Python keywords
        if keyword.iskeyword(name):
            name = f"{name}_"

        return name or "unknown_method"

    def _get_python_type(self, schema: Dict[str, Any]) -> str:
        """Convert OpenAPI schema type to Python type hint."""
        schema_type = schema.get("type", "string")
        schema_format = schema.get("format")

        type_mapping = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "array": "List[Any]",
            "object": "Dict[str, Any]"
        }

        # Handle specific formats
        if schema_type == "string":
            if schema_format == "date":
                return "str"  # Could be datetime.date with proper imports
            elif schema_format == "date-time":
                return "str"  # Could be datetime.datetime with proper imports
            elif schema_format == "binary":
                return "bytes"

        # Handle arrays with item types
        if schema_type == "array":
            items = schema.get("items", {})
            if items:
                item_type = self._get_python_type(items)
                return f"List[{item_type}]"

        # Handle references
        if "$ref" in schema:
            ref_path = schema["$ref"]
            if ref_path.startswith("#/components/schemas/"):
                model_name = ref_path.split("/")[-1]
                return self._to_pascal_case(model_name)

        return type_mapping.get(schema_type, "Any")
