"""Тесты для асинхронного HTTP-клиента."""

import asyncio
import os
import tempfile
import json
from unittest.mock import patch, AsyncMock

import pytest
import httpx
from httpx import Response

from talkie.core.async_client import AsyncHttpClient


@pytest.fixture
def mock_response():
    """Возвращает мок-объект HTTP-ответа."""
    response = AsyncMock(spec=Response)
    response.status_code = 200
    response.headers = {"Content-Type": "application/json"}
    response.text = '{"id": 1, "name": "Test"}'
    response.json.return_value = {"id": 1, "name": "Test"}
    return response


@pytest.mark.asyncio
async def test_async_client_request(mock_response):
    """Тест асинхронного выполнения запроса."""
    with patch("httpx.AsyncClient.request", return_value=mock_response) as mock_request:
        async with AsyncHttpClient() as client:
            req_id, response = await client.request(
                method="GET",
                url="https://example.com/api",
                headers={"Accept": "application/json"},
                params={"page": "1"},
                request_id="test_req"
            )
            
            assert req_id == "test_req"
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


@pytest.mark.asyncio
async def test_async_client_execute_batch(mock_response):
    """Тест выполнения пакета запросов."""
    with patch("httpx.AsyncClient.request", return_value=mock_response) as mock_request:
        async with AsyncHttpClient(concurrency=3) as client:
            requests = [
                {
                    "method": "GET",
                    "url": f"https://example.com/api/users/{i}",
                    "request_id": f"req_{i}"
                }
                for i in range(1, 6)  # 5 запросов
            ]
            
            results = await client.execute_batch(requests)
            
            # Проверяем, что все запросы выполнились
            assert len(results) == 5
            
            # Проверяем формат результатов
            for i, (req_id, response, error) in enumerate(results):
                assert req_id == f"req_{i+1}"
                assert response is not None
                assert response.status_code == 200
                assert error is None
            
            # Проверяем количество вызовов request
            assert mock_request.call_count == 5


@pytest.mark.asyncio
async def test_async_client_execute_batch_with_errors():
    """Тест выполнения пакета запросов с ошибками."""
    # Создаем успешный и ошибочный ответы
    success_response = AsyncMock(spec=Response)
    success_response.status_code = 200
    success_response.headers = {"Content-Type": "application/json"}
    success_response.text = '{"id": 1, "name": "Test"}'
    success_response.json.return_value = {"id": 1, "name": "Test"}
    
    # Функция-заглушка для имитации успешных и неудачных запросов
    async def mock_request(**kwargs):
        if "users/2" in kwargs["url"] or "users/4" in kwargs["url"]:
            raise httpx.ConnectError("Connection refused")
        return success_response
    
    with patch("httpx.AsyncClient.request", side_effect=mock_request) as mock_request:
        async with AsyncHttpClient(concurrency=2) as client:
            requests = [
                {
                    "method": "GET",
                    "url": f"https://example.com/api/users/{i}",
                    "request_id": f"req_{i}"
                }
                for i in range(1, 6)  # 5 запросов
            ]
            
            results = await client.execute_batch(requests)
            
            # Проверяем, что все запросы обработаны
            assert len(results) == 5
            
            # Проверяем успешные запросы
            success_count = 0
            error_count = 0
            
            for req_id, response, error in results:
                if "req_2" in req_id or "req_4" in req_id:
                    assert response is None
                    assert error is not None
                    assert isinstance(error, httpx.ConnectError)
                    error_count += 1
                else:
                    assert response is not None
                    assert response.status_code == 200
                    assert error is None
                    success_count += 1
            
            assert success_count == 3
            assert error_count == 2


@pytest.mark.asyncio
async def test_async_client_execute_from_file():
    """Тест выполнения запросов из файла."""
    # Создаем временный файл с запросами
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
        temp.write("GET https://example.com/api/users/1\n")
        temp.write("GET https://example.com/api/users/2\n")
        temp.write("# Комментарий\n")
        temp.write("GET https://example.com/api/users/3\n")
        temp.write("INVALID LINE\n")  # Некорректная строка
        temp.write("GET https://example.com/api/users/4\n")
        temp_filename = temp.name
    
    # Создаем временную директорию для результатов
    with tempfile.TemporaryDirectory() as temp_dir:
        # Создаем успешный ответ
        success_response = AsyncMock(spec=Response)
        success_response.status_code = 200
        success_response.headers = {"Content-Type": "application/json"}
        success_response.text = '{"id": 1, "name": "Test"}'
        success_response.json.return_value = {"id": 1, "name": "Test"}
        
        with patch("httpx.AsyncClient.request", return_value=success_response) as mock_request:
            async with AsyncHttpClient() as client:
                results = await client.execute_from_file(temp_filename, temp_dir)
                
                # Проверяем, что обработано правильное количество запросов
                # (4 строки, из них 1 комментарий и 1 некорректная)
                assert len(results) == 4
                
                # Проверяем, что все выполненные запросы успешны
                for req_id, response, error in results:
                    assert response is not None
                    assert response.status_code == 200
                    assert error is None
                
                # Проверяем, что созданы файлы результатов
                result_files = os.listdir(temp_dir)
                assert len(result_files) == 4
                
                # Проверяем содержимое файлов
                for i, filename in enumerate(sorted(result_files)):
                    filepath = os.path.join(temp_dir, filename)
                    with open(filepath, "r") as f:
                        data = json.load(f)
                        assert data["response"]["status_code"] == 200
                        assert data["response"]["headers"]["Content-Type"] == "application/json"
                        assert "id" in data["response"]["content"]
                        assert "name" in data["response"]["content"]
    
    # Удаляем временный файл
    os.unlink(temp_filename)


@pytest.mark.asyncio
async def test_async_client_with_delay():
    """Тест задержки между запросами."""
    # Создаем мок для time.sleep для проверки задержки
    with patch("httpx.AsyncClient.request", return_value=AsyncMock(spec=Response)) as mock_request:
        with patch("asyncio.sleep") as mock_sleep:
            async with AsyncHttpClient(concurrency=1, request_delay=0.5) as client:
                requests = [
                    {
                        "method": "GET",
                        "url": f"https://example.com/api/users/{i}",
                        "request_id": f"req_{i}"
                    }
                    for i in range(1, 4)  # 3 запроса
                ]
                
                await client.execute_batch(requests)
                
                # Проверяем, что метод sleep был вызван для каждого запроса
                # с правильным значением задержки
                assert mock_sleep.await_count == 3
                for call in mock_sleep.await_args_list:
                    args, _ = call
                    assert args[0] == 0.5 