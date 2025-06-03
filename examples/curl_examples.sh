#!/bin/bash
# Примеры использования функциональности генерации curl-команд в Talkie

# Простая генерация curl-команды
echo "=== Генерация curl для GET-запроса ==="
talkie curl https://jsonplaceholder.typicode.com/posts/1

# Генерация curl для POST-запроса
echo -e "\n=== Генерация curl для POST-запроса ==="
talkie curl https://jsonplaceholder.typicode.com/posts -X POST -d "title=Тестовый пост" -d "body=Содержание поста" -d "userId:=1"

# Генерация curl с заголовками
echo -e "\n=== Генерация curl с заголовками ==="
talkie curl https://jsonplaceholder.typicode.com/posts -H "Content-Type: application/json" -H "Authorization: Bearer token123"

# Генерация curl с параметрами запроса
echo -e "\n=== Генерация curl с параметрами запроса ==="
talkie curl https://jsonplaceholder.typicode.com/posts -q "userId=1" -q "_limit=3"

# Генерация с опциями verbose и insecure
echo -e "\n=== Генерация curl с дополнительными опциями ==="
talkie curl https://jsonplaceholder.typicode.com/posts -v -k

# Добавление curl-команды к обычному запросу
echo -e "\n=== Вывод curl при выполнении запроса ==="
talkie get https://jsonplaceholder.typicode.com/posts/1 --curl

# Получение только curl-команды без выполнения запроса
echo -e "\n=== Получение только curl-команды без выполнения запроса ==="
talkie get https://jsonplaceholder.typicode.com/posts/1 --curl -v 