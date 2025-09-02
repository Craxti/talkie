"""Main CLI module for Talkie."""

import sys
import asyncio
import os
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

import typer
from rich.console import Console
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from talkie.core.client import HttpClient
from talkie.core.async_client import AsyncHttpClient
from talkie.core.request_builder import RequestBuilder
from talkie.core.response_formatter import format_response
from talkie.utils.config import Config
from talkie.utils.curl_generator import CurlGenerator
from talkie.utils.formatter import DataFormatter
from talkie.utils.openapi import OpenApiInspector
from talkie.utils.validators import InputValidator, ValidationError
from talkie.utils.graphql import GraphQLClient, GraphQLResponse
from talkie.utils.cache import get_cache, CacheConfig, set_cache_config
from talkie.core.websocket_client import WebSocketClient
from talkie.utils.openapi_generator import OpenApiClientGenerator
from talkie.utils.benchmarks import BenchmarkRunner

# Create application
cli = typer.Typer(
    name="talkie",
    help="A convenient command-line HTTP client for API interaction.",
    add_completion=False,
)

console = Console()


@cli.command("get")
def http_get(
    url: str = typer.Argument(..., help="URL for request"),
    header: List[str] = typer.Option(
        [], "--header", "-H", help="Headers in format 'key:value'"
    ),
    query: List[str] = typer.Option(
        [], "--query", "-q", help="Query parameters in format 'key=value'"
    ),
    output: str = typer.Option(
        None, "--output", "-o", help="Save response to file"
    ),
    timeout: float = typer.Option(
        30.0, "--timeout", "-t", help="Request timeout in seconds"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Verbose output"
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Output only JSON-content"
    ),
    headers_only: bool = typer.Option(
        False, "--headers", help="Output only headers"
    ),
    curl: bool = typer.Option(
        False, "--curl", help="Output equivalent curl command"
    ),
    format_output: Optional[str] = typer.Option(
        None, "--format", "-f", help="Output format: json, xml, html, markdown"
    ),
    cert: Optional[str] = typer.Option(
        None, "--cert", help="Client certificate file (.pem) or cert:key pair"
    ),
) -> None:
    """Perform GET request to specified URL."""
    _handle_request("GET", url, header, None, query, output, timeout, verbose, json_output, headers_only, curl, format_output, cert)


