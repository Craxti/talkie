import pytest
import tempfile
import os
import json
import yaml
from talkie.utils.openapi import (
    load_openapi_spec,
    validate_openapi_spec,
    extract_endpoints,
    extract_endpoint_details,
    format_openapi_spec
)


@pytest.fixture
def sample_openapi_json():
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0"
        },
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get users",
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "name": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": "Create user",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "User created"
                        }
                    }
                }
            },
            "/users/{id}": {
                "get": {
                    "summary": "Get user by ID",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "integer"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "User found"
                        }
                    }
                }
            }
        }
    }


@pytest.fixture
def openapi_json_file(sample_openapi_json):
    """Создает временный JSON-файл с OpenAPI спецификацией."""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as f:
        json.dump(sample_openapi_json, f)
        filename = f.name
    yield filename
    os.unlink(filename)


@pytest.fixture
def openapi_yaml_file(sample_openapi_json):
    """Создает временный YAML-файл с OpenAPI спецификацией."""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml', delete=False) as f:
        yaml.dump(sample_openapi_json, f)
        filename = f.name
    yield filename
    os.unlink(filename)


def test_load_openapi_spec_json(openapi_json_file):
    """Тест загрузки OpenAPI спецификации из JSON-файла."""
    spec = load_openapi_spec(openapi_json_file)
    assert spec["info"]["title"] == "Test API"
    assert spec["openapi"] == "3.0.0"


def test_load_openapi_spec_yaml(openapi_yaml_file):
    """Тест загрузки OpenAPI спецификации из YAML-файла."""
    spec = load_openapi_spec(openapi_yaml_file)
    assert spec["info"]["title"] == "Test API"
    assert spec["openapi"] == "3.0.0"


def test_validate_openapi_spec(sample_openapi_json):
    """Тест валидации OpenAPI спецификации."""
    is_valid, _ = validate_openapi_spec(sample_openapi_json)
    assert is_valid is True


def test_extract_endpoints(sample_openapi_json):
    """Тест извлечения конечных точек из OpenAPI спецификации."""
    endpoints = extract_endpoints(sample_openapi_json)
    
    assert len(endpoints) == 3
    
    # Проверяем, что все эндпоинты присутствуют
    endpoint_keys = [(e["path"], e["method"]) for e in endpoints]
    assert ("/users", "get") in endpoint_keys
    assert ("/users", "post") in endpoint_keys
    assert ("/users/{id}", "get") in endpoint_keys


def test_extract_endpoint_details(sample_openapi_json):
    """Тест извлечения деталей конечной точки из OpenAPI спецификации."""
    details = extract_endpoint_details(sample_openapi_json, "/users", "get")
    
    assert details["summary"] == "Get users"
    assert "responses" in details
    assert "200" in details["responses"]


def test_format_openapi_spec(sample_openapi_json):
    """Тест форматирования OpenAPI спецификации."""
    formatted = format_openapi_spec(sample_openapi_json)
    
    # Проверяем, что результат - строка и содержит ключевые элементы
    assert isinstance(formatted, str)
    assert "Test API" in formatted
    assert "/users" in formatted
    assert "Get users" in formatted 