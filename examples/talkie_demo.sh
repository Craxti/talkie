#!/bin/bash
# talkie_demo.sh - Комплексная демонстрация функциональности Talkie HTTP-клиента
#
# Этот скрипт демонстрирует основные возможности Talkie для работы с HTTP-запросами
# и управления конфигурацией. Каждый раздел содержит комментарии, объясняющие
# выполняемые команды.

# Создаем директорию для выходных файлов
mkdir -p ./demo_output

# Функция для отображения заголовков разделов
show_header() {
    echo -e "\n\033[1;36m=== $1 ===\033[0m"
    echo -e "\033[0;90m$2\033[0m\n"
}

# Функция для отображения планируемых функций
show_planned_feature() {
    echo -e "\n\033[1;33m⭐ ПЛАНИРУЕМАЯ ФУНКЦИЯ ⭐\033[0m"
    echo -e "\033[0;90mСледующий пример демонстрирует, как будет работать функциональность, которая находится в разработке\033[0m\n"
}

# ---------- ЧАСТЬ 1: БАЗОВЫЕ HTTP-ЗАПРОСЫ ----------

show_header "БАЗОВЫЕ HTTP-ЗАПРОСЫ" "Демонстрация основных HTTP-методов: GET, POST, PUT, DELETE"

echo -e "\033[0;33m# Простой GET-запрос - получение данных о посте\033[0m"
talkie get https://jsonplaceholder.typicode.com/posts/1

echo -e "\n\033[0;33m# POST-запрос - создание нового поста с автоматическим определением типа JSON\033[0m"
talkie post https://jsonplaceholder.typicode.com/posts title="Новый пост о Talkie" body="Это демонстрация возможностей Talkie" userId:=1

echo -e "\n\033[0;33m# PUT-запрос - обновление существующего поста\033[0m"
talkie put https://jsonplaceholder.typicode.com/posts/1 title="Обновленный заголовок" body="Измененное содержание" userId:=1

echo -e "\n\033[0;33m# DELETE-запрос - удаление поста\033[0m"
talkie delete https://jsonplaceholder.typicode.com/posts/1

# ---------- ЧАСТЬ 2: ЗАГОЛОВКИ И ПАРАМЕТРЫ ----------

show_header "ЗАГОЛОВКИ И ПАРАМЕТРЫ" "Демонстрация работы с HTTP-заголовками и параметрами запроса"

echo -e "\033[0;33m# GET-запрос с настраиваемыми заголовками\033[0m"
talkie get https://httpbin.org/headers \
  -H "X-Custom-Header: demo-value" \
  -H "Accept: application/json" \
  -H "User-Agent: Talkie-Demo/1.0"

echo -e "\n\033[0;33m# GET-запрос с параметрами запроса\033[0m"
talkie get https://httpbin.org/get \
  -q "param1=value1" \
  -q "param2=value2" \
  -q "filter=active"

echo -e "\n\033[0;33m# Комбинированный запрос с заголовками и параметрами\033[0m"
talkie get https://httpbin.org/get \
  -H "Authorization: Bearer demo-token" \
  -q "page=1" \
  -q "limit=10"

# ---------- ЧАСТЬ 3: ФОРМАТЫ ВЫВОДА ----------

show_header "ФОРМАТЫ ВЫВОДА" "Демонстрация различных форматов вывода ответов"

echo -e "\033[0;33m# Подробный вывод с информацией о запросе и ответе\033[0m"
talkie get https://jsonplaceholder.typicode.com/posts/1 -v

echo -e "\n\033[0;33m# Вывод только JSON-содержимого\033[0m"
talkie get https://jsonplaceholder.typicode.com/posts/1 --json

echo -e "\n\033[0;33m# Вывод только заголовков ответа\033[0m"
talkie get https://jsonplaceholder.typicode.com/posts/1 --headers