@cli.command()
def post(
    url: str = typer.Argument(..., help="URL for request"),
    data: List[str] = typer.Option(None, "-d", "--data", help="Data to send (key=value or key:=value for JSON)"),
    headers: List[str] = typer.Option(None, "-H", "--header", help="Request headers (key:value)"),
    query: List[str] = typer.Option(None, "-q", "--query", help="Request parameters (key=value)"),
    format: str = typer.Option("json", "-f", "--format", help="Output format (json, xml, html)"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="File to save response"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output"),
    json_output: bool = typer.Option(False, "--json", help="Output only response body in JSON"),
    timeout: float = typer.Option(30.0, "-t", "--timeout", help="Request timeout in seconds"),
    curl: bool = typer.Option(False, "--curl", help="Output equivalent curl command"),
) -> None:
    """Send POST request."""
    try:
        # Create request builder
        builder = RequestBuilder(
            method="POST",
            url=url,
            headers=headers,
            data=data,
            query=query,
            timeout=timeout
        )
        
        # Apply configuration
        config = Config.load_default()
        builder.apply_config(config)
        
        # Build request
        request = builder.build()
        
        # Output curl command if requested
        if curl:
            console.print("[bold]Equivalent curl command:[/bold]")
            curl_command = CurlGenerator.generate_from_request(request)
            CurlGenerator.display_curl(curl_command, console)
            if not verbose:
                return
        
        # Output request information in verbose mode
        if verbose:
            console.print(f"[bold]URL:[/bold] {request['url']}")
            console.print("[bold]Method:[/bold] POST")
            
            if request["headers"]:
                console.print("[bold]Headers:[/bold]")
                for key, value in request["headers"].items():
                    console.print(f"  {key}: {value}")
            
            if "json" in request and request["json"]:
                console.print("[bold]JSON data:[/bold]")
                formatter = DataFormatter(console=console)
                formatted_json = formatter.format_json(request["json"], colorize=False)
                syntax = Syntax(formatted_json, "json", theme="monokai", word_wrap=True)
                console.print(syntax)
            elif "data" in request and request["data"]:
                console.print("[bold]Form data:[/bold]")
                for key, value in request["data"].items():
                    console.print(f"  {key}: {value}")
            
            console.print("[bold]Sending request...[/bold]")
        
        # Perform request
        client = HttpClient()
        response = client.send(request)
        
        # Format and output response
        from talkie.cli.output import print_response
        print_response(
            response,
            format=format,
            verbose=verbose,
            json_only=json_output,
            headers_only=False,
            output_file=output
        )
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@cli.command("put")
def http_put(
    url: str = typer.Argument(..., help="URL for request"),
    header: List[str] = typer.Option(
        [], "--header", "-H", help="Headers in format 'key:value'"
    ),
    data: List[str] = typer.Option(
        [], "--data", "-d", help="Data in format 'key=value' or 'key:=value' for JSON"
    ),
    query: List[str] = typer.Option(
        [], "--query", "-q", help="Query parameters in format 'key=value'"
    ),
    output: str = typer.Option(
        None, "--output", "-o", help="Save response to file"
    ),
    timeout: float = typer.Option(
        30.0, "--timeout", "-t", help="Request timeout in seconds"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Verbose output"
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Output only JSON-content"
    ),
    headers_only: bool = typer.Option(
        False, "--headers", help="Output only headers"
    ),
    curl: bool = typer.Option(
        False, "--curl", help="Output equivalent curl command"
    ),
    format_output: Optional[str] = typer.Option(
        None, "--format", "-f", help="Output format: json, xml, html, markdown"
    ),
) -> None:
    """Perform PUT request to specified URL."""
    _handle_request("PUT", url, header, data, query, output, timeout, verbose, json_output, headers_only, curl, format_output)


@cli.command("delete")
def http_delete(
    url: str = typer.Argument(..., help="URL for request"),
    header: List[str] = typer.Option(
        [], "--header", "-H", help="Headers in format 'key:value'"
    ),
    data: List[str] = typer.Option(
        [], "--data", "-d", help="Data in format 'key=value' or 'key:=value' for JSON"
    ),
    query: List[str] = typer.Option(
        [], "--query", "-q", help="Query parameters in format 'key=value'"
    ),
    output: str = typer.Option(
        None, "--output", "-o", help="Save response to file"
    ),
    timeout: float = typer.Option(
        30.0, "--timeout", "-t", help="Request timeout in seconds"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Verbose output"
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Output only JSON-content"
    ),
    headers_only: bool = typer.Option(
        False, "--headers", help="Output only headers"
    ),
    curl: bool = typer.Option(
        False, "--curl", help="Output equivalent curl command"
    ),
    format_output: Optional[str] = typer.Option(
        None, "--format", "-f", help="Output format: json, xml, html, markdown"
    ),
) -> None:
    """Perform DELETE request to specified URL."""
    _handle_request("DELETE", url, header, data, query, output, timeout, verbose, json_output, headers_only, curl, format_output)


@cli.command("openapi")
def openapi_inspect(
    spec_url: str = typer.Argument(..., help="URL or path to OpenAPI specification file"),
    endpoints: bool = typer.Option(
        True, "--endpoints/--no-endpoints", help="Show list of endpoints"
    ),
) -> None:
    """Inspect OpenAPI specification and display API information."""
    try:
        with OpenApiInspector(console=console) as inspector:
            inspector.inspect_api(spec_url, show_endpoints=endpoints)
    except Exception as e:
        console.print(f"[bold red]Error in OpenAPI inspection:[/bold red] {str(e)}")
        sys.exit(1)


@cli.command("format")
def format_data(
    input_file: str = typer.Argument(..., help="File to format"),
    output_file: str = typer.Option(
        None, "--output", "-o", help="File to save result (default output to console)"
    ),
    format_type: str = typer.Option(
        None, "--type", "-t", help="Formatting type (json, xml, html, markdown)"
    ),
) -> None:
    """Format JSON, XML or HTML file."""
    try:
        # Determine MIME type by file extension
        content_type = None
        if input_file.endswith(".json"):
            content_type = "application/json"
        elif input_file.endswith(".xml"):
            content_type = "application/xml"
        elif input_file.endswith(".html") or input_file.endswith(".htm"):
            content_type = "text/html"

        # Read file content
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Format content
        formatter = DataFormatter(console=console)
        formatted_content = formatter.format_data(content, content_type, format_type)

        # Output result
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(formatted_content)
            console.print(f"[green]Formatted output saved to:[/green] {output_file}")
        else:
            # Use rich formatting for console output
            formatter.display_formatted(content, content_type or "")

    except Exception as e:
        console.print(f"[bold red]Error in formatting:[/bold red] {str(e)}")
        sys.exit(1)


@cli.command("curl")
def generate_curl(
    method: str = typer.Option(
        "GET", "--method", "-X", help="HTTP method (GET, POST, PUT, DELETE etc.)"
    ),
    url: str = typer.Argument(..., help="URL for request"),
    header: List[str] = typer.Option(
        [], "--header", "-H", help="Headers in format 'key:value'"
    ),
    data: List[str] = typer.Option(
        [], "--data", "-d", help="Data in format 'key=value' or 'key:=value' for JSON"
    ),
    query: List[str] = typer.Option(
        [], "--query", "-q", help="Query parameters in format 'key=value'"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Add -v flag to curl command"
    ),
    insecure: bool = typer.Option(
        False, "--insecure", "-k", help="Add -k flag to curl command"
    ),
) -> None:
    """Generate equivalent curl command for request."""
    try:
        # Create request builder
        builder = RequestBuilder(
            method=method,
            url=url,
            headers=header,
            data=data,
            query=query,
        )
        
        # Build request
        request = builder.build()
        
        # Add verbose and insecure options
        request["verbose"] = verbose
        request["insecure"] = insecure
        
        # Generate curl command
        curl_command = CurlGenerator.generate_from_request(request)
        
        # Output result
        console.print("[bold]Equivalent curl command:[/bold]")
        CurlGenerator.display_curl(curl_command, console)
        
    except Exception as e:
        console.print(f"[bold red]Error in generating curl command:[/bold red] {str(e)}")
        sys.exit(1)


@cli.command("parallel")
def parallel_requests(
    file: str = typer.Option(
        None, "--file", "-f", help="File with request list"
    ),
    method: str = typer.Option(
        None, "--method", "-X", help="HTTP method (for all requests if not specified in file)"
    ),
    base_url: str = typer.Option(
        None, "--base-url", "-b", help="Base URL for all requests"
    ),
    urls: List[str] = typer.Option(
        [], "--url", "-u", help="URL for request (can be specified multiple times)"
    ),
    concurrency: int = typer.Option(
        10, "--concurrency", "-c", help="Maximum number of simultaneous requests"
    ),
    delay: float = typer.Option(
        0.0, "--delay", "-d", help="Delay between requests in seconds"
    ),
    timeout: float = typer.Option(
        30.0, "--timeout", "-t", help="Request timeout in seconds"
    ),
    output_dir: str = typer.Option(
        None, "--output-dir", "-o", help="Directory to save results"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Verbose output"
    ),
    summary: bool = typer.Option(
        True, "--summary/--no-summary", help="Output summary of results"
    ),
) -> None:
    """
    Perform multiple requests in parallel.
    
    Requests can be specified in file (one per line in format "METHOD URL")
    or via command-line options.
    """
    try:
        # Prepare requests
        requests = []
        
        # If file specified, read requests from it
        if file:
            if not os.path.exists(file):
                console.print(f"[bold red]Error:[/bold red] File not found: {file}")
                sys.exit(1)
                
            console.print(f"[bold]Reading requests from file:[/bold] {file}")
            
            # In this case requests will be processed directly in async client
            requests = []
        
        # If URLs specified via command-line options
        elif urls:
            if not method:
                console.print("[bold red]Error:[/bold red] HTTP method (--method) not specified")
                sys.exit(1)
                
            for i, url in enumerate(urls):
                # Add base URL if specified and URL does not start with http
                if base_url and not url.startswith(("http://", "https://")):
                    full_url = f"{base_url.rstrip('/')}/{url.lstrip('/')}"
                else:
                    full_url = url
                
                requests.append({
                    "method": method.upper(),
                    "url": full_url,
                    "request_id": f"req_{i+1}"
                })
        
        # If neither file nor URLs
        else:
            console.print("[bold red]Error:[/bold red] No requests specified. Use --file or --url")
            sys.exit(1)
        
        # Create directory for saving results if specified
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            console.print(f"[bold]Results will be saved to directory:[/bold] {output_dir}")
        
        # Start asynchronous request execution
        if verbose:
            console.print(f"[bold]Maximum number of simultaneous requests:[/bold] {concurrency}")
            console.print(f"[bold]Delay between requests:[/bold] {delay} sec.")
            console.print(f"[bold]Request timeout:[/bold] {timeout} sec.")
        
        # For progress display
        progress_task_id = None
        
        async def run_requests():
            nonlocal progress_task_id
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
                transient=True,
            ) as progress:
                description = "Executing requests"
                progress_task_id = progress.add_task(description, total=len(requests) if requests else 100)
                
                async with AsyncHttpClient(
                    timeout=timeout,
                    concurrency=concurrency,
                    request_delay=delay
                ) as client:
                    if file:
                        # Execute requests from file
                        results = await client.execute_from_file(file, output_dir)
                        # Update progress
                        progress.update(progress_task_id, total=len(results), completed=len(results))
                    else:
                        # Execute requests from list
                        completed = 0
                        results = []
                        
                        for batch in _batch_requests(requests, concurrency):
                            batch_results = await client.execute_batch(batch)
                            results.extend(batch_results)
                            
                            completed += len(batch_results)
                            progress.update(progress_task_id, completed=completed)
                            
                            # Save results if directory specified
                            if output_dir:
                                for req_id, response, error in batch_results:
                                    if req_id:
                                        filename = os.path.join(output_dir, f"{req_id}.txt")
                                        with open(filename, "w", encoding="utf-8") as f:
                                            if error:
                                                f.write(f"ERROR: {str(error)}\n")
                                            elif response:
                                                f.write(f"STATUS: {response.status_code}\n")
                                                f.write(f"HEADERS:\n")
                                                for key, value in response.headers.items():
                                                    f.write(f"{key}: {value}\n")
                                                f.write(f"\nBODY:\n{response.text}\n")
                
                return results
        
        # Start asynchronous execution
        results = asyncio.run(run_requests())
        
        # Output summary of results
        if summary:
            console.print("\n[bold]Results summary:[/bold]")
            
            total = len(results)
            successful = sum(1 for _, resp, err in results if resp and not err)
            failed = sum(1 for _, resp, err in results if err)
            
            console.print(f"Total requests: {total}")
            console.print(f"Successful: [green]{successful}[/green]")
            
            if failed > 0:
                console.print(f"Failed: [red]{failed}[/red]")
                
                console.print("\n[bold]Errors:[/bold]")
                for req_id, _, err in results:
                    if err:
                        console.print(f"  [red]{req_id}:[/red] {str(err)}")
            
            # Status code statistics
            status_counts = {}
            for _, resp, _ in results:
                if resp:
                    status = resp.status_code
                    status_counts[status] = status_counts.get(status, 0) + 1
            
            if status_counts:
                console.print("\n[bold]Status codes:[/bold]")
                for status, count in sorted(status_counts.items()):
                    color = "[green]" if 200 <= status < 300 else "[yellow]" if 300 <= status < 400 else "[red]"
                    console.print(f"  {color}{status}:[/] {count}")
            
            if output_dir:
                console.print(f"\nResults saved to directory: [bold]{output_dir}[/bold]")
        
    except Exception as e:
        console.print(f"[bold red]Error in executing requests:[/bold red] {str(e)}")
        import traceback
        if verbose:
            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command("graphql")
