"""Module for auto-formatting various data types."""

import html
import json
import re
from typing import Any, Dict, Optional, Union

import html2text
import xmltodict
from pygments import formatters, highlight, lexers
from rich.console import Console
from rich.syntax import Syntax


class DataFormatter:
    """Class for formatting various data types."""

    def __init__(self, console: Optional[Console] = None) -> None:
        """Initialize data formatter.

        Args:
            console: Rich console for output
        """
        self.console = console or Console()
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.ignore_tables = False
        self.html_converter.body_width = 0  # Don't limit text width

    def format_json(self, data: Union[str, Dict[str, Any]], colorize: bool = True) -> str:
        """Format JSON data with indentation and highlighting.

        Args:
            data: JSON string or dictionary
            colorize: Use color highlighting

        Returns:
            str: Formatted JSON
        """
        # Convert string to dictionary
        if isinstance(data, str):
            try:
                json_obj = json.loads(data)
            except json.JSONDecodeError:
                # If parsing fails, return original string
                return data
        else:
            json_obj = data

        # Format JSON with indentation
        formatted_json = json.dumps(json_obj, indent=2, ensure_ascii=False, sort_keys=True)

        # Syntax highlighting
        if colorize:
            lexer = lexers.JsonLexer()
            formatter = formatters.TerminalFormatter()
            return highlight(formatted_json, lexer, formatter)

        return formatted_json

    def format_xml(self, data: str, colorize: bool = True) -> str:
        """Format XML data with indentation and highlighting.

        Args:
            data: XML string
            colorize: Use color highlighting

        Returns:
            str: Formatted XML
        """
        try:
            # Convert XML to dictionary and back for formatting
            xml_dict = xmltodict.parse(data)
            formatted_xml = xmltodict.unparse(xml_dict, pretty=True)

            # Syntax highlighting
            if colorize:
                lexer = lexers.XmlLexer()
                formatter = formatters.TerminalFormatter()
                return highlight(formatted_xml, lexer, formatter)

            return formatted_xml
        except Exception:
            # In case of error, return original string
            return data

    def format_html(self, data: str, to_markdown: bool = False, colorize: bool = True) -> str:
        """Format HTML data with indentation and highlighting.

        Args:
            data: HTML string
            to_markdown: Convert HTML to Markdown
            colorize: Use color highlighting

        Returns:
            str: Formatted HTML or Markdown
        """
        if to_markdown:
            # Convert HTML to Markdown
            return self.html_converter.handle(data)

        # Try formatting HTML with indentation
        try:
            # Simple formatting of tags with indentation
            formatted_html = self._format_html_tags(data)

            # Syntax highlighting
            if colorize:
                lexer = lexers.HtmlLexer()
                formatter = formatters.TerminalFormatter()
                return highlight(formatted_html, lexer, formatter)

            return formatted_html
        except Exception:
            # In case of error, return original string
            return data

    def _format_html_tags(self, html_str: str) -> str:
        """Format HTML tags with indentation.

        Args:
            html_str: HTML string

        Returns:
            str: Formatted HTML
        """
        result = []
        indent = 0
        lines = html_str.split(">")

        for line in lines:
            if not line:
                continue

            # Add closing symbol, except for the last line
            line = line.strip() + (">" if line != lines[-1] else "")

            # Check if the tag is closed on this line
            if line.startswith("</"):
                indent -= 1

            # Add indentation
            if line:
                result.append(" " * (2 * indent) + line)

            # Check if a new tag is opened
            # Проверяем, открывается ли новый тег
            if not line.startswith("</") and not line.endswith("/>") and "</" not in line and line.startswith("<"):
                indent += 1

        return "\n".join(result)

    def display_formatted(self, data: str, content_type: str) -> None:
        """Отобразить отформатированные данные с подсветкой синтаксиса.

        Args:
            data: Содержимое для отображения
            content_type: MIME-тип содержимого
        """
        if content_type == "application/json" or (
            data and data.strip().startswith(("{", "[")) and data.strip().endswith(("]", "}"))
        ):
            # JSON
            try:
                json_obj = json.loads(data)
                syntax = Syntax(
                    json.dumps(json_obj, indent=2, ensure_ascii=False, sort_keys=True),
                    "json",
                    theme="monokai",
                    word_wrap=True,
                )
                self.console.print(syntax)
            except json.JSONDecodeError:
                # Не JSON, выводим как есть
                self.console.print(data)
        
        elif content_type in ["application/xml", "text/xml"] or (
            data and data.strip().startswith("<") and data.strip().endswith(">")
        ):
            # XML
            try:
                formatted_xml = self.format_xml(data, colorize=False)
                syntax = Syntax(formatted_xml, "xml", theme="monokai", word_wrap=True)
                self.console.print(syntax)
            except Exception:
                self.console.print(data)
        
        elif content_type == "text/html":
            # HTML
            try:
                formatted_html = self._format_html_tags(data)
                syntax = Syntax(formatted_html, "html", theme="monokai", word_wrap=True)
                self.console.print(syntax)
            except Exception:
                self.console.print(data)
        
        else:
            # Другое содержимое
            self.console.print(data)

    def format_data(self, data: str, content_type: str, format_type: Optional[str] = None) -> str:
        """Автоматически форматировать данные в зависимости от типа.

        Args:
            data: Содержимое для форматирования
            content_type: MIME-тип содержимого
            format_type: Явное указание типа форматирования (json, xml, html, markdown)

        Returns:
            str: Отформатированные данные
        """
        if format_type == "json" or content_type == "application/json" or (
            data and data.strip().startswith(("{", "[")) and data.strip().endswith(("]", "}"))
        ):
            return self.format_json(data)
        
        elif format_type == "xml" or content_type in ["application/xml", "text/xml"] or (
            data and data.strip().startswith("<") and data.strip().endswith(">") and "?xml" in data
        ):
            return self.format_xml(data)
        
        elif format_type == "html" or content_type == "text/html" or (
            data and data.strip().startswith("<") and data.strip().endswith(">") and ("<html" in data or "</html>" in data)
        ):
            return self.format_html(data)
        
        elif format_type == "markdown" and content_type == "text/html":
            return self.format_html(data, to_markdown=True)
        
        # Возвращаем данные как есть
        return data 

