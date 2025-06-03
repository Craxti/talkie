"""Module for console output formatting."""

from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from httpx import Response
from ..utils.formatter import DataFormatter, format_json, format_xml, format_html
import json

console = Console()

def print_response(
    response: Response, 
    format: str = "json", 
    verbose: bool = False,
    json_only: bool = False,
    headers_only: bool = False,
    output_file: Optional[str] = None,
    format_type: Optional[str] = None
) -> None:
    """Print response to console.
    
    Args:
        response: Server response
        format: Default output format
        verbose: Detailed output
        json_only: Output only JSON
        headers_only: Output only headers
        output_file: File to save response
        format_type: Explicit format type
    """
    formatter = DataFormatter(console=console)
    
    # If only JSON needed, output it and exit
    if json_only and not headers_only:
        try:
            json_data = response.json()
            print(json.dumps(json_data, indent=2, ensure_ascii=False))
            return
        except Exception:
            pass
    
    # Output request information in verbose mode
    if verbose:
        # Table with basic information
        info_table = Table(show_header=False, box=None)
        info_table.add_column("Key", style="bold blue")
        info_table.add_column("Value")
        
        info_table.add_row("URL", str(response.url))
        info_table.add_row("Method", response.request.method)
        info_table.add_row("Status", f"[{'green' if response.status_code < 400 else 'red'}]{response.status_code} {response.reason_phrase}[/]")
        info_table.add_row("Time", f"{response.elapsed.total_seconds():.3f} sec")
        info_table.add_row("Size", f"{len(response.content)} bytes")
        
        console.print(info_table)
        console.print()
        
        # Table with request headers
        if response.request.headers:
            console.print("[bold]Request Headers:[/bold]")
            headers_table = Table(show_header=True, box=True)
            headers_table.add_column("Header", style="bold")
            headers_table.add_column("Value")
            
            for name, value in response.request.headers.items():
                headers_table.add_row(name, str(value))
            
            console.print(headers_table)
            console.print()
        
        # Table with response headers
        if response.headers:
            console.print("[bold]Response Headers:[/bold]")
            headers_table = Table(show_header=True, box=True)
            headers_table.add_column("Header", style="bold")
            headers_table.add_column("Value")
            
            for name, value in response.headers.items():
                headers_table.add_row(name, str(value))
            
            console.print(headers_table)
            console.print()
    
    # If only headers needed, exit
    if headers_only:
        return
    
    # Determine content type
    content_type = response.headers.get("content-type", "").split(";")[0].strip()
    
    # Format and output response body
    if format_type:
        formatted_content = formatter.format_data(response.text, content_type, format_type)
    else:
        formatted_content = formatter.format_data(response.text, content_type, format)
    
    # Save to file or output to console
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(formatted_content)
        console.print(f"[green]Response saved to file:[/green] {output_file}")
    else:
        if json_only:
            try:
                json_data = response.json()
                print(json.dumps(json_data, indent=2, ensure_ascii=False))
            except Exception:
                print(response.text)
        else:
            console.print("[bold]Response Body:[/bold]")
            formatter.display_formatted(response.text, content_type) 