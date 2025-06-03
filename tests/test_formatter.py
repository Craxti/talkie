import pytest
import json
import xml.etree.ElementTree as ET
from talkie.utils.formatter import (
    format_json, 
    format_xml, 
    format_html, 
    detect_content_type,
    html_to_markdown,
    format_content
)


@pytest.fixture
def sample_json():
    return '{"name": "Test", "value": 123}'


@pytest.fixture
def sample_xml():
    return '<root><item id="1"><name>Test</name><value>123</value></item></root>'


@pytest.fixture
def sample_html():
    return '<html><head><title>Test</title></head><body><h1>Test</h1><p>Content</p></body></html>'


def test_format_json(sample_json):
    """Тест форматирования JSON."""
    formatted = format_json(sample_json)
    # Проверяем, что результат форматирования валидный JSON
    parsed = json.loads(formatted)
    assert parsed["name"] == "Test"
    # Проверяем, что в строке есть отступы (признак форматирования)
    assert "\n" in formatted
    assert "  " in formatted


def test_format_xml(sample_xml):
    """Тест форматирования XML."""
    formatted = format_xml(sample_xml)
    # Проверяем, что результат форматирования валидный XML
    root = ET.fromstring(formatted)
    assert root.tag == "root"
    # Проверяем, что в строке есть отступы (признак форматирования)
    assert "\n" in formatted
    assert "\t" in formatted  # XML форматтер использует табуляцию


def test_format_html(sample_html):
    """Тест форматирования HTML."""
    formatted = format_html(sample_html)
    # Проверяем, что в строке есть отступы (признак форматирования)
    assert "\n" in formatted
    assert "  " in formatted
    # Проверяем базовую структуру HTML
    assert "<html>" in formatted
    assert "</html>" in formatted
    assert "<body>" in formatted
    assert "</body>" in formatted


def test_html_to_markdown(sample_html):
    """Тест преобразования HTML в Markdown."""
    markdown = html_to_markdown(sample_html)
    # Проверяем базовые элементы Markdown
    assert "# Test" in markdown  # <h1> -> #
    assert "Test" in markdown  # содержимое сохранено
    assert "Content" in markdown  # параграф сохранен


def test_detect_content_type():
    """Тест определения типа контента."""
    assert detect_content_type('{"key": "value"}') == "json"
    assert detect_content_type('<root><item>value</item></root>') == "xml"
    assert detect_content_type('<html><head><title>Test</title></head><body>content</body></html>') == "html"
    assert detect_content_type('plain text') == "text"


def test_format_content():
    """Тест автоматического форматирования контента."""
    # JSON
    json_content = '{"name": "Test", "value": 123}'
    assert "name" in format_content(json_content)
    assert "Test" in format_content(json_content)
    
    # XML
    xml_content = '<root><item>value</item></root>'
    formatted_xml = format_content(xml_content)
    assert "<root>" in formatted_xml
    assert "<item>" in formatted_xml
    assert "value" in formatted_xml
    
    # HTML
    html_content = '<html><body><h1>Test</h1></body></html>'
    formatted_html = format_content(html_content)
    assert "<html>" in formatted_html
    assert "<body>" in formatted_html
    assert "<h1>" in formatted_html 