echo -e "\n\033[0;33m# Сохранение ответа в файл\033[0m"
talkie get https://jsonplaceholder.typicode.com/posts/1 -o ./demo_output/post.json
echo "Результат сохранен в ./demo_output/post.json"

# ---------- ЧАСТЬ 4: ГЕНЕРАЦИЯ CURL-КОМАНД ----------

show_header "ГЕНЕРАЦИЯ CURL-КОМАНД" "Демонстрация генерации curl-команд для совместимости"

echo -e "\033[0;33m# Генерация эквивалентной curl-команды\033[0m"
talkie curl https://jsonplaceholder.typicode.com/posts/1

echo -e "\n\033[0;33m# Генерация curl-команды с заголовками и методом POST\033[0m"
talkie curl https://jsonplaceholder.typicode.com/posts \
  -X POST \
  -H "Content-Type: application/json" \
  -d "title=Тестовый пост" \
  -d "body=Содержимое тестового поста" \
  -d "userId:=1"

echo -e "\n\033[0;33m# Выполнение GET-запроса с отображением curl-команды\033[0m"
talkie get https://jsonplaceholder.typicode.com/posts/1 --curl

# ---------- ЧАСТЬ 5: РАБОТА С OPENAPI ----------

show_header "ИНСПЕКЦИЯ OPENAPI" "Демонстрация инспекции OpenAPI-спецификаций"

echo -e "\033[0;33m# Инспекция публичной OpenAPI-спецификации\033[0m"
talkie openapi https://petstore.swagger.io/v2/swagger.json

# ---------- ЧАСТЬ 6: ФОРМАТИРОВАНИЕ ФАЙЛОВ ----------

show_header "ФОРМАТИРОВАНИЕ ФАЙЛОВ" "Демонстрация форматирования различных типов файлов"

# Создаем тестовый JSON-файл
echo '{"name":"Talkie Demo","version":"1.0","features":["HTTP-клиент","Форматирование","OpenAPI"],"settings":{"verbose":true,"timeout":30}}' > ./demo_output/test.json

echo -e "\033[0;33m# Форматирование JSON-файла с выводом на экран\033[0m"
talkie format ./demo_output/test.json

echo -e "\n\033[0;33m# Форматирование JSON-файла и сохранение результата\033[0m"
talkie format ./demo_output/test.json -o ./demo_output/formatted.json
echo "Отформатированный JSON сохранен в ./demo_output/formatted.json"

# Создаем тестовый XML-файл
echo '<root><item id="1"><name>Элемент 1</name><enabled>true</enabled></item><item id="2"><name>Элемент 2</name><enabled>false</enabled></item></root>' > ./demo_output/test.xml

echo -e "\n\033[0;33m# Форматирование XML-файла\033[0m"
talkie format ./demo_output/test.xml -o ./demo_output/formatted.xml
echo "Отформатированный XML сохранен в ./demo_output/formatted.xml"

# ---------- ЧАСТЬ 7: УПРАВЛЕНИЕ КОНФИГУРАЦИЕЙ ----------

show_header "УПРАВЛЕНИЕ КОНФИГУРАЦИЕЙ" "Демонстрация работы с конфигурационным файлом и окружениями"

echo -e "\033[0;33m# Создание тестового конфигурационного файла\033[0m"
mkdir -p ~/.talkie
cat > ~/.talkie/config.json << EOF
{
  "default_headers": {
    "User-Agent": "Talkie-Demo/1.0",
    "Accept": "application/json"
  },
  "environments": {
    "jsonplaceholder": {
      "name": "jsonplaceholder",
      "base_url": "https://jsonplaceholder.typicode.com",
      "default_headers": {
        "X-API-Demo": "enabled"
      }
    },
    "httpbin": {
      "name": "httpbin",
      "base_url": "https://httpbin.org",
      "default_headers": {
        "X-Demo-Source": "talkie-demo-script"
      }
    }
  },
  "active_environment": "jsonplaceholder"
}
EOF
echo "Создан тестовый конфигурационный файл ~/.talkie/config.json"

