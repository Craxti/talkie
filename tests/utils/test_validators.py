"""Tests for input validation utilities."""

import pytest
from talkie.utils.validators import InputValidator, ValidationError


class TestInputValidator:
    """Test cases for InputValidator class."""

    def test_validate_url_valid_http(self):
        """Test validation of valid HTTP URL."""
        url = "http://example.com"
        result = InputValidator.validate_url(url)
        assert result == url

    def test_validate_url_valid_https(self):
        """Test validation of valid HTTPS URL."""
        url = "https://api.example.com/v1"
        result = InputValidator.validate_url(url)
        assert result == url

    def test_validate_url_add_http_scheme(self):
        """Test that HTTP scheme is added to URL without scheme."""
        url = "example.com"
        result = InputValidator.validate_url(url)
        assert result == "http://example.com"

    def test_validate_url_empty(self):
        """Test validation of empty URL."""
        with pytest.raises(ValidationError, match="URL cannot be empty"):
            InputValidator.validate_url("")

    def test_validate_url_invalid(self):
        """Test validation of invalid URL."""
        # Test a URL that would result in empty netloc after parsing
        with pytest.raises(ValidationError, match="Invalid URL format"):
            InputValidator.validate_url("http://")  # Just protocol without domain

    def test_validate_timeout_valid(self):
        """Test validation of valid timeout."""
        timeout = 30.0
        result = InputValidator.validate_timeout(timeout)
        assert result == timeout

    def test_validate_timeout_zero(self):
        """Test validation of zero timeout."""
        with pytest.raises(ValidationError, match="Timeout must be positive"):
            InputValidator.validate_timeout(0)

    def test_validate_timeout_negative(self):
        """Test validation of negative timeout."""
        with pytest.raises(ValidationError, match="Timeout must be positive"):
            InputValidator.validate_timeout(-1)

    def test_validate_timeout_too_large(self):
        """Test validation of too large timeout."""
        with pytest.raises(ValidationError, match="Timeout cannot exceed 3600 seconds"):
            InputValidator.validate_timeout(3601)

    def test_validate_headers_valid(self):
        """Test validation of valid headers."""
        headers = ["Content-Type:application/json", "Authorization:Bearer token"]
        result = InputValidator.validate_headers(headers)
        expected = {
            "Content-Type": "application/json",
            "Authorization": "Bearer token"
        }
        assert result == expected

    def test_validate_headers_with_spaces(self):
        """Test validation of headers with extra spaces."""
        headers = [" Content-Type : application/json ", "Authorization:  Bearer token  "]
        result = InputValidator.validate_headers(headers)
        expected = {
            "Content-Type": "application/json",
            "Authorization": "Bearer token"
        }
        assert result == expected

    def test_validate_headers_empty_key(self):
        """Test validation of header with empty key."""
        headers = [" : value"]  # Space followed by colon
        with pytest.raises(ValidationError, match="Empty header key"):
            InputValidator.validate_headers(headers)

    def test_validate_headers_invalid_format(self):
        """Test validation of headers with invalid format."""
        headers = ["invalid-header-without-colon"]
        with pytest.raises(ValidationError, match="Invalid header format"):
            InputValidator.validate_headers(headers)

    def test_validate_query_params_valid(self):
        """Test validation of valid query parameters."""
        params = ["page=1", "limit=10", "sort=name"]
        result = InputValidator.validate_query_params(params)
        expected = {"page": "1", "limit": "10", "sort": "name"}
        assert result == expected

    def test_validate_query_params_with_spaces(self):
        """Test validation of query parameters with spaces."""
        params = [" page = 1 ", "limit=  10  "]
        result = InputValidator.validate_query_params(params)
        expected = {"page": "1", "limit": "10"}
        assert result == expected

    def test_validate_query_params_empty_key(self):
        """Test validation of query parameter with empty key."""
        params = [" = value"]  # Space followed by equals
        with pytest.raises(ValidationError, match="Empty parameter key"):
            InputValidator.validate_query_params(params)

    def test_validate_query_params_invalid_format(self):
        """Test validation of query parameters with invalid format."""
        params = ["invalid-param-without-equals"]
        with pytest.raises(ValidationError, match="Invalid query parameter format"):
            InputValidator.validate_query_params(params)

    def test_validate_data_params_form_data(self):
        """Test validation of form data parameters."""
        data = ["name=John", "age=30"]
        form_data, json_data = InputValidator.validate_data_params(data)
        assert form_data == {"name": "John", "age": "30"}
        assert json_data == {}

    def test_validate_data_params_json_data(self):
        """Test validation of JSON data parameters."""
        data = ["name:=John", "age:=30", "active:=true", "score:=95.5"]
        form_data, json_data = InputValidator.validate_data_params(data)
        assert form_data == {}
        assert json_data == {"name": "John", "age": 30, "active": True, "score": 95.5}

    def test_validate_data_params_mixed(self):
        """Test validation of mixed form and JSON data."""
        data = ["name=John", "age:=30", "active:=true"]
        form_data, json_data = InputValidator.validate_data_params(data)
        assert form_data == {"name": "John"}
        assert json_data == {"age": 30, "active": True}

    def test_validate_data_params_boolean_values(self):
        """Test validation of boolean JSON values."""
        data = ["active:=true", "deleted:=false", "null_value:=null"]
        form_data, json_data = InputValidator.validate_data_params(data)
        assert json_data == {"active": True, "deleted": False, "null_value": None}

    def test_validate_data_params_empty_key(self):
        """Test validation of data parameter with empty key."""
        data = [" = value"]  # Space followed by equals
        with pytest.raises(ValidationError, match="Empty form key"):
            InputValidator.validate_data_params(data)

    def test_validate_data_params_invalid_format(self):
        """Test validation of data parameters with invalid format."""
        data = ["invalid-param"]
        with pytest.raises(ValidationError, match="Invalid data format"):
            InputValidator.validate_data_params(data)

    def test_validate_output_format_valid(self):
        """Test validation of valid output formats."""
        valid_formats = ['json', 'xml', 'html', 'markdown', 'text']
        for fmt in valid_formats:
            result = InputValidator.validate_output_format(fmt)
            assert result == fmt

    def test_validate_output_format_case_insensitive(self):
        """Test validation of output format is case insensitive."""
        result = InputValidator.validate_output_format("JSON")
        assert result == "json"

    def test_validate_output_format_none(self):
        """Test validation of None output format."""
        result = InputValidator.validate_output_format(None)
        assert result is None

    def test_validate_output_format_invalid(self):
        """Test validation of invalid output format."""
        with pytest.raises(ValidationError, match="Invalid output format"):
            InputValidator.validate_output_format("invalid")

    def test_validate_http_method_valid(self):
        """Test validation of valid HTTP methods."""
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        for method in valid_methods:
            result = InputValidator.validate_http_method(method)
            assert result == method

    def test_validate_http_method_case_insensitive(self):
        """Test validation of HTTP method is case insensitive."""
        result = InputValidator.validate_http_method("get")
        assert result == "GET"

    def test_validate_http_method_empty(self):
        """Test validation of empty HTTP method."""
        with pytest.raises(ValidationError, match="HTTP method cannot be empty"):
            InputValidator.validate_http_method("")

    def test_validate_http_method_invalid(self):
        """Test validation of invalid HTTP method."""
        with pytest.raises(ValidationError, match="Invalid HTTP method"):
            InputValidator.validate_http_method("INVALID")
