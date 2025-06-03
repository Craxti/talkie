"""Main CLI module for Talkie."""

import sys
import asyncio
import os
from typing import Any, Dict, List, Optional, Union

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
) -> None:
    """Perform GET request to specified URL."""
    _handle_request("GET", url, header, None, query, output, timeout, verbose, json_output, headers_only, curl, format_output)


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
) -> None:
    """Handle HTTP request and output result."""
    try:
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
        
        # Perform request
        client = HttpClient()
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