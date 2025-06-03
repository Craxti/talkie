"""
Module for saving and managing HTTP request history.

Provides functionality for saving, loading, and managing HTTP request history,
including metadata, headers, parameters, and request bodies, as well as responses.
"""

import os
import json
import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import uuid
from pydantic import BaseModel, Field


class RequestRecord(BaseModel):
    """
    Model for storing data about executed HTTP request.
    
    Attributes:
        id (str): Unique request identifier.
        method (str): HTTP method (GET, POST, PUT, DELETE etc.).
        url (str): Request URL.
        headers (Dict[str, str]): Request headers.
        query_params (Dict[str, str]): Query string parameters.
        body (Optional[Any]): Request body (if any).
        response_status (Optional[int]): Response status code.
        response_headers (Optional[Dict[str, str]]): Response headers.
        response_body (Optional[Any]): Response body.
        timestamp (datetime.datetime): Request execution time.
        duration_ms (int): Request execution duration in milliseconds.
        environment (Optional[str]): Environment name where request was executed.
        tags (List[str]): User tags for request.
        notes (Optional[str]): Additional notes.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    method: str
    url: str
    headers: Dict[str, str] = {}
    query_params: Dict[str, str] = {}
    body: Optional[Any] = None
    response_status: Optional[int] = None
    response_headers: Optional[Dict[str, str]] = None
    response_body: Optional[Any] = None
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    duration_ms: int = 0
    environment: Optional[str] = None
    tags: List[str] = []
    notes: Optional[str] = None


class RequestHistory:
    """
    Class for managing HTTP request history.
    
    Provides methods for saving, loading, searching, and managing request history.
    History is stored in a JSON file.
    
    Attributes:
        history_file (Path): Path to history file.
        max_records (int): Maximum number of records to store.
        records (List[RequestRecord]): List of request records.
        
    Examples:
        >>> history = RequestHistory("requests.json")
        >>> record = RequestRecord(
        ...     method="GET",
        ...     url="https://api.example.com/users",
        ...     headers={"Authorization": "Bearer token"},
        ...     response_status=200
        ... )
        >>> history.add_record(record)
        >>> found = history.search(method="GET", status_range=(200, 299))
    """
    
    def __init__(self, history_file: Union[str, Path], max_records: int = 1000):
        """
        Initialize request history.
        
        Args:
            history_file (Union[str, Path]): Path to history file.
            max_records (int): Maximum number of records to store.
        """
        self.history_file = Path(history_file)
        self.max_records = max_records
        self.records: List[RequestRecord] = []
        
        # Load history if file exists
        if self.history_file.exists():
            self.load()
    
    def save(self) -> None:
        """Save history to file."""
        # Create directory if it doesn't exist
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert records to dictionaries
        data = [record.model_dump() for record in self.records]
        
        # Save to file
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                default=self._json_serializer,
                ensure_ascii=False,
                indent=2
            )
    
    def add_record(self, record: RequestRecord) -> str:
        """
        Add new record to history and save changes.
        
        Args:
            record (RequestRecord): Record to add.
            
        Returns:
            str: Added record ID.
        """
        # Add record to beginning of list (so newest are first)
        self.records.insert(0, record)
        
        # Trim history if limit exceeded
        if len(self.records) > self.max_records:
            self.records = self.records[:self.max_records]
        
        # Save changes
        self.save()
        
        return record.id
    
    def get_record(self, record_id: str) -> Optional[RequestRecord]:
        """
        Get record by ID.
        
        Args:
            record_id (str): Record ID.
            
        Returns:
            Optional[RequestRecord]: Found record or None if not found.
        """
        for record in self.records:
            if record.id == record_id:
                return record
        return None
    
    def delete_record(self, record_id: str) -> bool:
        """
        Delete record from history.
        
        Args:
            record_id (str): Record ID.
            
        Returns:
            bool: True if record was successfully deleted, False otherwise.
        """
        initial_length = len(self.records)
        self.records = [record for record in self.records if record.id != record_id]
        
        if len(self.records) < initial_length:
            self.save()
            return True
        
        return False
    
    def clear(self) -> None:
        """Clear all request history."""
        self.records = []
        self.save()
    
    def search(
        self,
        query: Optional[str] = None,
        method: Optional[str] = None,
        url_pattern: Optional[str] = None,
        status_range: Optional[tuple[int, int]] = None,
        time_range: Optional[tuple[datetime.datetime, datetime.datetime]] = None,
        environment: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[RequestRecord]:
        """
        Search records by specified criteria.
        
        Args:
            query (Optional[str]): Text search in URL and body.
            method (Optional[str]): Filter by HTTP method.
            url_pattern (Optional[str]): URL pattern for filtering.
            status_range (Optional[tuple[int, int]]): Status code range.
            time_range (Optional[tuple[datetime.datetime, datetime.datetime]]): 
                Execution time range.
            environment (Optional[str]): Filter by environment.
            tags (Optional[List[str]]): Filter by tags.
            limit (Optional[int]): Maximum number of results.
            
        Returns:
            List[RequestRecord]: List of records matching criteria.
        """
        results = []
        
        for record in self.records:
            # Filter by HTTP method
            if method and record.method.upper() != method.upper():
                continue
            
            # Filter by URL
            if url_pattern and url_pattern.lower() not in record.url.lower():
                continue
            
            # Filter by status code
            if status_range and (
                record.response_status is None or 
                not (status_range[0] <= record.response_status <= status_range[1])
            ):
                continue
            
            # Filter by execution time
            if time_range and not (time_range[0] <= record.timestamp <= time_range[1]):
                continue
            
            # Filter by environment
            if environment and record.environment != environment:
                continue
            
            # Filter by tags
            if tags and not all(tag in record.tags for tag in tags):
                continue
            
            # Text search
            if query:
                query_lower = query.lower()
                if (
                    query_lower not in record.url.lower() and
                    not self._search_in_body(record.body, query_lower) and
                    not self._search_in_body(record.response_body, query_lower)
                ):
                    continue
            
            results.append(record)
            
            # Limit number of results
            if limit and len(results) >= limit:
                break
        
        return results
    
    def _json_serializer(self, obj: Any) -> str:
        """JSON serializer for objects not serializable by default json code."""
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    def load(self) -> None:
        """Load request history from file."""
        if not self.history_file.exists():
            self.records = []
            return
        
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Convert dictionaries to RequestRecord objects
            self.records = []
            for item in data:
                # Convert string timestamp to datetime
                if "timestamp" in item and isinstance(item["timestamp"], str):
                    try:
                        item["timestamp"] = datetime.datetime.fromisoformat(item["timestamp"])
                    except ValueError:
                        item["timestamp"] = datetime.datetime.now()
                
                self.records.append(RequestRecord(**item))
        except Exception as e:
            print(f"Error loading history: {e}")
            self.records = []
    
    def export_to_file(self, file_path: str) -> bool:
        """
        Export history to specified file.
        
        Args:
            file_path (str): Path to export file.
            
        Returns:
            bool: True if export successful, False otherwise.
        """
        try:
            data = [record.model_dump() for record in self.records]
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(
                    data,
                    f,
                    default=self._json_serializer,
                    ensure_ascii=False,
                    indent=2
                )
            return True
        except Exception as e:
            print(f"Error exporting history: {e}")
            return False
    
    def import_from_file(self, file_path: str, replace: bool = False) -> bool:
        """
        Import history from file.
        
        Args:
            file_path (str): Path to import file.
            replace (bool): Whether to replace existing history.
            
        Returns:
            bool: True if import successful, False otherwise.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Convert dictionaries to RequestRecord objects
            imported_records = []
            for item in data:
                # Convert string timestamp to datetime
                if "timestamp" in item and isinstance(item["timestamp"], str):
                    try:
                        item["timestamp"] = datetime.datetime.fromisoformat(item["timestamp"])
                    except ValueError:
                        item["timestamp"] = datetime.datetime.now()
                
                imported_records.append(RequestRecord(**item))
            
            # Replace or merge records
            if replace:
                self.records = imported_records
            else:
                # Add new records at beginning
                self.records = imported_records + self.records
                
                # Trim if needed
                if len(self.records) > self.max_records:
                    self.records = self.records[:self.max_records]
            
            self.save()
            return True
        except Exception as e:
            print(f"Error importing history: {e}")
            return False
    
    def _search_in_body(self, body: Any, query: str) -> bool:
        """
        Search string in request or response body.
        
        Args:
            body (Any): Body to search in.
            query (str): String to search for.
            
        Returns:
            bool: True if string found, False otherwise.
        """
        if body is None:
            return False
        
        if isinstance(body, str):
            return query in body.lower()
        
        if isinstance(body, dict) or isinstance(body, list):
            # Convert to JSON string and search
            try:
                body_str = json.dumps(body, ensure_ascii=False).lower()
                return query in body_str
            except:
                pass
        
        # Try to convert to string and search
        try:
            return query in str(body).lower()
        except:
            pass
        
        return False 