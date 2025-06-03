"""Тесты для HTTP-клиента."""

import pytest
from unittest.mock import patch, MagicMock

from talkie.core.client import HttpClient


@pytest.fixture
def mock_response():
    """Фикстура для мок-ответа."""
    response = MagicMock()
    response.status_code = 200
    response.reason_phrase = "OK"
    response.elapsed.total_seconds.return_value = 0.1
    response.headers = {"Content-Type": "application/json"}
    response.content = b'{"id": 1, "name": "Test"}'
    response.text = '{"id": 1, "name": "Test"}'
    response.json.return_value = {"id": 1, "name": "Test"}
    return response


def test_http_client_init():
    """Тест инициализации HttpClient."""
    client = HttpClient()
    assert client.client is not None


@patch("httpx.Client.request")
def test_client_get_request(mock_request, mock_response):
    """Тест выполнения GET-запроса."""
    mock_request.return_value = mock_response
    
    client = HttpClient()
    
    request = {
        "method": "GET",
        "url": "https://example.com/api",
        "headers": {"Accept": "application/json"},
        "params": {"page": "1"},
        "timeout": 30.0
    }
    
    response = client.send(request)
    
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == {"id": 1, "name": "Test"}
    
    # Проверка, что метод request был вызван с правильными параметрами
    mock_request.assert_called_once()
    args, kwargs = mock_request.call_args
    
    assert kwargs["method"] == "GET"
    assert kwargs["url"] == "https://example.com/api"
    assert kwargs["headers"] == {"Accept": "application/json"}
    assert kwargs["params"] == {"page": "1"}


@patch("httpx.Client.request")
def test_client_post_request_json(mock_request, mock_response):
    """Тест выполнения POST-запроса с JSON."""
    mock_request.return_value = mock_response
    
    client = HttpClient()
    
    request = {
        "method": "POST",
        "url": "https://example.com/api/users",
        "headers": {"Content-Type": "application/json"},
        "json": {"name": "Test User", "age": 30},
        "timeout": 30.0
    }
    
    response = client.send(request)
    
    assert response.status_code == 200
    
    # Проверка, что метод request был вызван с правильными параметрами
    mock_request.assert_called_once()
    args, kwargs = mock_request.call_args
    
    assert kwargs["method"] == "POST"
    assert kwargs["url"] == "https://example.com/api/users"
    assert kwargs["headers"] == {"Content-Type": "application/json"}
    assert kwargs["json"] == {"name": "Test User", "age": 30}


@patch("httpx.Client.request")
def test_client_post_request_form(mock_request, mock_response):
    """Тест выполнения POST-запроса с данными формы."""
    mock_request.return_value = mock_response
    
    client = HttpClient()
    
    request = {
        "method": "POST",
        "url": "https://example.com/api/login",
        "headers": {"Content-Type": "application/x-www-form-urlencoded"},
        "data": {"username": "test", "password": "password123"},
        "timeout": 30.0
    }
    
    response = client.send(request)
    
    assert response.status_code == 200
    
    # Проверка, что метод request был вызван с правильными параметрами
    mock_request.assert_called_once()
    args, kwargs = mock_request.call_args
    
    assert kwargs["method"] == "POST"
    assert kwargs["url"] == "https://example.com/api/login"
    assert kwargs["headers"] == {"Content-Type": "application/x-www-form-urlencoded"}
    assert kwargs["data"] == {"username": "test", "password": "password123"}


def test_client_context_manager():
    """Тест работы HttpClient как контекстного менеджера."""
    with patch.object(HttpClient, "close") as mock_close:
        with HttpClient() as client:
            assert isinstance(client, HttpClient)
        
        # Проверка, что метод close был вызван
        mock_close.assert_called_once() 