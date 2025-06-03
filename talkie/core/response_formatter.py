"""Module for formatting HTTP responses."""

import json
import mimetypes
from typing import Any, Dict, Optional

import httpx
from rich.console import Console
from rich.highlighter import ReprHighlighter
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text


def format_response(
    response: httpx.Response,
    console: Optional[Console] = None,
    verbose: bool = False,
    json_only: bool = False,
    headers_only: bool = False,
    output_file: Optional[str] = None,
) -> None:
    """Format and display HTTP response.

    Args:
        response: HTTP response object
        console: Rich console for output
        verbose: Show detailed output
        json_only: Show only JSON content
        headers_only: Show only headers
        output_file: Path to save response to file
    """
    if console is None:
        console = Console()
    
    # Save response to file if specified
    if output_file:
        with open(output_file, "wb") as f:
            f.write(response.content)
        console.print(f"[green]Response saved to file:[/green] {output_file}")
        return
    
    # Status and request time
    if not json_only:
        status_color = "green" if response.status_code < 400 else "red"
        status_text = Text(f"{response.status_code} {response.reason_phrase}")
        status_text.stylize(status_color)
        
        table = Table.grid(padding=(0, 1))
        table.add_column(style="bold")
        table.add_column()
        
        table.add_row("Status:", status_text)
        table.add_row("Time:", f"{response.elapsed.total_seconds():.3f} sec")
        table.add_row("Size:", f"{len(response.content)} bytes")
        
        console.print(table)
        console.print()
    
    # Response headers
    if (verbose or headers_only) and not json_only:
        headers_table = Table(title="Response Headers", show_header=True, header_style="bold")
        headers_table.add_column("Header", style="dim")
        headers_table.add_column("Value")
        
        for key, value in response.headers.items():
            headers_table.add_row(key, value)
        
        console.print(headers_table)
        console.print()
    
    # If only headers needed, don't show content
    if headers_only:
        return
    
    # Response content
    try:
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        
        # Handle JSON
        if content_type == "application/json" or (
            response.content and response.content.strip().startswith((b"{", b"["))
        ):
            try:
                json_data = response.json()
                json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
                
                if not verbose and not json_only:
                    console.print("[bold]JSON Response:[/bold]")
                
                syntax = Syntax(json_str, "json", theme="monokai", word_wrap=True)
                console.print(syntax)
            except json.JSONDecodeError:
                if not json_only:
                    console.print("[bold red]Failed to parse JSON response[/bold red]")
                console.print(response.text)
        
        # Handle HTML
        elif content_type == "text/html":
            if not json_only:
                console.print("[bold]HTML Response:[/bold]")
            syntax = Syntax(response.text, "html", theme="monokai", word_wrap=True)
            console.print(syntax)
        
        # Handle XML
        elif content_type in ["application/xml", "text/xml"]:
            if not json_only:
                console.print("[bold]XML Response:[/bold]")
            syntax = Syntax(response.text, "xml", theme="monokai", word_wrap=True)
            console.print(syntax)
        
        # Handle text
        elif content_type.startswith("text/"):
            if not json_only:
                console.print("[bold]Text Response:[/bold]")
            console.print(response.text)
        
        # Binary data
        else:
            if not json_only:
                console.print(f"[bold]Binary data ({content_type}):[/bold]")
                console.print(f"Size: {len(response.content)} bytes")
                console.print("Use --output to save to file")
    
    except Exception as e:
        console.print(f"[bold red]Error processing response:[/bold red] {str(e)}")
        if verbose:
            console.print_exception() 