def graphql_request(
    endpoint: str = typer.Argument(..., help="GraphQL endpoint URL"),
    query: Optional[str] = typer.Option(
        None, "--query", "-q", help="GraphQL query string"
    ),
    query_file: Optional[str] = typer.Option(
        None, "--file", "-f", help="File containing GraphQL query"
    ),
    variables: List[str] = typer.Option(
        [], "--variable", "-v", help="Variables in format 'key=value' or 'key:=value' for JSON"
    ),
    operation_name: Optional[str] = typer.Option(
        None, "--operation", help="Operation name (if query has multiple operations)"
    ),
    headers: List[str] = typer.Option(
        [], "--header", "-H", help="Request headers in format 'key:value'"
    ),
    timeout: float = typer.Option(
        30.0, "--timeout", "-t", help="Request timeout in seconds"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Save response to file"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Verbose output"
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Output only JSON content"
    ),
    introspect: bool = typer.Option(
        False, "--introspect", help="Perform schema introspection"
    ),
    cert: Optional[str] = typer.Option(
        None, "--cert", help="Client certificate file (.pem) or cert:key pair"
    ),
) -> None:
    """Execute GraphQL query."""
    try:
        # Validate inputs
        try:
            endpoint = InputValidator.validate_url(endpoint)
            timeout = InputValidator.validate_timeout(timeout)
            
            # Parse and validate headers
            parsed_headers = InputValidator.validate_headers(headers) if headers else {}
            
            # Parse and validate variables
            form_vars, json_vars = InputValidator.validate_data_params(variables) if variables else ({}, {})
            # Combine form and JSON variables (prefer JSON for GraphQL)
            all_variables = {**form_vars, **json_vars} if form_vars or json_vars else None
            
        except ValidationError as e:
            console.print(f"[bold red]Validation Error:[/bold red] {str(e)}")
            sys.exit(1)
        
        # Get query text
        query_text = None
        if query:
            query_text = query
        elif query_file:
            try:
                with open(query_file, 'r', encoding='utf-8') as f:
                    query_text = f.read()
            except FileNotFoundError:
                console.print(f"[bold red]Error:[/bold red] Query file not found: {query_file}")
                sys.exit(1)
            except Exception as e:
                console.print(f"[bold red]Error reading query file:[/bold red] {str(e)}")
                sys.exit(1)
        elif introspect:
            # Use introspection query
            query_text = """
            query IntrospectionQuery {
              __schema {
                queryType { name }
                mutationType { name }
                subscriptionType { name }
                types {
                  ...FullType
                }
              }
            }
            
            fragment FullType on __Type {
              kind
              name
              description
              fields(includeDeprecated: true) {
                name
                description
                args {
                  ...InputValue
                }
                type {
                  ...TypeRef
                }
                isDeprecated
                deprecationReason
              }
            }
            
            fragment InputValue on __InputValue {
              name
              description
              type { ...TypeRef }
              defaultValue
            }
            
            fragment TypeRef on __Type {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                  ofType {
                    kind
                    name
                  }
                }
              }
            }
            """
        else:
            console.print("[bold red]Error:[/bold red] No query specified. Use --query, --file, or --introspect")
            sys.exit(1)
        
        # Parse certificate if provided
        cert_config = None
        if cert:
            if ':' in cert:
                cert_parts = cert.split(':', 1)
                cert_config = (cert_parts[0], cert_parts[1])
            else:
                cert_config = cert
        
        # Create GraphQL client
        client = GraphQLClient(
            endpoint=endpoint,
            headers=parsed_headers,
            timeout=int(timeout)
        )
        
        # Override HttpClient with certificate support if needed
        if cert_config:
            client.http_client = HttpClient(cert=cert_config, timeout=int(timeout))
        
        if verbose:
            console.print(f"[bold]GraphQL Endpoint:[/bold] {endpoint}")
            if parsed_headers:
                console.print("[bold]Headers:[/bold]")
                for key, value in parsed_headers.items():
                    console.print(f"  {key}: {value}")
            if all_variables:
                console.print("[bold]Variables:[/bold]")
                formatter = DataFormatter(console=console)
                formatted_vars = formatter.format_json(all_variables, colorize=False)
                syntax = Syntax(formatted_vars, "json", theme="monokai", word_wrap=True)
                console.print(syntax)
            if operation_name:
                console.print(f"[bold]Operation:[/bold] {operation_name}")
            console.print("[bold]Executing GraphQL query...[/bold]")
        
        # Execute GraphQL query
        response = client.execute(
            query=query_text,
            variables=all_variables,
            operation_name=operation_name
        )
        
        # Format and output response
        if introspect and response.data:
            # Special handling for introspection
            schema = response.data.get("__schema", {})
            console.print("[bold]GraphQL Schema Information:[/bold]")
            
            # Show available types
            if "queryType" in schema and schema["queryType"]:
                console.print(f"  Query Type: {schema['queryType']['name']}")
            if "mutationType" in schema and schema["mutationType"]:
                console.print(f"  Mutation Type: {schema['mutationType']['name']}")
            if "subscriptionType" in schema and schema["subscriptionType"]:
                console.print(f"  Subscription Type: {schema['subscriptionType']['name']}")
            
            types = schema.get("types", [])
            user_types = [t for t in types if not t["name"].startswith("__")]
            console.print(f"  Available Types: {len(user_types)}")
            
            if verbose:
                console.print("\n[bold]Custom Types:[/bold]")
                for type_info in user_types[:10]:  # Show first 10 types
                    console.print(f"  - {type_info['name']} ({type_info['kind']})")
                if len(user_types) > 10:
                    console.print(f"  ... and {len(user_types) - 10} more")
        
        # Output response
        response_data = {
            "data": response.data,
            "errors": response.errors
        }
        
        if output:
            # Save to file
            with open(output, 'w', encoding='utf-8') as f:
                import json
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            console.print(f"[green]Response saved to:[/green] {output}")
        elif json_output:
            # JSON only output
            import json
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        else:
            # Rich formatted output
            if response.errors:
                console.print("[bold red]GraphQL Errors:[/bold red]")
                for error in response.errors:
                    console.print(f"  - {error.get('message', 'Unknown error')}")
                    if 'locations' in error:
                        locations = error['locations']
                        for loc in locations:
                            console.print(f"    at line {loc.get('line', '?')}, column {loc.get('column', '?')}")
                console.print()
            
            if response.data:
                console.print("[bold]GraphQL Response:[/bold]")
                formatter = DataFormatter(console=console)
                formatted_data = formatter.format_json(response.data, colorize=True)
                syntax = Syntax(formatted_data, "json", theme="monokai", word_wrap=True)
                console.print(syntax)
            elif not response.errors:
                console.print("[yellow]No data received[/yellow]")
    
    except Exception as e:
        console.print(f"[bold red]Error executing GraphQL query:[/bold red] {str(e)}")
        import traceback
        if verbose:
            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command("cache")
