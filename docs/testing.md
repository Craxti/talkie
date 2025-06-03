# Руководство по тестированию Talkie

## Содержание
1. [Введение](#введение)
2. [Настройка тестового окружения](#настройка-тестового-окружения)
3. [Структура тестов](#структура-тестов)
4. [Запуск тестов](#запуск-тестов)
5. [Мок-сервер](#мок-сервер)
6. [Написание тестов](#написание-тестов)
7. [Известные проблемы](#известные-проблемы)

## Введение

Talkie использует `pytest` для модульного и интеграционного тестирования. Тесты охватывают все основные компоненты приложения:
- CLI интерфейс
- Построение HTTP-запросов
- Обработка ответов
- Работа с OpenAPI спецификациями
- Интеграционные тесты с мок-сервером

## Настройка тестового окружения

1. Установите зависимости для тестирования:
```bash
pip install pytest pytest-httpserver pytest-asyncio pytest-mock pytest-cov
```

2. Убедитесь, что у вас установлены все основные зависимости проекта:
```bash
pip install -r requirements.txt
```

## Структура тестов

Тесты организованы по модулям:
- `tests/test_cli.py` - тесты CLI интерфейса
- `tests/test_request_builder.py` - тесты построителя запросов
- `tests/test_integration.py` - интеграционные тесты
- `tests/test_openapi.py` - тесты работы с OpenAPI
- `tests/test_formatter.py` - тесты форматирования данных
- `tests/test_client.py` - тесты HTTP-клиента

## Запуск тестов

### Запуск всех тестов
```bash
python -m pytest tests/
```

### Запуск с подробным выводом
```bash
python -m pytest tests/ -v
```

### Запуск конкретного теста
```bash
python -m pytest tests/test_request_builder.py -v
```

### Запуск с покрытием кода
```bash
python -m pytest tests/ --cov=talkie
```

## Мок-сервер

Для интеграционных тестов используется `pytest-httpserver`. Пример настройки мок-сервера:

```python
@pytest.fixture
def mock_server(request):
    from pytest_httpserver import HTTPServer
    
    server = HTTPServer()
    server.start()
    
    # Настройка ответов
    server.expect_request("/api/users", method="GET").respond_with_json([
        {"id": 1, "name": "User 1"},
        {"id": 2, "name": "User 2"}
    ])
    
    yield server
    server.stop()
```

## Написание тестов

### Основные принципы
1. Каждый тест должен быть независимым
2. Используйте говорящие имена для тестов
3. Следуйте паттерну AAA (Arrange-Act-Assert)
4. Используйте фикстуры для общего кода

### Пример теста
```python
def test_parse_headers():
    """Тест разбора заголовков."""
    headers = [
        "Content-Type: application/json",
        "Authorization: Bearer token123"
    ]
    
    builder = RequestBuilder(
        method="GET",
        url="https://example.com/api",
        headers=headers
    )
    
    assert builder.headers == {
        "Content-Type": "application/json",
        "Authorization": "Bearer token123"
    }
```

### Тестирование граничных случаев
Обязательно тестируйте:
- Пустые значения
- Некорректные данные
- Специальные символы
- Граничные значения
- Дублирующиеся данные

## Известные проблемы

1. Предупреждение о deprecated методе в OpenAPI валидаторе:
   - Исправлено путем замены `validate_spec` на `validate`

2. Асинхронные тесты:
   - При написании асинхронных тестов используйте `@pytest.mark.asyncio`
   - Настройте область видимости цикла событий в `conftest.py`

3. Временные файлы:
   - Используйте `tempfile` для создания временных файлов
   - Убедитесь, что файлы удаляются после тестов 