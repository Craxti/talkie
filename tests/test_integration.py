import pytest
import os
import sys
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
    # Используем python вместо python3 на Windows
    python_cmd = "python" if sys.platform == "win32" else "python3"
    full_command = [python_cmd, "-m", "talkie"] + command
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


def test_graphql_integration(mock_server, temp_config_dir):
    """Интеграционный тест GraphQL запроса."""
    # Настраиваем GraphQL endpoint на мок-сервере
    mock_server.expect_request("/graphql", method="POST").respond_with_json({
        "data": {
            "users": [
                {"id": "1", "name": "John Doe"},
                {"id": "2", "name": "Jane Smith"}
            ]
        }
    })

    config_path = Path(temp_config_dir) / "config.json"
    with open(config_path, "r") as f:
        config = json.load(f)

    base_url = f"http://{mock_server.host}:{mock_server.port}"
    config["environments"]["test"]["base_url"] = base_url

    with open(config_path, "w") as f:
        json.dump(config, f)

    # Тестируем GraphQL запрос
    stdout, _ = run_talkie_command([
        "graphql",
        f"{base_url}/graphql",
        "--query", "query { users { id name } }",
        "--json"
    ])

    # Проверяем результат
    response_data = json.loads(stdout)
    assert "data" in response_data
    assert "users" in response_data["data"]
    assert len(response_data["data"]["users"]) == 2


def test_cache_integration(mock_server, temp_config_dir):
    """Интеграционный тест кэширования."""
    config_path = Path(temp_config_dir) / "config.json"
    with open(config_path, "r") as f:
        config = json.load(f)

    base_url = f"http://{mock_server.host}:{mock_server.port}"
    config["environments"]["test"]["base_url"] = base_url

    with open(config_path, "w") as f:
        json.dump(config, f)

    # Проверяем статистику кэша
    stdout, _ = run_talkie_command(["cache", "stats"])

    assert "Cache Statistics:" in stdout
    assert "Status:" in stdout
    assert "Entries:" in stdout

    # Очищаем кэш
    stdout, _ = run_talkie_command(["cache", "clear"])
    assert "Cache cleared successfully" in stdout

    # Настраиваем кэш
    stdout, _ = run_talkie_command([
        "cache", "config",
        "--ttl", "600",
        "--max-entries", "100"
    ])
    assert "Cache configuration updated" in stdout


def test_openapi_inspection_integration(temp_config_dir):
    """Интеграционный тест инспекции OpenAPI спецификации."""
    # Создаем простую OpenAPI спецификацию
    openapi_spec = {
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
                            "description": "Success"
                        }
                    }
                }
            }
        }
    }

    # Сохраняем спецификацию во временный файл
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as spec_file:
        json.dump(openapi_spec, spec_file)
        spec_path = spec_file.name

    try:
        # Тестируем инспекцию OpenAPI
        stdout, stderr = run_talkie_command(["openapi", spec_path])

        # Может быть проблема с кодировкой, проверим наличие ключевых элементов
        output = stdout + stderr
        assert ("Test API" in output or "title" in output or "/users" in output), f"Output: {output}"

    finally:
        # Удаляем временный файл
        os.unlink(spec_path)


def test_curl_generation_integration(mock_server, temp_config_dir):
    """Интеграционный тест генерации curl команд."""
    config_path = Path(temp_config_dir) / "config.json"
    with open(config_path, "r") as f:
        config = json.load(f)

    base_url = f"http://{mock_server.host}:{mock_server.port}"
    config["environments"]["test"]["base_url"] = base_url

    with open(config_path, "w") as f:
        json.dump(config, f)

    # Тестируем генерацию curl для GET запроса
    stdout, _ = run_talkie_command([
        "curl",
        f"{base_url}/api/users",
        "--method", "GET",
        "--header", "Authorization:Bearer token123"
    ])

    assert "curl" in stdout
    assert base_url in stdout
    assert "Authorization" in stdout

    # Тестируем генерацию curl для POST запроса
    stdout, _ = run_talkie_command([
        "curl",
        f"{base_url}/api/users",
        "--method", "POST",
        "--data", "name=Test User",
        "--header", "Content-Type:application/json"
    ])

    assert "curl" in stdout
    assert "-X POST" in stdout
    assert "name=Test" in stdout and "User" in stdout


