"""Tests for formatter module."""

import json
import pytest
from unittest.mock import Mock, patch
from talkie.utils.formatter import DataFormatter


class TestDataFormatter:
    """Test data formatter."""
    
    def test_formatter_initialization(self):
        """Test formatter initialization."""
        formatter = DataFormatter()
        assert formatter.console is not None
        assert formatter.html_converter is not None

    def test_format_json_string(self):
        """Test formatting JSON string."""
        formatter = DataFormatter()
        json_string = '{"name": "test", "value": 123}'
        
        result = formatter.format_json(json_string)
        assert isinstance(result, str)
        assert "name" in result
        assert "test" in result
        assert "value" in result
        assert "123" in result

    def test_format_json_dict(self):
        """Test formatting JSON dictionary."""
        formatter = DataFormatter()
        data = {"name": "test", "value": 123, "nested": {"key": "value"}}
        
        result = formatter.format_json(data)
        assert isinstance(result, str)
        assert "name" in result
        assert "test" in result
        assert "nested" in result

    def test_format_json_invalid_string(self):
        """Test formatting invalid JSON string."""
        formatter = DataFormatter()
        invalid_json = '{"name": "test", "value": 123'  # Missing closing brace
        
        result = formatter.format_json(invalid_json)
        assert result == invalid_json  # Should return original string

    def test_format_json_without_colorize(self):
        """Test formatting JSON without colorization."""
        formatter = DataFormatter()
        data = {"name": "test", "value": 123}
        
        result = formatter.format_json(data, colorize=False)
        assert isinstance(result, str)
        assert "name" in result

    def test_format_xml(self):
        """Test formatting XML."""
        formatter = DataFormatter()
        xml_string = '<?xml version="1.0"?><root><item>test</item></root>'
        
        result = formatter.format_xml(xml_string)
        assert isinstance(result, str)
        assert "root" in result
        assert "item" in result
        assert "test" in result

    def test_format_xml_invalid(self):
        """Test formatting invalid XML."""
        formatter = DataFormatter()
        invalid_xml = '<root><item>test</item>'  # Missing closing tag
        
        result = formatter.format_xml(invalid_xml)
        assert result == invalid_xml  # Should return original string

    def test_format_html(self):
        """Test formatting HTML."""
        formatter = DataFormatter()
        html_string = '<html><body><h1>Title</h1><p>Content</p></body></html>'
        
        result = formatter.format_html(html_string)
        assert isinstance(result, str)
        # HTML should be converted to text
        assert "Title" in result
        assert "Content" in result

    def test_format_html_with_links(self):
        """Test formatting HTML with links."""
        formatter = DataFormatter()
        html_string = '<html><body><a href="https://example.com">Link</a></body></html>'
        
        result = formatter.format_html(html_string)
        assert isinstance(result, str)
        assert "Link" in result

    def test_format_yaml(self):
        """Test formatting YAML."""
        formatter = DataFormatter()
        yaml_string = "name: test\nvalue: 123\nnested:\n  key: value"
        
        result = formatter.format_yaml(yaml_string)
        assert isinstance(result, str)
        assert "name" in result
        assert "test" in result
        assert "value" in result

    def test_format_yaml_invalid(self):
        """Test formatting invalid YAML."""
        formatter = DataFormatter()
        invalid_yaml = "name: test\nvalue: 123\nnested:\n  key: value\n  invalid_indentation"
        
        result = formatter.format_yaml(invalid_yaml)
        assert result == invalid_yaml  # Should return original string

    def test_format_sql(self):
        """Test formatting SQL."""
        formatter = DataFormatter()
        sql_string = "SELECT * FROM users WHERE id = 1 AND name = 'test'"
        
        result = formatter.format_sql(sql_string)
        assert isinstance(result, str)
        assert "SELECT" in result
        assert "FROM" in result
        assert "users" in result

    def test_format_sql_multiline(self):
        """Test formatting multiline SQL."""
        formatter = DataFormatter()
        sql_string = """
        SELECT u.id, u.name, p.title
        FROM users u
        JOIN posts p ON u.id = p.user_id
        WHERE u.active = 1
        """
        
        result = formatter.format_sql(sql_string)
        assert isinstance(result, str)
        assert "SELECT" in result
        assert "FROM" in result
        assert "JOIN" in result

    def test_format_auto_detection(self):
        """Test automatic format detection."""
        formatter = DataFormatter()
        
        # Test JSON detection
        json_data = '{"name": "test"}'
        result = formatter.format_auto(json_data)
        assert isinstance(result, str)
        
        # Test XML detection
        xml_data = '<root><item>test</item></root>'
        result = formatter.format_auto(xml_data)
        assert isinstance(result, str)
        
        # Test HTML detection
        html_data = '<html><body>test</body></html>'
        result = formatter.format_auto(html_data)
        assert isinstance(result, str)

    def test_format_auto_unknown(self):
        """Test automatic format detection with unknown format."""
        formatter = DataFormatter()
        unknown_data = "This is just plain text"
        
        result = formatter.format_auto(unknown_data)
        assert result == unknown_data  # Should return original string

    def test_format_with_console(self):
        """Test formatting with custom console."""
        mock_console = Mock()
        formatter = DataFormatter(console=mock_console)
        
        data = {"name": "test"}
        result = formatter.format_json(data)
        
        assert formatter.console == mock_console

    def test_html_converter_configuration(self):
        """Test HTML converter configuration."""
        formatter = DataFormatter()
        
        # Check that HTML converter is properly configured
        assert formatter.html_converter.ignore_links is False
        assert formatter.html_converter.ignore_images is False
        assert formatter.html_converter.ignore_tables is False
        assert formatter.html_converter.body_width == 0
