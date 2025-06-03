"""Module for working with OpenAPI specifications."""

import json
import os
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import httpx
import yaml
from openapi_spec_validator import validate
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from talkie.utils.logger import logger


class OpenApiInspector:
    """Class for working with OpenAPI specifications."""

    def __init__(self, console: Optional[Console] = None) -> None:
        """Initialize OpenAPI inspector.

        Args:
            console: Rich console for output
        """
        self.console = console or Console()
        self.client = httpx.Client(verify=True, follow_redirects=True)

    def load_spec(self, spec_url: str) -> Dict[str, Any]:
        """Load OpenAPI specification from URL or file.

        Args:
            spec_url: URL or path to specification file

        Returns:
            Dict[str, Any]: Specification as dictionary

        Raises:
            ValueError: If unable to load specification
        """
        parsed_url = urlparse(spec_url)

        # Load from local file
        if not parsed_url.scheme or parsed_url.scheme == "file":
            file_path = parsed_url.path if parsed_url.scheme == "file" else spec_url
            try:
                with open(os.path.expanduser(file_path), "r") as f:
                    content = f.read()
                    return self._parse_spec_content(content, file_path)
            except Exception as e:
                logger.error(f"Error reading specification file: {str(e)}")
                raise ValueError(f"Unable to load specification from file: {str(e)}")

        # Load from URL
        try:
            response = self.client.get(spec_url)
            response.raise_for_status()
            return self._parse_spec_content(response.text, spec_url)
        except Exception as e:
            logger.error(f"Error loading specification from URL: {str(e)}")
            raise ValueError(f"Unable to load specification from URL: {str(e)}")

    def _parse_spec_content(self, content: str, source: str) -> Dict[str, Any]:
        """Parse specification content.

        Args:
            content: Specification content
            source: Specification source (for error messages)

        Returns:
            Dict[str, Any]: Specification as dictionary

        Raises:
            ValueError: If unable to parse specification
        """
        # Try parsing as JSON
        try:
            spec = json.loads(content)
            return spec
        except json.JSONDecodeError:
            # Try parsing as YAML
            try:
                spec = yaml.safe_load(content)
                return spec
            except yaml.YAMLError as e:
                logger.error(f"Error parsing specification: {str(e)}")
                raise ValueError(f"Unable to parse specification from {source}: {str(e)}")

    def validate_spec(self, spec: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Check specification against OpenAPI standard.

        Args:
            spec: Specification as dictionary

        Returns:
            Tuple[bool, Optional[str]]: (success, error message)
        """
        try:
            validate(spec)
            return True, None
        except Exception as e:
            return False, str(e)

    def display_api_info(self, spec: Dict[str, Any]) -> None:
        """Display general API information.

        Args:
            spec: Specification as dictionary
        """
        # Extract information
        info = spec.get("info", {})
        title = info.get("title", "Unknown API")
        version = info.get("version", "Unknown version")
        description = info.get("description", "No description")

        # Display information
        self.console.print(Panel(f"[bold]{title}[/bold] [dim]v{version}[/dim]", 
                                subtitle=description[:100] + ("..." if len(description) > 100 else "")))

        # Servers
        if "servers" in spec and spec["servers"]:
            self.console.print("\n[bold]Servers:[/bold]")
            for server in spec["servers"]:
                self.console.print(f"  • {server.get('url')} - {server.get('description', '')}")

    def display_endpoints(self, spec: Dict[str, Any]) -> None:
        """Display list of available endpoints.

        Args:
            spec: Specification as dictionary
        """
        if "paths" not in spec:
            self.console.print("[yellow]Endpoints not found in specification[/yellow]")
            return

        paths = spec["paths"]
        
        # Create table for endpoints
        table = Table(title="Available Endpoints")
        table.add_column("Path", style="cyan")
        table.add_column("Method", style="green")
        table.add_column("Description")
        table.add_column("Tags")

        # Fill table
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.lower() in ["get", "post", "put", "delete", "patch", "options", "head"]:
                    description = details.get("summary", details.get("description", ""))
                    tags = ", ".join(details.get("tags", []))
                    table.add_row(path, method.upper(), description, tags)

        self.console.print(table)

    def generate_sample_request(self, spec: Dict[str, Any], path: str, method: str) -> str:
        """Generate sample talkie command for endpoint request.

        Args:
            spec: Specification as dictionary
            path: Endpoint path
            method: HTTP method

        Returns:
            str: Sample talkie command
        """
        try:
            # Check for path and method existence
            if "paths" not in spec or path not in spec["paths"] or method.lower() not in spec["paths"][path]:
                return f"# Endpoint {method.upper()} {path} not found in specification"

            endpoint = spec["paths"][path][method.lower()]
            server_url = spec.get("servers", [{"url": "https://api.example.com"}])[0]["url"]
            base_url = server_url.rstrip("/")
            full_path = path.lstrip("/")

            # Build command
            cmd = f"talkie {method.lower()} {base_url}/{full_path}"

            # Path parameters
            path_params = [param for param in endpoint.get("parameters", []) if param.get("in") == "path"]
            for param in path_params:
                name = param.get("name")
                cmd = cmd.replace(f"{{{name}}}", f"value_{name}")

            # Query parameters
            query_params = [param for param in endpoint.get("parameters", []) if param.get("in") == "query"]
            for param in query_params:
                name = param.get("name")
                cmd += f' -q "{name}=value"'

            # Headers
            header_params = [param for param in endpoint.get("parameters", []) if param.get("in") == "header"]
            for param in header_params:
                name = param.get("name")
                cmd += f' -H "{name}: value"'

            # Request body
            if "requestBody" in endpoint and method.lower() in ["post", "put", "patch"]:
                content = endpoint["requestBody"].get("content", {})
                if "application/json" in content:
                    schema = content["application/json"].get("schema", {})
                    if "properties" in schema:
                        for prop, details in schema["properties"].items():
                            if details.get("type") in ["integer", "number", "boolean"]:
                                cmd += f" {prop}:=value"
                            else:
                                cmd += f" {prop}=\"value\""

            return cmd
        except Exception as e:
            logger.error(f"Error generating sample request: {str(e)}")
            return f"# Error generating sample: {str(e)}"

    def inspect_api(self, spec_url: str, show_endpoints: bool = True) -> None:
        """Perform full API inspection.

        Args:
            spec_url: URL or path to specification file
            show_endpoints: Display endpoint list
        """
        try:
            # Load and validate specification
            # Загружаем и проверяем спецификацию
            self.console.print(f"[bold]Загрузка спецификации OpenAPI из:[/bold] {spec_url}")
            spec = self.load_spec(spec_url)
            
            is_valid, error = self.validate_spec(spec)
            if not is_valid:
                self.console.print(f"[yellow]Предупреждение:[/yellow] Спецификация содержит ошибки: {error}")
            else:
                self.console.print("[green]Спецификация валидна.[/green]")
            
            # Отображаем информацию
            self.console.print("\n[bold]Информация об API:[/bold]")
            self.display_api_info(spec)
            
            # Отображаем эндпоинты
            if show_endpoints:
                self.console.print("\n[bold]Эндпоинты:[/bold]")
                self.display_endpoints(spec)
                
                # Пример запроса для первого эндпоинта
                if "paths" in spec and spec["paths"]:
                    path = next(iter(spec["paths"]))
                    method = next((m for m in spec["paths"][path] if m.lower() in ["get", "post", "put", "delete"]), "get")
                    
                    self.console.print("\n[bold]Пример запроса:[/bold]")
                    sample = self.generate_sample_request(spec, path, method)
                    self.console.print(Syntax(sample, "bash", theme="monokai"))
        
        except Exception as e:
            self.console.print(f"[bold red]Ошибка при инспекции API:[/bold red] {str(e)}")
            logger.error(f"Ошибка при инспекции API: {str(e)}")

    def close(self) -> None:
        """Закрыть соединения."""
        self.client.close()

    def __enter__(self) -> "OpenApiInspector":
        """Вход в контекстный менеджер."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Выход из контекстного менеджера."""
        self.close()

# Создаем глобальный экземпляр инспектора
_inspector = OpenApiInspector()

def load_openapi_spec(spec_url: str) -> Dict[str, Any]:
    """Загрузить спецификацию OpenAPI из URL или файла."""
    return _inspector.load_spec(spec_url)

def validate_openapi_spec(spec: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Проверить спецификацию на соответствие стандарту OpenAPI."""
    return _inspector.validate_spec(spec)

def display_api_info(spec: Dict[str, Any]) -> None:
    """Отобразить общую информацию об API."""
    _inspector.display_api_info(spec)

def display_endpoints(spec: Dict[str, Any]) -> None:
    """Отобразить список доступных эндпоинтов."""
    _inspector.display_endpoints(spec)

def generate_sample_request(spec: Dict[str, Any], path: str, method: str) -> str:
    """Генерировать пример команды talkie для запроса к эндпоинту."""
    return _inspector.generate_sample_request(spec, path, method)

def inspect_api(spec_url: str, show_endpoints: bool = True) -> None:
    """Проверить и отобразить информацию об API."""
    _inspector.inspect_api(spec_url, show_endpoints)

def extract_endpoints(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Извлечь список всех конечных точек из спецификации.
    
    Args:
        spec: Спецификация OpenAPI
        
    Returns:
        List[Dict[str, Any]]: Список эндпоинтов с их деталями
    """
    endpoints = []
    
    if "paths" not in spec:
        return endpoints
    
    for path, methods in spec["paths"].items():
        for method, details in methods.items():
            if method.lower() in ["get", "post", "put", "delete", "patch", "options", "head"]:
                endpoint = {
                    "path": path,
                    "method": method.lower(),
                    "summary": details.get("summary", ""),
                    "description": details.get("description", ""),
                    "tags": details.get("tags", []),
                    "parameters": details.get("parameters", []),
                    "responses": details.get("responses", {}),
                }
                endpoints.append(endpoint)
    
    return endpoints

def extract_endpoint_details(spec: Dict[str, Any], path: str, method: str) -> Dict[str, Any]:
    """Извлечь детальную информацию о конкретном эндпоинте.
    
    Args:
        spec: Спецификация OpenAPI
        path: Путь эндпоинта
        method: HTTP-метод
        
    Returns:
        Dict[str, Any]: Детали эндпоинта
    """
    if "paths" not in spec or path not in spec["paths"]:
        raise ValueError(f"Путь {path} не найден в спецификации")
    
    if method.lower() not in spec["paths"][path]:
        raise ValueError(f"Метод {method} не найден для пути {path}")
    
    return spec["paths"][path][method.lower()]

def format_openapi_spec(spec: Dict[str, Any]) -> str:
    """Форматировать спецификацию OpenAPI для вывода.
    
    Args:
        spec: Спецификация OpenAPI
        
    Returns:
        str: Отформатированная спецификация
    """
    # Форматируем как YAML для лучшей читаемости
    return yaml.dump(spec, allow_unicode=True, sort_keys=False) 