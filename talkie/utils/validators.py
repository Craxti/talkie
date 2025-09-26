"""Input validation utilities for Talkie."""

import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse


class ValidationError(Exception):
    """Custom exception for validation errors."""


# Convenience functions for direct import
def validate_url(url: str) -> str:
    """Validate URL format."""
    return InputValidator.validate_url(url)


def validate_json(data: str) -> Dict[str, Any]:
    """Validate JSON format."""
    return InputValidator.validate_json(data)


class InputValidator:
    """Utility class for validating command line inputs."""

    @staticmethod
    def validate_url(url: str) -> str:
        """
        Validate URL format.

        Args:
            url (str): URL to validate

        Returns:
            str: Validated URL

        Raises:
            ValidationError: If URL is invalid
        """
        if not url:
            raise ValidationError("URL cannot be empty")

        # Add http:// if no scheme provided
        if not url.startswith(('http://', 'https://')):
            url = f'http://{url}'

        parsed = urlparse(url)
        if not parsed.netloc or parsed.netloc == '':
            raise ValidationError(f"Invalid URL format: {url}")

        return url

    @staticmethod
    def validate_timeout(timeout: float) -> float:
        """
        Validate timeout value.

        Args:
            timeout (float): Timeout in seconds

        Returns:
            float: Validated timeout

        Raises:
            ValidationError: If timeout is invalid
        """
        if timeout <= 0:
            raise ValidationError("Timeout must be positive")
        if timeout > 3600:  # 1 hour max
            raise ValidationError("Timeout cannot exceed 3600 seconds (1 hour)")
        return timeout

    @staticmethod
    def validate_headers(headers: List[str]) -> Dict[str, str]:
        """
        Validate and parse header list.

        Args:
            headers (List[str]): Headers in format ['key:value', ...]

        Returns:
            Dict[str, str]: Parsed headers

        Raises:
            ValidationError: If header format is invalid
        """
        parsed_headers = {}
        header_pattern = re.compile(r'^([^:]+):(.*)$')

        for header in headers:
            match = header_pattern.match(header)
            if not match:
                raise ValidationError(
                    f"Invalid header format: '{header}'. Expected format: 'key:value'"
                )

            key, value = match.groups()
            key = key.strip()
            value = value.strip()

            if not key:
                raise ValidationError(f"Empty header key in: '{header}'")

            parsed_headers[key] = value

        return parsed_headers

    @staticmethod
    def validate_query_params(params: List[str]) -> Dict[str, str]:
        """
        Validate and parse query parameters.

        Args:
            params (List[str]): Parameters in format ['key=value', ...]

        Returns:
            Dict[str, str]: Parsed parameters

        Raises:
            ValidationError: If parameter format is invalid
        """
        parsed_params = {}
        param_pattern = re.compile(r'^([^=]+)=(.*)$')

        for param in params:
            match = param_pattern.match(param)
            if not match:
                raise ValidationError(
                    f"Invalid query parameter format: '{param}'. "
                    f"Expected format: 'key=value'"
                )

            key, value = match.groups()
            key = key.strip()
            value = value.strip()

            if not key:
                raise ValidationError(f"Empty parameter key in: '{param}'")

            parsed_params[key] = value

        return parsed_params

    @staticmethod
    def validate_data_params(data: List[str]) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Validate and parse data parameters.

        Args:
            data (List[str]): Data in format ['key=value', 'key:=value']

        Returns:
            tuple: (form_data, json_data)

        Raises:
            ValidationError: If data format is invalid
        """
        form_data = {}
        json_data = {}

        form_pattern = re.compile(r'^([^=]+)=(.*)$')
        json_pattern = re.compile(r'^([^:]+):=(.*)$')

        for item in data:
            # Check for JSON data format (key:=value)
            json_match = json_pattern.match(item)
            if json_match:
                key, value = json_match.groups()
                key = key.strip()
                value = value.strip()

                if not key:
                    raise ValidationError(f"Empty JSON key in: '{item}'")

                # Try to parse JSON value
                try:
                    if value.lower() == 'true':
                        json_data[key] = True
                    elif value.lower() == 'false':
                        json_data[key] = False
                    elif value.lower() == 'null':
                        json_data[key] = None
                    elif value.isdigit():
                        json_data[key] = int(value)
                    elif re.match(r'^\d+\.\d+$', value):
                        json_data[key] = float(value)
                    else:
                        json_data[key] = value
                except ValueError as e:
                    raise ValidationError(
                        f"Invalid JSON value '{value}' for key '{key}': {e}"
                    )
                continue

            # Check for form data format (key=value)
            form_match = form_pattern.match(item)
            if form_match:
                key, value = form_match.groups()
                key = key.strip()
                value = value.strip()

                if not key:
                    raise ValidationError(f"Empty form key in: '{item}'")

                form_data[key] = value
                continue

            # If neither pattern matches
            raise ValidationError(
                f"Invalid data format: '{item}'. "
                f"Expected format: 'key=value' or 'key:=value'"
            )

        return form_data, json_data

    @staticmethod
    def validate_output_format(format_name: Optional[str]) -> Optional[str]:
        """
        Validate output format.

        Args:
            format_name (Optional[str]): Format name

        Returns:
            Optional[str]: Validated format name

        Raises:
            ValidationError: If format is invalid
        """
        if format_name is None:
            return None

        valid_formats = {'json', 'xml', 'html', 'markdown', 'text'}
        format_name = format_name.lower()

        if format_name not in valid_formats:
            raise ValidationError(
                f"Invalid output format: '{format_name}'. "
                f"Valid formats: {', '.join(sorted(valid_formats))}"
            )

        return format_name

    @staticmethod
    def validate_http_method(method: str) -> str:
        """
        Validate HTTP method.

        Args:
            method (str): HTTP method

        Returns:
            str: Validated method in uppercase

        Raises:
            ValidationError: If method is invalid
        """
        if not method:
            raise ValidationError("HTTP method cannot be empty")

        method = method.upper()
        valid_methods = {
            'GET', 'POST', 'PUT', 'DELETE', 'PATCH',
            'HEAD', 'OPTIONS', 'TRACE', 'CONNECT'
        }

        if method not in valid_methods:
            raise ValidationError(
                f"Invalid HTTP method: '{method}'. "
                f"Valid methods: {', '.join(sorted(valid_methods))}"
            )

        return method

    @staticmethod
    def validate_json(data: str) -> Dict[str, Any]:
        """
        Validate JSON format.

        Args:
            data (str): JSON string

        Returns:
            Dict[str, Any]: Parsed JSON data

        Raises:
            ValidationError: If JSON is invalid
        """
        try:
            import json
            return json.loads(data)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON format: {e}")
