"""Тесты для модуля построения запросов."""

import json
import pytest

from talkie.core.request_builder import RequestBuilder
from talkie.utils.config import Config, Environment


def test_request_builder_init():
    """Тест инициализации RequestBuilder."""
    builder = RequestBuilder(
        method="GET",
        url="https://example.com/api"
    )
    
    assert builder.method == "GET"
    assert builder.url == "https://example.com/api"
    assert builder.headers == {}
    assert builder.data == {}
    assert builder.json_data == {}
    assert builder.query_params == {}


def test_parse_headers():
    """Тест разбора заголовков."""
    headers = [
        "Content-Type: application/json",
        "Authorization: Bearer token123",
        "X-Custom-Header: value"
    ]
    
    builder = RequestBuilder(
        method="GET",
        url="https://example.com/api",
        headers=headers
    )
    
    assert builder.headers == {
        "Content-Type": "application/json",
        "Authorization": "Bearer token123",
        "X-Custom-Header": "value"
    }


def test_parse_data():
    """Тест разбора данных формы."""
    data = [
        "username=testuser",
        "password=password123",
        "remember=true"
    ]
    
    builder = RequestBuilder(
        method="POST",
        url="https://example.com/api/login",
        data=data
    )
    
    assert builder.data == {
        "username": "testuser",
        "password": "password123",
        "remember": "true"
    }
    assert builder.json_data == {}


def test_parse_json_data():
    """Тест разбора JSON-данных."""
    data = [
        "age:=30",
        "is_admin:=true",
        "skills:=[\"python\", \"javascript\"]",
        "profile:={\"title\": \"Developer\", \"level\": 5}"
    ]
    
    builder = RequestBuilder(
        method="POST",
        url="https://example.com/api/users",
        data=data
    )
    
    assert builder.json_data == {
        "age": 30,
        "is_admin": True,
        "skills": ["python", "javascript"],
        "profile": {"title": "Developer", "level": 5}
    }


def test_parse_query():
    """Тест разбора параметров запроса."""
    query = [
        "page=1",
        "limit=10",
        "sort=name",
        "order=asc"
    ]
    
    builder = RequestBuilder(
        method="GET",
        url="https://example.com/api/users",
        query=query
    )
    
    assert builder.query_params == {
        "page": "1",
        "limit": "10",
        "sort": "name",
        "order": "asc"
    }


def test_apply_config():
    """Тест применения конфигурации."""
    # Создаем конфигурацию с заголовками по умолчанию
    config = Config(
        default_headers={
            "User-Agent": "Talkie/0.1.0",
            "Accept": "application/json"
        }
    )
    
    # Создаем построитель с некоторыми заголовками
    builder = RequestBuilder(
        method="GET",
        url="https://example.com/api",
        headers=["Authorization: Bearer token123"]
    )
    
    # Применяем конфигурацию
    builder.apply_config(config)
    
    # Проверяем, что заголовки из конфигурации добавлены,
    # но не перезаписывают существующие
    assert builder.headers == {
        "Authorization": "Bearer token123",
        "User-Agent": "Talkie/0.1.0",
        "Accept": "application/json"
    }


def test_build_get_request():
    """Тест построения GET-запроса."""
    builder = RequestBuilder(
        method="GET",
        url="https://example.com/api/users",
        headers=["Accept: application/json"],
        query=["page=1", "limit=10"]
    )
    
    request = builder.build()
    
    assert request["method"] == "GET"
    assert request["url"] == "https://example.com/api/users"
    assert request["headers"] == {"Accept": "application/json"}
    assert request["params"] == {"page": "1", "limit": "10"}
    assert "json" not in request
    assert "data" not in request


def test_build_post_request_json():
    """Тест построения POST-запроса с JSON."""
    builder = RequestBuilder(
        method="POST",
        url="https://example.com/api/users",
        headers=["Authorization: Bearer token123"],
        data=["name=John", "age:=30", "is_admin:=true"]
    )
    
    request = builder.build()
    
    assert request["method"] == "POST"
    assert request["url"] == "https://example.com/api/users"
    assert request["headers"] == {
        "Authorization": "Bearer token123",
        "Content-Type": "application/json"
    }
    assert request["json"] == {
        "name": "John",
        "age": 30,
        "is_admin": True
    }
    assert "data" not in request