echo -e "\n\033[0;33m# Использование активного окружения (jsonplaceholder)\033[0m"
talkie get /posts/1

echo -e "\n\033[0;33m# Добавление новых заголовков поверх конфигурации\033[0m"
talkie get /posts/1 -H "X-Additional-Header: test-value"

# ---------- ЧАСТЬ 8: ПАРАЛЛЕЛЬНЫЕ ЗАПРОСЫ ----------

show_header "ПАРАЛЛЕЛЬНЫЕ ЗАПРОСЫ" "Демонстрация выполнения нескольких запросов параллельно"
show_planned_feature

# Создаем тестовый файл с запросами
cat > ./demo_output/requests.txt << EOF
GET https://jsonplaceholder.typicode.com/posts/1
GET https://jsonplaceholder.typicode.com/posts/2
GET https://jsonplaceholder.typicode.com/posts/3
GET https://jsonplaceholder.typicode.com/users/1
GET https://jsonplaceholder.typicode.com/users/2
EOF

echo -e "\033[0;33m# Выполнение нескольких запросов параллельно из файла\033[0m"
echo -e "\033[0;90m# talkie parallel -f ./demo_output/requests.txt --concurrency 3\033[0m"
echo -e "[ Будет выполнено 5 запросов с максимальным параллелизмом 3 ]"

echo -e "\n\033[0;33m# Параллельное выполнение запросов с задержкой между ними\033[0m"
echo -e "\033[0;90m# talkie parallel -f ./demo_output/requests.txt --delay 0.5 --concurrency 2\033[0m"
echo -e "[ Будет выполнено 5 запросов с задержкой 0.5с и параллелизмом 2 ]"

echo -e "\n\033[0;33m# Параллельные запросы с сохранением результатов в отдельные файлы\033[0m"
echo -e "\033[0;90m# talkie parallel -f ./demo_output/requests.txt --output-dir ./demo_output/results\033[0m"
echo -e "[ Результаты будут сохранены в отдельные файлы в директории ./demo_output/results ]"

echo -e "\n\033[0;33m# Параллельные запросы с использованием шаблона URL\033[0m"
echo -e "\033[0;90m# talkie parallel --url \"https://jsonplaceholder.typicode.com/posts/{1..10}\" --concurrency 5\033[0m"
echo -e "[ Будет выполнено 10 запросов с подстановкой значений от 1 до 10 ]"

# ---------- ЧАСТЬ 9: ИНТЕРАКТИВНЫЙ РЕЖИМ ----------

show_header "ИНТЕРАКТИВНЫЙ РЕЖИМ" "Демонстрация интерактивного режима работы с историей запросов"
show_planned_feature

echo -e "\033[0;33m# Запуск Talkie в интерактивном режиме\033[0m"
echo -e "\033[0;90m# talkie interactive\033[0m"
echo -e "[ Запускает интерактивную оболочку с автодополнением и историей ]"

echo -e "\n\033[0;33m# Пример работы в интерактивном режиме\033[0m"
cat << 'EOF' | sed 's/^/    /'
talkie> get https://jsonplaceholder.typicode.com/posts/1
{
  "userId": 1,
  "id": 1,
  "title": "...",
  "body": "..."
}

talkie> !last --headers  # Повторение последнего запроса с выводом только заголовков
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
...

talkie> history  # Просмотр истории запросов
1: get https://jsonplaceholder.typicode.com/posts/1
2: get https://jsonplaceholder.typicode.com/posts/1 --headers

talkie> save history ./demo_output/session.log  # Сохранение истории запросов

talkie> env switch httpbin  # Переключение на другое окружение

talkie> exit  # Выход из интерактивного режима
EOF

