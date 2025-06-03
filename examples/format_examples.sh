#!/bin/bash
# Примеры использования функциональности автоформатирования в Talkie

# Создаём тестовые файлы
echo '{"id": 1, "name": "Test", "tags": ["api", "example"], "active": true, "details": {"type": "user", "role": "admin"}}' > test.json
echo '<?xml version="1.0" encoding="UTF-8"?><root><user id="1"><name>Test</name><email>test@example.com</email><roles><role>admin</role><role>user</role></roles></user></root>' > test.xml
echo '<html><head><title>Test Page</title></head><body><h1>Hello, World!</h1><p>This is a <b>test</b> page.</p><ul><li>Item 1</li><li>Item 2</li></ul></body></html>' > test.html

# Форматирование JSON
echo "=== Форматирование JSON ==="
talkie format test.json

# Форматирование JSON и сохранение результата
echo -e "\n=== Форматирование JSON с сохранением результата ==="
talkie format test.json -o formatted.json
echo "Результат сохранен в formatted.json"

# Форматирование XML
echo -e "\n=== Форматирование XML ==="
talkie format test.xml

# Преобразование HTML в Markdown
echo -e "\n=== Преобразование HTML в Markdown ==="
talkie format test.html --type markdown

# Форматирование с явным указанием типа
echo -e "\n=== Форматирование XML с явным указанием типа ==="
talkie format test.xml --type xml

# Использование форматирования при HTTP-запросе
echo -e "\n=== Форматирование при HTTP-запросе ==="
talkie get https://jsonplaceholder.typicode.com/posts/1 --format json

# Очистка тестовых файлов
echo -e "\n=== Очистка тестовых файлов ==="
rm test.json test.xml test.html formatted.json 