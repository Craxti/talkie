"""Конфигурация и общие фикстуры для тестов."""

import os
import tempfile
from typing import Generator

import pytest
from _pytest.fixtures import SubRequest


def pytest_configure(config):
    """Настройка pytest."""
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as async"
    )


@pytest.fixture
def temp_config_dir() -> Generator[str, None, None]:
    """Создает временный каталог конфигурации для тестов."""
    with tempfile.TemporaryDirectory() as temp_dir:
        old_config_dir = os.environ.get("TALKIE_CONFIG_DIR")
        os.environ["TALKIE_CONFIG_DIR"] = temp_dir
        yield temp_dir
        if old_config_dir:
            os.environ["TALKIE_CONFIG_DIR"] = old_config_dir
        else:
            del os.environ["TALKIE_CONFIG_DIR"]


@pytest.fixture
def mock_http_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Мок для HTTP-ответов в тестах."""
    class MockResponse:
        def __init__(self, status_code: int = 200, content: bytes = None, headers: dict = None) -> None:
            self.status_code = status_code
            self._content = content or b'{"status": "ok", "code": 200, "data": {"name": "Test", "value": 123}}'
            self.headers = headers or {"Content-Type": "application/json; charset=utf-8"}
            self.reason_phrase = "OK" if status_code == 200 else "Error"
            from datetime import timedelta
            self.elapsed = timedelta(milliseconds=100)
            
        @property
        def content(self) -> bytes:
            return self._content
            
        @property
        def text(self) -> str:
            return self._content.decode('utf-8')
            
        def json(self) -> dict:
            import json
            return json.loads(self.text)
            
        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise Exception(f"HTTP Error: {self.status_code}")
    
    class MockClient:
        def __init__(self, *args, **kwargs) -> None:
            pass
            
        def request(self, *args, **kwargs) -> MockResponse:
            return MockResponse()
    
    monkeypatch.setattr("talkie.core.client.httpx.Client", MockClient)


@pytest.fixture
def mock_server(request: SubRequest) -> Generator:
    """Запускает мок HTTP-сервер для интеграционных тестов."""
    pytest.importorskip("pytest_httpserver")
    from pytest_httpserver import HTTPServer
    
    server = HTTPServer()
    server.start()
    
    # Настраиваем мок-ответы
    server.expect_request("/api/users", method="GET").respond_with_json([
        {"id": 1, "name": "User 1"},
        {"id": 2, "name": "User 2"}
    ])
    
    server.expect_request("/api/users", method="POST").respond_with_json(
        {"id": 3, "name": "New User"}
    )
    
    server.expect_request("/api/users/1").respond_with_json(
        {"id": 1, "name": "User 1", "email": "user1@example.com"}
    )
    
    yield server
    
    server.stop()


@pytest.fixture
def sample_openapi_spec() -> dict:
    """Возвращает пример спецификации OpenAPI для тестов."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
            "description": "API для тестирования"
        },
        "servers": [
            {
                "url": "https://api.example.com",
                "description": "Тестовый сервер"
            }
        ],
        "paths": {
            "/users": {
                "get": {
                    "summary": "Получить список пользователей",
                    "responses": {
                        "200": {
                            "description": "Успешный ответ",
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
                }
            }
        }
    } 