def test_format_integration(temp_config_dir):
    """Интеграционный тест форматирования файлов."""
    # Создаем JSON файл для форматирования
    json_data = {"users": [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]}

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as input_file:
        json.dump(json_data, input_file, separators=(',', ':'))  # Минифицированный JSON
        input_path = input_file.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as output_file:
        output_path = output_file.name

    try:
        # Тестируем форматирование JSON
        stdout, _ = run_talkie_command([
            "format",
            input_path,
            "--output", output_path,
            "--type", "json"
        ])

        # Проверяем, что файл был отформатирован
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            formatted_content = f.read()
            # Форматированный JSON должен содержать отступы
            assert '  ' in formatted_content or '\t' in formatted_content

    finally:
        # Удаляем временные файлы
        os.unlink(input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_generate_client_integration(temp_config_dir):
    """Интеграционный тест генерации OpenAPI клиента."""
    # Создаем более полную OpenAPI спецификацию
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Pet Store API",
            "version": "1.0.0",
            "description": "A simple pet store API"
        },
        "servers": [
            {"url": "https://api.petstore.com/v1"}
        ],
        "paths": {
            "/pets": {
                "get": {
                    "operationId": "listPets",
                    "summary": "List all pets",
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "A list of pets"
                        }
                    }
                },
                "post": {
                    "operationId": "createPet",
                    "summary": "Create a pet",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/Pet"
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Pet created"
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Pet": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "tag": {"type": "string"}
                    },
                    "required": ["id", "name"]
                }
            }
        }
    }

    # Сохраняем спецификацию во временный файл
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as spec_file:
        json.dump(openapi_spec, spec_file)
        spec_path = spec_file.name

    # Создаем временную директорию для генерации
    with tempfile.TemporaryDirectory() as output_dir:
        try:
            # Тестируем генерацию клиента
            stdout, _ = run_talkie_command([
                "generate-client",
                spec_path,
                "--output", output_dir,
                "--class-name", "PetStoreClient",
                "--overwrite"
            ])

            assert "Client generated successfully" in stdout
            assert "PetStoreClient" in stdout

            # Проверяем, что файлы созданы
            client_file = Path(output_dir) / "petstoreclient.py"
            models_file = Path(output_dir) / "models.py"
            init_file = Path(output_dir) / "__init__.py"
            readme_file = Path(output_dir) / "README.md"

            assert client_file.exists()
            assert models_file.exists()
            assert init_file.exists()
            assert readme_file.exists()

            # Проверяем содержимое основного файла клиента
            with open(client_file, 'r') as f:
                client_content = f.read()
                assert "class PetStoreClient" in client_content
                assert "def list_pets" in client_content
                assert "def create_pet" in client_content

            # Проверяем содержимое моделей
            with open(models_file, 'r') as f:
                models_content = f.read()
                assert "class Pet" in models_content
                assert "BaseModel" in models_content

        finally:
            # Удаляем временный файл спецификации
            os.unlink(spec_path)


def test_error_handling_integration(temp_config_dir):
    """Интеграционный тест обработки ошибок."""
    # Тестируем обработку неверного URL
    stdout, stderr = run_talkie_command([
        "get", "invalid-url"
    ], expected_exit_code=1)

    assert "Error" in stderr or "Validation Error" in stdout or "Failed to connect" in stderr

    # Тестируем обработку несуществующего файла
    stdout, stderr = run_talkie_command([
        "format", "/nonexistent/file.json"
    ], expected_exit_code=1)

    assert "Error" in stderr or "not found" in stdout or "Error in formatting" in stdout

    # Тестируем обработку неверных параметров GraphQL
    stdout, stderr = run_talkie_command([
        "graphql", "http://example.com/graphql"
    ], expected_exit_code=1)

    assert "Error" in stderr or "No query specified" in stdout