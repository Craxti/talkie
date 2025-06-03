import pytest
import os
import json
import subprocess
import tempfile
from pathlib import Path


@pytest.fixture
def mock_server(request):
    """
    Запускает мок HTTP-сервер для интеграционных тестов.
    Использует pytest-httpserver для создания временного HTTP-сервера.
    """
    pytest.importorskip("pytest_httpserver")
    from pytest_httpserver import HTTPServer
    
    server = HTTPServer()
    server.start()
    
    # Настраиваем мок-ответы
    server.expect_request("/api/users", method="GET").respond_with_json([
        {"id": 1, "name": "User 1"},
        {"id": 2, "name": "User 2"}
    ])
    
    # Настраиваем ответ для POST запроса
    server.expect_request("/api/users", method="POST").respond_with_json(
        {"id": 3, "name": "New User"}
    )
    
    server.expect_request("/api/users/1").respond_with_json(
        {"id": 1, "name": "User 1", "email": "user1@example.com"}
    )
    
    yield server
    
    server.stop()


@pytest.fixture
def temp_config_dir():
    """Создает временный каталог конфигурации для тестов."""
    with tempfile.TemporaryDirectory() as temp_dir:
        old_config_dir = os.environ.get("TALKIE_CONFIG_DIR")
        os.environ["TALKIE_CONFIG_DIR"] = temp_dir
        
        # Создаем базовый конфиг
        config_path = Path(temp_dir) / "config.json"
        config = {
            "default_headers": {
                "User-Agent": "Talkie-Test/0.1.0"
            },
            "environments": {
                "test": {
                    "name": "test",
                    "base_url": "http://localhost:8000"
                }
            },
            "active_environment": "test"
        }
        
        with open(config_path, "w") as f:
            json.dump(config, f)
        
        yield temp_dir
        
        # Восстанавливаем оригинальный путь к конфигурации
        if old_config_dir:
            os.environ["TALKIE_CONFIG_DIR"] = old_config_dir
        else:
            del os.environ["TALKIE_CONFIG_DIR"]


def run_talkie_command(command, expected_exit_code=0):
    """Запускает команду talkie и возвращает результат."""
    full_command = ["python3", "-m", "talkie"] + command
    process = subprocess.run(
        full_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding='utf-8',
        errors='replace'
    )
    
    assert process.returncode == expected_exit_code, \
        f"Команда вернула код {process.returncode}, ожидалось {expected_exit_code}. Stderr: {process.stderr}"
    
    return process.stdout, process.stderr


def test_get_request_integration(mock_server, temp_config_dir):
    """Интеграционный тест GET-запроса."""
    # Обновляем конфигурацию с правильным адресом сервера
    config_path = Path(temp_config_dir) / "config.json"
    with open(config_path, "r") as f:
        config = json.load(f)
    
    base_url = f"http://{mock_server.host}:{mock_server.port}"
    config["environments"]["test"]["base_url"] = base_url
    
    with open(config_path, "w") as f:
        json.dump(config, f)
    
    # Выполняем GET-запрос
    stdout, _ = run_talkie_command(["get", f"{base_url}/api/users", "--json"])
    
    # Проверяем результат
    assert "id" in stdout
    assert "name" in stdout


def test_post_request_integration(mock_server, temp_config_dir):
    """Интеграционный тест POST-запроса."""
    # Обновляем конфигурацию с правильным адресом сервера
    config_path = Path(temp_config_dir) / "config.json"
    with open(config_path, "r") as f:
        config = json.load(f)
    
    base_url = f"http://{mock_server.host}:{mock_server.port}"
    config["environments"]["test"]["base_url"] = base_url
    
    with open(config_path, "w") as f:
        json.dump(config, f)
    
    # Тестируем POST с данными формы
    stdout, _ = run_talkie_command([
        "post",
        f"{base_url}/api/users",
        "-d", "name=New User",
        "-d", "email=newuser@example.com",
        "--json"
    ])
    
    # Проверяем результат
    response_data = json.loads(stdout)
    if isinstance(response_data, list):
        response_data = response_data[0]
    assert response_data["id"] == 3
    assert response_data["name"] == "New User"
    
    # Тестируем POST с JSON данными
    stdout, _ = run_talkie_command([
        "post", 
        f"{base_url}/api/users", 
        "-d", "name:=New User 2",
        "-d", "email:=newuser2@example.com",
        "-d", "roles:=[\"user\", \"admin\"]",
        "-d", "settings:={\"theme\": \"dark\", \"notifications\": true}",
        "--json"
    ])
    
    # Проверяем результат
    response_data = json.loads(stdout)
    if isinstance(response_data, list):
        response_data = response_data[0]
    assert response_data["id"] == 3
    assert response_data["name"] == "New User"
    
    # Тестируем POST с заголовками и параметрами запроса
    stdout, _ = run_talkie_command([
        "post", 
        f"{base_url}/api/users", 
        "-H", "X-API-Key: test-key",
        "-H", "Accept-Language: ru",
        "-q", "source=api",
        "-q", "version=1",
        "-d", "name=New User 3",
        "--json"
    ])
    
    # Проверяем результат
    response_data = json.loads(stdout)
    if isinstance(response_data, list):
        response_data = response_data[0]
    assert response_data["id"] == 3
    assert response_data["name"] == "New User"


def test_output_to_file_integration(mock_server, temp_config_dir):
    """Интеграционный тест сохранения вывода в файл."""
    # Обновляем конфигурацию с правильным адресом сервера
    config_path = Path(temp_config_dir) / "config.json"
    with open(config_path, "r") as f:
        config = json.load(f)
    
    base_url = f"http://{mock_server.host}:{mock_server.port}"
    config["environments"]["test"]["base_url"] = base_url
    
    with open(config_path, "w") as f:
        json.dump(config, f)
    
    # Временный файл для вывода
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as output_file:
        output_path = output_file.name
    
    try:
        # Выполняем запрос с сохранением вывода
        run_talkie_command(["get", f"{base_url}/api/users/1", "-o", output_path])
        
        # Проверяем, что файл создан и содержит JSON
        assert os.path.exists(output_path)
        with open(output_path, "r") as f:
            data = json.load(f)
            assert "id" in data
            assert "name" in data
    finally:
        # Удаляем временный файл
        if os.path.exists(output_path):
            os.unlink(output_path) 