echo -e "\n\033[0;33m# Восстановление сессии из файла истории\033[0m"
echo -e "\033[0;90m# talkie interactive --history ./demo_output/session.log\033[0m"
echo -e "[ Загружает ранее сохраненную историю запросов ]"

# ---------- ЧАСТЬ 10: ИНТЕГРАЦИЯ С CI/CD ----------

show_header "ИНТЕГРАЦИЯ С CI/CD" "Демонстрация интеграции с инструментами непрерывной интеграции"
show_planned_feature

# Создаем тестовый конфигурационный файл для CI/CD
cat > ./demo_output/ci-config.yml << EOF
# Пример конфигурации для CI/CD
base_url: https://api.example.com
headers:
  Authorization: Bearer \${CI_API_TOKEN}
tests:
  - name: "Проверка статуса API"
    request:
      method: GET
      path: /status
    expect:
      status: 200
      body:
        contains: "operational"
  - name: "Создание нового ресурса"
    request:
      method: POST
      path: /resources
      json:
        name: "Test Resource"
        active: true
    expect:
      status: 201
EOF

echo -e "\033[0;33m# Запуск тестов API в окружении CI/CD\033[0m"
echo -e "\033[0;90m# talkie ci run --config ./demo_output/ci-config.yml --reporter junit\033[0m"
echo -e "[ Запускает набор тестов и форматирует отчет в формате JUnit XML ]"

echo -e "\n\033[0;33m# Проверка контракта API на соответствие спецификации\033[0m"
echo -e "\033[0;90m# talkie ci validate --spec https://api.example.com/openapi.json --env production\033[0m"
echo -e "[ Проверяет соответствие API спецификации ]"

echo -e "\n\033[0;33m# Проверка бюджета производительности в CI\033[0m"
echo -e "\033[0;90m# talkie ci performance --config ./demo_output/ci-config.yml --budget 200ms\033[0m"
echo -e "[ Проверяет, что все запросы выполняются в рамках бюджета времени ]"

echo -e "\n\033[0;33m# Интеграция с GitHub Actions\033[0m"
cat << 'EOF' | sed 's/^/    /'
# .github/workflows/api-tests.yml
name: API Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install talkie
      - name: Run API tests
        run: talkie ci run --config ./tests/api-tests.yml --reporter github
        env:
          CI_API_TOKEN: ${{ secrets.API_TOKEN }}
EOF

# ---------- ЧАСТЬ 11: ТЕСТОВЫЕ СЦЕНАРИИ ----------

show_header "ТЕСТОВЫЕ СЦЕНАРИИ" "Демонстрация создания и выполнения тестовых сценариев"
show_planned_feature

# Создаем тестовый сценарий
cat > ./demo_output/test-scenario.yaml << EOF
name: "Тестовый сценарий для API пользователей"
description: "Демонстрация возможностей создания и проверки пользователей"
variables:
  base_url: https://jsonplaceholder.typicode.com
  user_id: null

steps:
  - name: "Получение списка пользователей"
    request:
      method: GET
      url: "\${base_url}/users"
    assertions:
      - "status == 200"
      - "body is array"
      - "body.length > 0"
    extract:
      first_user_id: "body[0].id"
      
  - name: "Создание нового пользователя"
    request:
      method: POST
      url: "\${base_url}/users"
      json:
        name: "Тестовый пользователь"
        email: "test@example.com"
    assertions:
      - "status == 201"
      - "body.name == 'Тестовый пользователь'"
    extract:
      user_id: "body.id"
      
  - name: "Получение созданного пользователя"
    request:
      method: GET
      url: "\${base_url}/users/\${user_id}"
    assertions:
      - "status == 200"
      - "body.email == 'test@example.com'"
EOF

echo -e "\033[0;33m# Выполнение тестового сценария\033[0m"
echo -e "\033[0;90m# talkie scenario run ./demo_output/test-scenario.yaml\033[0m"
echo -e "[ Выполняет серию взаимосвязанных запросов с проверками ]"

