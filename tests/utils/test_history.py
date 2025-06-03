"""Тесты для модуля истории HTTP запросов."""

import os
import json
import datetime
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch

from talkie.utils.history import RequestHistory, RequestRecord


@pytest.fixture
def temp_history_dir():
    """Создает временную директорию для файлов истории."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def history(temp_history_dir):
    """Создает экземпляр RequestHistory для тестов."""
    history_file = Path(temp_history_dir) / "requests.json"
    return RequestHistory(history_file=history_file)


@pytest.fixture
def sample_record():
    """Создает тестовую запись запроса."""
    return RequestRecord(
        method="GET",
        url="https://api.example.com/users",
        headers={"Authorization": "Bearer token"},
        query_params={"page": "1", "limit": "10"},
        response_status=200,
        response_headers={"Content-Type": "application/json"},
        response_body={"data": [{"id": 1, "name": "User 1"}]},
        environment="test",
        tags=["api", "users"],
        notes="Test request"
    )


def test_request_record_creation(sample_record):
    """Тест создания записи запроса."""
    assert sample_record.method == "GET"
    assert sample_record.url == "https://api.example.com/users"
    assert sample_record.headers["Authorization"] == "Bearer token"
    assert sample_record.query_params["page"] == "1"
    assert sample_record.response_status == 200
    assert sample_record.environment == "test"
    assert "api" in sample_record.tags
    assert sample_record.notes == "Test request"
    assert isinstance(sample_record.timestamp, datetime.datetime)
    assert isinstance(sample_record.id, str)


def test_history_initialization(temp_history_dir):
    """Тест инициализации менеджера истории."""
    history_file = Path(temp_history_dir) / "requests.json"
    history = RequestHistory(
        history_file=history_file,
        max_records=500
    )
    
    assert history.history_file == history_file
    assert history.max_records == 500
    assert len(history.records) == 0
    assert history.history_file.parent.exists()


def test_add_record(history, sample_record):
    """Тест добавления записи в историю."""
    record_id = history.add_record(sample_record)
    
    assert record_id == sample_record.id
    assert len(history.records) == 1
    assert history.records[0] == sample_record
    assert history.history_file.exists()


def test_get_record(history, sample_record):
    """Тест получения записи по идентификатору."""
    history.add_record(sample_record)
    
    # Получение существующей записи
    record = history.get_record(sample_record.id)
    assert record == sample_record
    
    # Получение несуществующей записи
    record = history.get_record("non_existent_id")
    assert record is None


def test_delete_record(history, sample_record):
    """Тест удаления записи."""
    history.add_record(sample_record)
    
    # Удаление существующей записи
    success = history.delete_record(sample_record.id)
    assert success is True
    assert len(history.records) == 0
    
    # Удаление несуществующей записи
    success = history.delete_record("non_existent_id")
    assert success is False


def test_clear_history(history, sample_record):
    """Тест очистки истории."""
    history.add_record(sample_record)
    assert len(history.records) == 1
    
    history.clear()
    assert len(history.records) == 0
    assert history.history_file.exists()


def test_max_records_limit(history):
    """Тест ограничения максимального количества записей."""
    history.max_records = 2
    
    # Добавляем 3 записи
    for i in range(3):
        record = RequestRecord(
            method="GET",
            url=f"https://api.example.com/users/{i}",
            response_status=200
        )
        history.add_record(record)
    
    assert len(history.records) == 2
    assert history.records[0].url == "https://api.example.com/users/2"
    assert history.records[1].url == "https://api.example.com/users/1"


def test_search_records(history):
    """Тест поиска записей."""
    # Добавляем тестовые записи
    records = [
        RequestRecord(
            method="GET",
            url="https://api.example.com/users",
            response_status=200,
            environment="prod",
            tags=["api", "users"]
        ),
        RequestRecord(
            method="POST",
            url="https://api.example.com/users",
            response_status=201,
            environment="test",
            tags=["api", "users", "create"]
        ),
        RequestRecord(
            method="GET",
            url="https://api.example.com/posts",
            response_status=404,
            environment="prod",
            tags=["api", "posts"]
        )
    ]
    
    for record in records:
        history.add_record(record)
    
    # Поиск по методу
    results = history.search(method="GET")
    assert len(results) == 2
    
    # Поиск по URL
    results = history.search(url_pattern="users")
    assert len(results) == 2
    
    # Поиск по статусу
    results = history.search(status_range=(200, 299))
    assert len(results) == 2
    
    # Поиск по окружению
    results = history.search(environment="prod")
    assert len(results) == 2
    
    # Поиск по тегам
    results = history.search(tags=["users"])
    assert len(results) == 2
    
    # Комбинированный поиск
    results = history.search(
        method="GET",
        environment="prod",
        status_range=(200, 299)
    )
    assert len(results) == 1


def test_save_and_load(history, sample_record):
    """Test saving and loading history."""
    history.add_record(sample_record)
    
    # Create new history instance
    new_history = RequestHistory(
        history_file=history.history_file
    )
    
    assert len(new_history.records) == 1
    assert new_history.records[0].model_dump() == sample_record.model_dump()


def test_export_and_import(history, sample_record, temp_history_dir):
    """Test exporting and importing history."""
    history.add_record(sample_record)
    
    # Export
    export_file = os.path.join(temp_history_dir, "export.json")
    success = history.export_to_file(export_file)
    assert success is True
    assert os.path.exists(export_file)
    
    # Import into new history
    new_history = RequestHistory(
        history_file=Path(os.path.join(temp_history_dir, "new")) / "requests.json"
    )
    success = new_history.import_from_file(export_file)
    
    assert success is True
    assert len(new_history.records) == 1
    assert new_history.records[0].model_dump() == sample_record.model_dump()


def test_json_serialization(history, sample_record):
    """Тест сериализации в JSON."""
    # Проверяем, что запись может быть сериализована
    try:
        json_str = json.dumps(
            sample_record.dict(),
            default=history._json_serializer
        )
        assert isinstance(json_str, str)
        
        # Проверяем, что datetime сериализуется корректно
        data = json.loads(json_str)
        assert isinstance(data["timestamp"], str)
    except Exception as e:
        pytest.fail(f"JSON serialization failed: {str(e)}")


def test_search_in_body(history):
    """Тест поиска в теле запроса/ответа."""
    # Тестируем различные типы данных
    assert history._search_in_body({"key": "test value"}, "test") is True
    assert history._search_in_body(["test", "value"], "value") is True
    assert history._search_in_body("test string", "string") is True
    assert history._search_in_body(123, "123") is True
    assert history._search_in_body(None, "test") is False
    assert history._search_in_body({"key": "value"}, "missing") is False 