def cache_management(
    action: str = typer.Argument(..., help="Action: stats, clear, config"),
    ttl: Optional[int] = typer.Option(
        None, "--ttl", help="Set default TTL in seconds"
    ),
    max_entries: Optional[int] = typer.Option(
        None, "--max-entries", help="Set maximum number of cache entries"
    ),
    max_size: Optional[int] = typer.Option(
        None, "--max-size", help="Set maximum cache size in MB"
    ),
    enable: Optional[bool] = typer.Option(
        None, "--enable/--disable", help="Enable or disable caching"
    ),
    cache_get: Optional[bool] = typer.Option(
        None, "--cache-get/--no-cache-get", help="Enable/disable GET request caching"
    ),
    cache_graphql: Optional[bool] = typer.Option(
        None, "--cache-graphql/--no-cache-graphql", help="Enable/disable GraphQL query caching"
    ),
) -> None:
    """Manage response cache."""
    try:
        cache = get_cache()
        
        if action == "stats":
            # Show cache statistics
            stats = cache.get_cache_stats()
            console.print("[bold]Cache Statistics:[/bold]")
            console.print(f"  Status: {'Enabled' if stats['enabled'] else 'Disabled'}")
            console.print(f"  Entries: {stats['total_entries']}")
            console.print(f"  Size: {stats['total_size_mb']} MB")
            console.print(f"  Directory: {stats['cache_dir']}")
            
            if stats['total_entries'] > 0:
                console.print("\n[bold]Cache Configuration:[/bold]")
                config = stats['config']
                console.print(f"  Default TTL: {config['default_ttl']} seconds")
                console.print(f"  Max Entries: {config['max_entries']}")
                console.print(f"  Max Size: {config['max_size_mb']} MB")
                console.print(f"  Cache GET: {config['cache_get']}")
                console.print(f"  Cache POST: {config['cache_post']}")
                console.print(f"  Cache GraphQL: {config['cache_graphql']}")
        
        elif action == "clear":
            # Clear cache
            cache.clear_cache()
            console.print("[green]Cache cleared successfully[/green]")
        
        elif action == "config":
            # Update cache configuration
            current_config = cache.config
            
            # Create new config with updated values
            new_config_data = current_config.model_dump()
            
            if ttl is not None:
                new_config_data['default_ttl'] = ttl
            if max_entries is not None:
                new_config_data['max_entries'] = max_entries
            if max_size is not None:
                new_config_data['max_size_mb'] = max_size
            if enable is not None:
                new_config_data['enabled'] = enable
            if cache_get is not None:
                new_config_data['cache_get'] = cache_get
            if cache_graphql is not None:
                new_config_data['cache_graphql'] = cache_graphql
            
            # Apply new configuration
            new_config = CacheConfig(**new_config_data)
            set_cache_config(new_config)
            
            console.print("[green]Cache configuration updated[/green]")
            
            # Show updated configuration
            console.print("\n[bold]Current Configuration:[/bold]")
            console.print(f"  Enabled: {new_config.enabled}")
            console.print(f"  Default TTL: {new_config.default_ttl} seconds")
            console.print(f"  Max Entries: {new_config.max_entries}")
            console.print(f"  Max Size: {new_config.max_size_mb} MB")
            console.print(f"  Cache GET: {new_config.cache_get}")
            console.print(f"  Cache GraphQL: {new_config.cache_graphql}")
        
        else:
            console.print(f"[bold red]Error:[/bold red] Unknown action '{action}'. Use: stats, clear, or config")
            sys.exit(1)
    
    except Exception as e:
        console.print(f"[bold red]Error managing cache:[/bold red] {str(e)}")
        sys.exit(1)