echo -e "\n\033[0;33m# Запись тестового сценария из интерактивной сессии\033[0m"
echo -e "\033[0;90m# talkie scenario record --output ./demo_output/recorded-scenario.yaml\033[0m"
echo -e "[ Запускает интерактивный режим с записью всех действий в сценарий ]"

echo -e "\n\033[0;33m# Запуск нескольких сценариев с параллельным выполнением\033[0m"
echo -e "\033[0;90m# talkie scenario run ./demo_output/scenarios/ --parallel 3 --reporter html\033[0m"
echo -e "[ Выполняет все сценарии из директории параллельно и создает HTML-отчет ]"

echo -e "\n\033[0;33m# Параметризация сценария с данными из файла\033[0m"
echo -e "\033[0;90m# talkie scenario run ./demo_output/test-scenario.yaml --data ./demo_output/test-data.csv\033[0m"
echo -e "[ Выполняет сценарий несколько раз с разными наборами данных ]"

# ---------- ЧАСТЬ 12: ПОДДЕРЖКА WEBSOCKET ----------

show_header "ПОДДЕРЖКА WEBSOCKET" "Демонстрация работы с WebSocket для API реального времени"
show_planned_feature

echo -e "\033[0;33m# Подключение к WebSocket-серверу и отправка сообщения\033[0m"
echo -e "\033[0;90m# talkie ws connect wss://echo.websocket.org\033[0m"
cat << 'EOF' | sed 's/^/    /'
Connected to wss://echo.websocket.org
Type 'exit' or press Ctrl+C to disconnect

> {"message": "Hello WebSocket!"}
< {"message": "Hello WebSocket!"}

> exit
Connection closed
EOF

echo -e "\n\033[0;33m# Отправка сообщения и вывод только ответа\033[0m"
echo -e "\033[0;90m# talkie ws send wss://echo.websocket.org '{\"message\": \"Hello\"}'\033[0m"
echo -e '    {"message": "Hello"}'

echo -e "\n\033[0;33m# Мониторинг WebSocket-соединения в течение указанного времени\033[0m"
echo -e "\033[0;90m# talkie ws monitor wss://stream.example.com/prices --duration 10s\033[0m"
cat << 'EOF' | sed 's/^/    /'
Monitoring wss://stream.example.com/prices for 10 seconds...
< {"symbol": "BTC", "price": 50123.45}
< {"symbol": "ETH", "price": 2987.12}
< {"symbol": "BTC", "price": 50128.33}
...
Monitoring completed. Received 15 messages.
EOF

echo -e "\n\033[0;33m# Использование WebSocket-подписок для получения обновлений\033[0m"
echo -e "\033[0;90m# talkie ws subscribe wss://stream.example.com --topic 'updates/products' --filter 'category=electronics'\033[0m"
cat << 'EOF' | sed 's/^/    /'
Subscribing to 'updates/products' with filter 'category=electronics'
Subscription established
< {"id": "prod-123", "name": "Smartphone", "price": 599.99, "in_stock": true}
< {"id": "prod-456", "name": "Laptop", "price": 1299.99, "in_stock": false}
...
EOF

# ---------- ЗАКЛЮЧЕНИЕ ----------

show_header "ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА" "Вы увидели текущие и планируемые возможности Talkie HTTP-клиента"

echo -e "Посетите документацию для получения подробной информации о доступных возможностях Talkie."
echo -e "Все выходные файлы демонстрации сохранены в директории ./demo_output/\n"

echo -e "\033[1;33mПланируемые функции:\033[0m"
echo -e " - Параллельные запросы для повышения производительности"
echo -e " - Интерактивный режим с историей запросов"
echo -e " - Интеграция с инструментами непрерывной интеграции"
echo -e " - Создание и выполнение тестовых сценариев"
echo -e " - Поддержка WebSocket для работы с API реального времени\n" 