# Создаем глобальный экземпляр форматтера
_formatter = DataFormatter()

def format_json(data: Union[str, Dict[str, Any]], colorize: bool = False) -> str:
    """Форматировать JSON-данные с отступами и подсветкой."""
    return _formatter.format_json(data, colorize)

def format_xml(data: str, colorize: bool = False) -> str:
    """Форматировать XML-данные с отступами и подсветкой."""
    return _formatter.format_xml(data, colorize)

def format_html(data: str, to_markdown: bool = False, colorize: bool = False) -> str:
    """Форматировать HTML-данные с отступами и подсветкой."""
    return _formatter.format_html(data, to_markdown, colorize)

def display_formatted(data: str, content_type: str) -> None:
    """Отобразить отформатированные данные с подсветкой синтаксиса."""
    _formatter.display_formatted(data, content_type)

def format_data(data: str, content_type: str, format_type: Optional[str] = None) -> str:
    """Автоматически форматировать данные в зависимости от типа."""
    return _formatter.format_data(data, content_type, format_type)

def detect_content_type(content: str) -> str:
    """Определить тип контента на основе его содержимого.
    
    Args:
        content: Строка с содержимым
        
    Returns:
        str: Тип контента ('json', 'xml', 'html' или 'text')
    """
    content = content.strip()
    
    # Проверяем JSON
    if content.startswith(("{", "[")) and content.endswith(("}", "]")):
        try:
            json.loads(content)
            return "json"
        except json.JSONDecodeError:
            pass
    
    # Проверяем HTML
    if content.startswith("<") and content.endswith(">"):
        # Сначала проверяем HTML-специфичные теги
        if re.search(r"<html.*?>|<body.*?>|<head.*?>|<!DOCTYPE\s+html.*?>", content, re.IGNORECASE):
            return "html"
        # Если не HTML, пробуем XML
        try:
            xmltodict.parse(content)
            return "xml"
        except Exception:
            # Если не удалось разобрать как XML, считаем что это HTML
            if "<" in content and ">" in content:
                return "html"
    
    return "text"

def html_to_markdown(content: str) -> str:
    """Преобразовать HTML в Markdown.
    
    Args:
        content: HTML-строка
        
    Returns:
        str: Markdown-строка
    """
    return _formatter.format_html(content, to_markdown=True)

def format_content(content: str, content_type: Optional[str] = None) -> str:
    """Форматировать содержимое с автоопределением типа.
    
    Args:
        content: Строка с содержимым
        content_type: Тип содержимого (опционально)
        
    Returns:
        str: Отформатированное содержимое
    """
    # Определяем тип контента, если не указан
    if not content_type:
        content_type = detect_content_type(content)
    
    # Форматируем в зависимости от типа
    if content_type == "json":
        return format_json(content)
    elif content_type == "xml":
        return format_xml(content)
    elif content_type == "html":
        return format_html(content)
    else:
        return content 