def test_build_post_request_form():
    """Тест построения POST-запроса с данными формы."""
    builder = RequestBuilder(
        method="POST",
        url="https://example.com/api/login",
        data=["username=testuser", "password=password123"]
    )
    
    request = builder.build()
    
    assert request["method"] == "POST"
    assert request["url"] == "https://example.com/api/login"
    assert request["headers"] == {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    assert request["data"] == {
        "username": "testuser",
        "password": "password123"
    }


def test_parse_headers_edge_cases():
    """Тест граничных случаев при разборе заголовков."""
    # Пустые заголовки
    builder = RequestBuilder(
        method="GET",
        url="https://example.com/api",
        headers=["Empty: ", ": value", "NoValue:", "  :  "]
    )
    assert builder.headers == {
        "Empty": "",
        "NoValue": ""
    }
    
    # Заголовки с пробелами
    builder = RequestBuilder(
        method="GET",
        url="https://example.com/api",
        headers=["  Content-Type  :  application/json  "]
    )
    assert builder.headers == {
        "Content-Type": "application/json"
    }
    
    # Дублирующиеся заголовки (должен использоваться последний)
    builder = RequestBuilder(
        method="GET",
        url="https://example.com/api",
        headers=[
            "X-Custom: first",
            "X-Custom: second",
            "X-Custom: third"
        ]
    )
    assert builder.headers == {
        "X-Custom": "third"
    }


def test_parse_data_edge_cases():
    """Тест граничных случаев при разборе данных."""
    # Пустые значения
    builder = RequestBuilder(
        method="POST",
        url="https://example.com/api",
        data=["empty=", "=value", "no_value=", "  =  "]
    )
    assert builder.data == {
        "empty": "",
        "no_value": ""
    }
    
    # Специальные символы
    builder = RequestBuilder(
        method="POST",
        url="https://example.com/api",
        data=["key=value with spaces", "symbols=!@#$%^&*()"]
    )
    assert builder.data == {
        "key": "value with spaces",
        "symbols": "!@#$%^&*()"
    }
    
    # Некорректный JSON
    builder = RequestBuilder(
        method="POST",
        url="https://example.com/api",
        data=["invalid:={not json}", "valid:={\"key\": \"value\"}"]
    )
    assert builder.json_data == {
        "invalid": "{not json}",
        "valid": {"key": "value"}
    }


def test_parse_query_edge_cases():
    """Тест граничных случаев при разборе параметров запроса."""
    # URL с существующими параметрами
    builder = RequestBuilder(
        method="GET",
        url="https://example.com/api?existing=param",
        query=["page=1", "limit=10"]
    )
    request = builder.build()
    assert request["params"] == {
        "page": "1",
        "limit": "10"
    }
    
    # Специальные символы в параметрах
    builder = RequestBuilder(
        method="GET",
        url="https://example.com/api",
        query=["q=search term", "filter=status!=done"]
    )
    assert builder.query_params == {
        "q": "search term",
        "filter": "status!=done"
    }
    
    # Дублирующиеся параметры (должен использоваться последний)
    builder = RequestBuilder(
        method="GET",
        url="https://example.com/api",
        query=["sort=name", "sort=date", "sort=id"]
    )
    assert builder.query_params == {
        "sort": "id"
    }


def test_mixed_form_and_json_data():
    """Тест смешанных данных формы и JSON в одном запросе."""
    builder = RequestBuilder(
        method="POST",
        url="https://example.com/api/users",
        data=[
            # Обычные данные формы
            "username=testuser",
            "email=user@example.com",
            # JSON данные
            "settings:={\"theme\": \"dark\"}",
            "roles:=[\"user\", \"admin\"]",
            # Смешанные данные
            "active:=true",
            "status=active"
        ]
    )
    
    request = builder.build()
    assert request["headers"]["Content-Type"] == "application/json"
    assert request["json"] == {
        "username": "testuser",
        "email": "user@example.com",
        "settings": {"theme": "dark"},
        "roles": ["user", "admin"],
        "active": True,
        "status": "active"
    } 