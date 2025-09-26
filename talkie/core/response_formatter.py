"""Response formatter for HTTP responses."""

import json
from typing import Dict, Any


class ResponseFormatter:
    """Formatter for HTTP responses."""

    def __init__(self):
        self.formatters = {
            'json': self._format_json,
            'xml': self._format_xml,
            'html': self._format_html,
            'text': self._format_text
        }

    def format_response(self, response: Dict[str, Any],
                        format_type: str = 'text') -> str:
        """Format response data."""
        formatter = self.formatters.get(format_type, self._format_text)
        return formatter(response)

    def _format_json(self, response: Dict[str, Any]) -> str:
        """Format as JSON."""
        return json.dumps(response, indent=2)

    def _format_xml(self, response: Dict[str, Any]) -> str:
        """Format as XML."""
        return f"<response><status>{response.get('status', '')}</status></response>"

    def _format_html(self, response: Dict[str, Any]) -> str:
        """Format as HTML."""
        status = response.get('status', '')
        return f"<html><body><h1>Status: {status}</h1></body></html>"

    def _format_text(self, response: Dict[str, Any]) -> str:
        """Format as plain text."""
        return f"Status: {response.get('status', '')}\nBody: {response.get('body', '')}"