@cli.command("websocket")
def websocket_connect(
    uri: str = typer.Argument(..., help="WebSocket URI to connect to"),
    headers: List[str] = typer.Option(
        [], "--header", "-H", help="Request headers in format 'key:value'"
    ),
    message: Optional[str] = typer.Option(
        None, "--message", "-m", help="Message to send after connection"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Interactive mode for sending/receiving messages"
    ),
    listen: bool = typer.Option(
        False, "--listen", "-l", help="Only listen for incoming messages"
    ),
    timeout: float = typer.Option(
        10.0, "--timeout", "-t", help="Connection timeout in seconds"
    ),
    max_messages: Optional[int] = typer.Option(
        None, "--max-messages", help="Maximum number of messages to receive before closing"
    ),
    duration: Optional[float] = typer.Option(
        None, "--duration", help="Duration to keep connection open in seconds"
    ),
    cert: Optional[str] = typer.Option(
        None, "--cert", help="Client certificate file (.pem) or cert:key pair"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Save received messages to file"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Verbose output"
    ),
) -> None:
    """Connect to WebSocket server and send/receive messages."""
    async def main():
        try:
            # Validate inputs
            try:
                uri_validated = InputValidator.validate_url(uri)
                timeout_validated = InputValidator.validate_timeout(timeout)
                
                # Parse headers
                parsed_headers = InputValidator.validate_headers(headers) if headers else {}
                
            except ValidationError as e:
                console.print(f"[bold red]Validation Error:[/bold red] {str(e)}")
                sys.exit(1)
            
            # Parse certificate if provided
            cert_file = None
            key_file = None
            if cert:
                if ':' in cert:
                    cert_parts = cert.split(':', 1)
                    cert_file, key_file = cert_parts[0], cert_parts[1]
                else:
                    cert_file = cert
            
            # Create WebSocket client
            client = WebSocketClient(
                uri=uri_validated,
                headers=parsed_headers,
                timeout=timeout_validated,
                cert_file=cert_file,
                key_file=key_file
            )
            
            if verbose:
                console.print(f"[bold]Connecting to:[/bold] {uri_validated}")
                if parsed_headers:
                    console.print("[bold]Headers:[/bold]")
                    for key, value in parsed_headers.items():
                        console.print(f"  {key}: {value}")
            
            # Connect to WebSocket
            connected = await client.connect()
            if not connected:
                console.print("[bold red]Failed to connect to WebSocket[/bold red]")
                sys.exit(1)
            
            console.print(f"[green]Connected to {uri_validated}[/green]")
            
            # Prepare output file if specified
            output_file = None
            if output:
                output_file = open(output, 'w', encoding='utf-8')
            
            try:
                received_count = 0
                start_time = asyncio.get_event_loop().time()
                
                # Send initial message if provided
                if message:
                    success = await client.send(message)
                    if success:
                        console.print(f"[blue]Sent:[/blue] {message}")
                    else:
                        console.print("[red]Failed to send message[/red]")
                
                # Interactive mode
                if interactive:
                    console.print("[yellow]Interactive mode. Type messages (Ctrl+C to exit):[/yellow]")
                    
                    # Start message listener task
                    async def listen_task():
                        nonlocal received_count
                        while client.is_connected:
                            try:
                                msg = await asyncio.wait_for(client.receive(), timeout=1.0)
                                if msg:
                                    received_count += 1
                                    timestamp = datetime.now().strftime("%H:%M:%S")
                                    console.print(f"[green]{timestamp} Received ({msg.type}):[/green] {msg.data}")
                                    
                                    if output_file:
                                        output_file.write(f"{timestamp} {msg.type}: {msg.data}\n")
                                        output_file.flush()
                                    
                                    if max_messages and received_count >= max_messages:
                                        break
                            except asyncio.TimeoutError:
                                continue
                            except Exception as e:
                                if verbose:
                                    console.print(f"[red]Error receiving message: {e}[/red]")
                                break
                    
                    listener = asyncio.create_task(listen_task())
                    
                    try:
                        while client.is_connected:
                            # Get user input
                            try:
                                user_message = await asyncio.get_event_loop().run_in_executor(
                                    None, input, "> "
                                )
                                if user_message.strip():
                                    success = await client.send(user_message)
                                    if not success:
                                        console.print("[red]Failed to send message[/red]")
                            except EOFError:
                                break
                            except KeyboardInterrupt:
                                break
                    finally:
                        listener.cancel()
                
                # Listen-only mode or single message mode
                else:
                    while client.is_connected:
                        try:
                            # Check duration limit
                            if duration:
                                elapsed = asyncio.get_event_loop().time() - start_time
                                if elapsed >= duration:
                                    console.print(f"[yellow]Duration limit reached ({duration}s)[/yellow]")
                                    break
                            
                            # Receive message with timeout
                            msg = await asyncio.wait_for(client.receive(), timeout=1.0)
                            if msg:
                                received_count += 1
                                timestamp = datetime.now().strftime("%H:%M:%S")
                                console.print(f"[green]{timestamp} Received ({msg.type}):[/green] {msg.data}")
                                
                                if output_file:
                                    output_file.write(f"{timestamp} {msg.type}: {msg.data}\n")
                                    output_file.flush()
                                
                                # Check message count limit
                                if max_messages and received_count >= max_messages:
                                    console.print(f"[yellow]Message limit reached ({max_messages})[/yellow]")
                                    break
                        
                        except asyncio.TimeoutError:
                            # Continue waiting for messages
                            continue
                        except KeyboardInterrupt:
                            console.print("\n[yellow]Interrupted by user[/yellow]")
                            break
                        except Exception as e:
                            if verbose:
                                console.print(f"[red]Error: {e}[/red]")
                            break
            
            finally:
                if output_file:
                    output_file.close()
                    console.print(f"[green]Messages saved to:[/green] {output}")
                
                # Disconnect
                await client.disconnect()
                console.print(f"[blue]Disconnected. Received {received_count} messages.[/blue]")
        
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            if verbose:
                import traceback
                console.print(traceback.format_exc())
            sys.exit(1)
    
    # Import datetime here to avoid circular imports
    from datetime import datetime
    
    # Run async main
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Connection interrupted[/yellow]")


