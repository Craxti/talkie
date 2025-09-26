"""Module for managing request history."""

import csv
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, NamedTuple
from pathlib import Path


class RequestData(NamedTuple):
    """Data structure for request information."""
    method: str
    url: str
    headers: Optional[Dict[str, str]] = None
    data: Optional[Any] = None
    response_status: Optional[int] = None
    response_time: Optional[float] = None


class HistoryManager:
    """Manager for request history."""

    def __init__(self, history_file: Optional[str] = None):
        """Initialize history manager.

        Args:
            history_file: Path to history file
        """
        if history_file:
            self.history_file = Path(history_file)
        else:
            # Default history file location
            history_dir = Path.home() / ".talkie"
            history_dir.mkdir(exist_ok=True)
            self.history_file = history_dir / "history.json"

        self.history: List[Dict[str, Any]] = []
        self.load_history()

    def load_history(self) -> None:
        """Load history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.history = []

    def save_history(self) -> None:
        """Save history to file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except IOError:
            pass  # If we can't save, continue without error

    def add_request(self, request_data: RequestData) -> None:
        """Add request to history.

        Args:
            request_data: Request data structure
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "method": request_data.method,
            "url": request_data.url,
            "headers": request_data.headers or {},
            "data": request_data.data,
            "response_status": request_data.response_status,
            "response_time": request_data.response_time
        }

        self.history.append(entry)

        # Keep only last 1000 entries
        if len(self.history) > 1000:
            self.history = self.history[-1000:]

        self.save_history()

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get request history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List[Dict[str, Any]]: History entries
        """
        if limit:
            return self.history[-limit:]
        return self.history.copy()

    def search_history(
        self,
        method: Optional[str] = None,
        url_pattern: Optional[str] = None,
        status_code: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search history by criteria.

        Args:
            method: HTTP method to filter by
            url_pattern: URL pattern to filter by
            status_code: Status code to filter by

        Returns:
            List[Dict[str, Any]]: Matching history entries
        """
        results = []

        for entry in self.history:
            match = True

            if method and entry.get("method") != method:
                match = False

            if url_pattern and url_pattern not in entry.get("url", ""):
                match = False

            if status_code and entry.get("response_status") != status_code:
                match = False

            if match:
                results.append(entry)

        return results

    def clear_history(self) -> None:
        """Clear all history."""
        self.history = []
        self.save_history()

    def export_history(self, output_file: str, export_format: str = "json") -> None:
        """Export history to file.

        Args:
            output_file: Output file path
            format: Export format (json, csv)
        """
        if export_format == "json":
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        elif export_format == "csv":
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                if self.history:
                    writer = csv.DictWriter(f, fieldnames=self.history[0].keys())
                    writer.writeheader()
                    writer.writerows(self.history)

    def get_stats(self) -> Dict[str, Any]:
        """Get history statistics.

        Returns:
            Dict[str, Any]: Statistics data
        """
        if not self.history:
            return {}

        methods = {}
        status_codes = {}
        total_time = 0
        response_times = []

        for entry in self.history:
            # Count methods
            method = entry.get("method", "UNKNOWN")
            methods[method] = methods.get(method, 0) + 1

            # Count status codes
            status = entry.get("response_status")
            if status:
                status_codes[status] = status_codes.get(status, 0) + 1

            # Collect response times
            response_time = entry.get("response_time")
            if response_time:
                response_times.append(response_time)
                total_time += response_time

        avg_response_time = total_time / len(response_times) if response_times else 0

        return {
            "total_requests": len(self.history),
            "methods": methods,
            "status_codes": status_codes,
            "average_response_time": avg_response_time,
            "fastest_response": min(response_times) if response_times else 0,
            "slowest_response": max(response_times) if response_times else 0
        }


# Global history manager instance
_HISTORY_MANAGER = None


def get_history_manager() -> HistoryManager:
    """Get global history manager instance.

    Returns:
        HistoryManager: Global history manager
    """
    global _HISTORY_MANAGER
    if _HISTORY_MANAGER is None:
        _HISTORY_MANAGER = HistoryManager()
    return _HISTORY_MANAGER


def add_to_history(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Any] = None,
    response_status: Optional[int] = None,
    response_time: Optional[float] = None
) -> None:
    """Add request to global history.

    Args:
        method: HTTP method
        url: Request URL
        headers: Request headers
        data: Request data
        response_status: Response status code
        response_time: Response time in seconds
    """
    manager = get_history_manager()
    request_data = RequestData(
        method=method,
        url=url,
        headers=headers,
        data=data,
        response_status=response_status,
        response_time=response_time
    )
    manager.add_request(request_data)


def get_recent_requests(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent requests from history.

    Args:
        limit: Maximum number of requests to return

    Returns:
        List[Dict[str, Any]]: Recent requests
    """
    manager = get_history_manager()
    return manager.get_history(limit)


def search_requests(
    method: Optional[str] = None,
    url_pattern: Optional[str] = None,
    status_code: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Search requests in history.

    Args:
        method: HTTP method to filter by
        url_pattern: URL pattern to filter by
        status_code: Status code to filter by

    Returns:
        List[Dict[str, Any]]: Matching requests
    """
    manager = get_history_manager()
    return manager.search_history(method, url_pattern, status_code)