@cli.command("generate-client")
def generate_openapi_client(
    spec_url: str = typer.Argument(..., help="URL or path to OpenAPI specification"),
    output_dir: str = typer.Option(
        "generated_client", "--output", "-o", help="Output directory for generated client"
    ),
    class_name: str = typer.Option(
        "ApiClient", "--class-name", "-c", help="Name of the generated client class"
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite existing files in output directory"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Verbose output"
    ),
) -> None:
    """Generate Python client code from OpenAPI specification."""
    try:
        # Validate inputs
        try:
            spec_url = InputValidator.validate_url(spec_url) if spec_url.startswith('http') else spec_url
        except ValidationError as e:
            console.print(f"[bold red]Validation Error:[/bold red] {str(e)}")
            sys.exit(1)
        
        # Check if output directory exists
        output_path = Path(output_dir)
        if output_path.exists() and not overwrite:
            if list(output_path.iterdir()):  # Directory not empty
                console.print(f"[bold red]Error:[/bold red] Output directory '{output_dir}' already exists and is not empty.")
                console.print("Use --overwrite to overwrite existing files.")
                sys.exit(1)
        
        if verbose:
            console.print(f"[bold]Generating client from:[/bold] {spec_url}")
            console.print(f"[bold]Output directory:[/bold] {output_dir}")
            console.print(f"[bold]Client class name:[/bold] {class_name}")
        
        # Create generator
        generator = OpenApiClientGenerator(spec_url, class_name)
        
        with console.status("[bold green]Loading OpenAPI specification...") as status:
            try:
                generator.load_specification()
                status.update("[bold green]Generating client code...")
                
                # Generate client
                client_file = generator.generate_client(output_dir)
                
                status.stop()
                
                # Show results
                console.print(f"[green]OK Client generated successfully![/green]")
                console.print(f"[blue]Main client file:[/blue] {client_file}")
                console.print(f"[blue]Generated methods:[/blue] {len(generator.generated_methods)}")
                
                if verbose:
                    console.print("\n[bold]Generated methods:[/bold]")
                    for method in generator.generated_methods[:10]:  # Show first 10
                        console.print(f"  - {method.name}() - {method.description[:80]}...")
                    
                    if len(generator.generated_methods) > 10:
                        remaining = len(generator.generated_methods) - 10
                        console.print(f"  ... and {remaining} more methods")
                
                # Show usage instructions
                console.print(f"\n[bold]Usage:[/bold]")
                console.print(f"```python")
                console.print(f"from {output_dir}.{class_name.lower()} import {class_name}")
                console.print(f"")
                console.print(f"client = {class_name}(base_url='https://api.example.com')")
                console.print(f"# Use generated methods...")
                console.print(f"```")
                
                # Show generated files
                console.print(f"\n[bold]Generated files:[/bold]")
                for file_path in output_path.rglob("*"):
                    if file_path.is_file():
                        console.print(f"  - {file_path}")
            
            except FileNotFoundError:
                console.print(f"[bold red]Error:[/bold red] OpenAPI specification not found: {spec_url}")
                sys.exit(1)
            except Exception as e:
                console.print(f"[bold red]Error loading specification:[/bold red] {str(e)}")
                if verbose:
                    import traceback
                    console.print(traceback.format_exc())
                sys.exit(1)
    
    except Exception as e:
        console.print(f"[bold red]Error generating client:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command("benchmark")
def run_benchmark(
    test_url: str = typer.Option(
        "http://httpbin.org/json", "--url", "-u", help="URL to benchmark against"
    ),
    output_dir: str = typer.Option(
        "benchmarks", "--output", "-o", help="Output directory for benchmark results"
    ),
    benchmark_type: str = typer.Option(
        "full", "--type", "-t", help="Benchmark type: full, http, cache, async, memory"
    ),
    num_requests: int = typer.Option(
        100, "--requests", "-n", help="Number of requests for HTTP benchmarks"
    ),
    concurrent: int = typer.Option(
        10, "--concurrent", "-c", help="Number of concurrent requests"
    ),
    compare_with: Optional[str] = typer.Option(
        None, "--compare", help="Path to previous benchmark file for comparison"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Verbose output"
    ),
) -> None:
    """Run performance benchmarks."""
    try:
        # Validate inputs
        try:
            test_url = InputValidator.validate_url(test_url)
        except ValidationError as e:
            console.print(f"[bold red]Validation Error:[/bold red] {str(e)}")
            sys.exit(1)
        
        if verbose:
            console.print(f"[bold]Running benchmark against:[/bold] {test_url}")
            console.print(f"[bold]Output directory:[/bold] {output_dir}")
            console.print(f"[bold]Benchmark type:[/bold] {benchmark_type}")
        
        # Create benchmark runner
        runner = BenchmarkRunner(output_dir)
        
        # Run benchmarks based on type
        with console.status("[bold green]Running benchmarks...") as status:
            if benchmark_type == "full":
                status.update("[bold green]Running full benchmark suite...")
                suite = runner.run_full_benchmark_suite(test_url)
                
                console.print(f"[green]OK Full benchmark suite completed![/green]")
                console.print(f"[blue]Results saved to:[/blue] {runner.output_dir}")
                
                # Display summary
                console.print("\n[bold]Benchmark Summary:[/bold]")
                summary = suite.summary
                console.print(f"  Total Duration: {summary['total_duration']:.2f}s")
                console.print(f"  Average RPS: {summary['average_requests_per_second']:.2f}")
                console.print(f"  Average Memory: {summary['average_memory_usage_mb']:.2f} MB")
                console.print(f"  Average Success Rate: {summary['average_success_rate']:.1f}%")
                
                if verbose:
                    console.print("\n[bold]Individual Results:[/bold]")
                    for result in suite.results:
                        console.print(f"  {result.name}:")
                        console.print(f"    RPS: {result.requests_per_second:.2f}")
                        console.print(f"    Duration: {result.duration:.2f}s")
                        console.print(f"    Memory: {result.memory_usage_mb:.2f} MB")
                        console.print(f"    Success Rate: {result.success_rate:.1f}%")
                        if result.errors:
                            console.print(f"    Errors: {len(result.errors)}")
                
            elif benchmark_type == "http":
                status.update("[bold green]Running HTTP benchmark...")
                result = runner.run_http_benchmark(test_url, num_requests, concurrent, use_cache=False)
                
                console.print(f"[green]OK HTTP benchmark completed![/green]")
                console.print(f"  RPS: {result.requests_per_second:.2f}")
                console.print(f"  Duration: {result.duration:.2f}s")
                console.print(f"  Success Rate: {result.success_rate:.1f}%")
                console.print(f"  Memory Usage: {result.memory_usage_mb:.2f} MB")
                
            elif benchmark_type == "cache":
                status.update("[bold green]Running cache benchmark...")
                result = runner.run_cache_benchmark(test_url, num_requests)
                
                console.print(f"[green]OK Cache benchmark completed![/green]")
                console.print(f"  RPS: {result.requests_per_second:.2f}")
                console.print(f"  Duration: {result.duration:.2f}s")
                console.print(f"  Cache Hit Rate: {result.metadata.get('cache_hit_rate', 0):.1f}%")
                console.print(f"  Memory Usage: {result.memory_usage_mb:.2f} MB")
                
            elif benchmark_type == "async":
                status.update("[bold green]Running async benchmark...")
                urls = [f"{test_url}?id={i}" for i in range(num_requests)]
                result = asyncio.run(runner.run_async_benchmark(urls, concurrent))
                
                console.print(f"[green]OK Async benchmark completed![/green]")
                console.print(f"  RPS: {result.requests_per_second:.2f}")
                console.print(f"  Duration: {result.duration:.2f}s")
                console.print(f"  Success Rate: {result.success_rate:.1f}%")
                console.print(f"  Memory Usage: {result.memory_usage_mb:.2f} MB")
                
            elif benchmark_type == "memory":
                status.update("[bold green]Running memory stress test...")
                result = runner.run_memory_stress_test(concurrent, num_requests // concurrent, test_url)
                
                console.print(f"[green]OK Memory stress test completed![/green]")
                console.print(f"  RPS: {result.requests_per_second:.2f}")
                console.print(f"  Duration: {result.duration:.2f}s")
                console.print(f"  Peak Memory: {result.memory_usage_mb:.2f} MB")
                console.print(f"  Success Rate: {result.success_rate:.1f}%")
                
            else:
                console.print(f"[bold red]Error:[/bold red] Unknown benchmark type '{benchmark_type}'")
                console.print("Available types: full, http, cache, async, memory")
                sys.exit(1)
        
        # Compare with previous results if requested
        if compare_with and benchmark_type == "full":
            try:
                previous_suite = runner.load_benchmark_suite(compare_with)
                comparison = runner.compare_benchmark_suites(previous_suite, suite)
                
                console.print(f"\n[bold]Comparison with {previous_suite.name}:[/bold]")
                for comp in comparison["comparisons"]:
                    name = comp["benchmark"]
                    rps_change = comp["requests_per_second"]["change_percent"]
                    memory_change = comp["memory_usage_mb"]["change_percent"]
                    
                    rps_color = "green" if rps_change > 0 else "red" if rps_change < 0 else "yellow"
                    memory_color = "green" if memory_change < 0 else "red" if memory_change > 0 else "yellow"
                    
                    console.print(f"  {name}:")
                    console.print(f"    RPS: [{rps_color}]{rps_change:+.1f}%[/{rps_color}]")
                    console.print(f"    Memory: [{memory_color}]{memory_change:+.1f}%[/{memory_color}]")
                
            except Exception as e:
                console.print(f"[yellow]Warning: Could not compare with previous results: {e}[/yellow]")
    
    except Exception as e:
        console.print(f"[bold red]Error running benchmark:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


def _batch_requests(requests, batch_size):
    """Splits request list into batches of given size."""
    for i in range(0, len(requests), batch_size):
        yield requests[i:i + batch_size]


@cli.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context) -> None:
    """Handle call without command specified."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


def _handle_request(
    method: str,
    url: str,
    headers: List[str],
    data: Optional[List[str]],
    query: List[str],
    output: Optional[str],
    timeout: float,
    verbose: bool,
    json_output: bool,
    headers_only: bool,
    curl: bool = False,
    format_output: Optional[str] = None,
    cert: Optional[str] = None,
) -> None:
    """Handle HTTP request and output result."""
    try:
        # Validate inputs
        try:
            url = InputValidator.validate_url(url)
            method = InputValidator.validate_http_method(method)
            timeout = InputValidator.validate_timeout(timeout)
            format_output = InputValidator.validate_output_format(format_output)
            
            # Parse and validate headers, query params, and data
            parsed_headers = InputValidator.validate_headers(headers) if headers else {}
            parsed_query = InputValidator.validate_query_params(query) if query else {}
            
            # Convert parsed data back to lists for RequestBuilder
            if parsed_headers:
                headers = [f"{k}:{v}" for k, v in parsed_headers.items()]
            if parsed_query:
                query = [f"{k}={v}" for k, v in parsed_query.items()]
                
        except ValidationError as e:
            console.print(f"[bold red]Validation Error:[/bold red] {str(e)}")
            sys.exit(1)
        # Load configuration
        config = Config.load_default()
        
        # Create request builder
        builder = RequestBuilder(
            method=method,
            url=url,
            headers=headers,
            data=data or [],
            query=query,
            timeout=timeout,
        )
        
        # Apply settings from configuration
        builder.apply_config(config)
        
        # Build request
        request = builder.build()
        
        # Output curl command if requested
        if curl:
            console.print("[bold]Equivalent curl command:[/bold]")
            curl_command = CurlGenerator.generate_from_request(request)
            CurlGenerator.display_curl(curl_command, console)
            
            # If only curl command needed, exit
            if not verbose:
                return
        
        if verbose:
            console.print(f"[bold]URL:[/bold] {request['url']}")
            console.print("[bold]Method:[/bold]", method)
            
            if request["headers"]:
                console.print("[bold]Headers:[/bold]")
                for key, value in request["headers"].items():
                    console.print(f"  {key}: {value}")
            
            if "json" in request and request["json"]:
                console.print("[bold]JSON:[/bold]")
                formatter = DataFormatter(console=console)
                formatted_json = formatter.format_json(request["json"], colorize=False)
                syntax = Syntax(formatted_json, "json", theme="monokai", word_wrap=True)
                console.print(syntax)
            
            console.print("[bold]Sending request...[/bold]")
        
        # Parse certificate if provided
        cert_config = None
        if cert:
            if ':' in cert:
                # Format: cert_file:key_file
                cert_parts = cert.split(':', 1)
                cert_config = (cert_parts[0], cert_parts[1])
            else:
                # Single .pem file
                cert_config = cert
        
        # Perform request
        client = HttpClient(cert=cert_config)
        response = client.send(request)
        
        # Format and output response with specified format
        if format_output:
            # If specific formatting requested, apply it
            formatter = DataFormatter(console=console)
            content_type = response.headers.get("content-type", "").split(";")[0].strip()
            
            if output:
                # Save formatted output to file
                formatted_content = formatter.format_data(response.text, content_type, format_output)
                with open(output, "w", encoding="utf-8") as f:
                    f.write(formatted_content)
                console.print(f"[green]Formatted response saved to file:[/green] {output}")
            else:
                # Output status and headers
                if not json_output and not headers_only:
                    status_color = "green" if response.status_code < 400 else "red"
                    console.print(f"[bold {status_color}]Status:[/bold {status_color}] {response.status_code} {response.reason_phrase}")
                    console.print(f"[bold]Time:[/bold] {response.elapsed.total_seconds():.3f} sec")
                    console.print()
                
                if headers_only or verbose:
                    console.print("[bold]Response headers:[/bold]")
                    for key, value in response.headers.items():
                        console.print(f"  {key}: {value}")
                    console.print()
                
                if not headers_only:
                    # Output formatted content
                    formatter.display_formatted(response.text, content_type)
        else:
            # Use default response formatter
            format_response(
                response, 
                console=console, 
                verbose=verbose, 
                json_only=json_output, 
                headers_only=headers_only, 
                output_file=output
            )
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


def app() -> None:
    """Entry point for CLI."""
    cli()

if __name__ == "__main__":
    app() 