#!/bin/bash
# Примеры использования Talkie HTTP-клиента

# Базовый GET-запрос
echo "=== Простой GET-запрос ==="
talkie get https://jsonplaceholder.typicode.com/posts/1

# GET-запрос с параметрами
echo -e "\n=== GET-запрос с параметрами ==="
talkie get https://jsonplaceholder.typicode.com/posts -q "userId=1" -q "id=5"

# GET-запрос с заголовками
echo -e "\n=== GET-запрос с заголовками ==="
talkie get https://jsonplaceholder.typicode.com/posts/1 -H "Accept: application/json" -H "X-Custom-Header: value"

# POST-запрос с JSON-данными
echo -e "\n=== POST-запрос с JSON-данными ==="
talkie post https://jsonplaceholder.typicode.com/posts title="Новый пост" body="Содержание поста" userId:=1

# PUT-запрос для обновления ресурса
echo -e "\n=== PUT-запрос для обновления ==="
talkie put https://jsonplaceholder.typicode.com/posts/1 title="Обновленный заголовок" body="Обновленное содержание" userId:=1

# DELETE-запрос
echo -e "\n=== DELETE-запрос ==="
talkie delete https://jsonplaceholder.typicode.com/posts/1

# Вывод только заголовков
echo -e "\n=== Вывод только заголовков ==="
talkie get https://jsonplaceholder.typicode.com/posts/1 --headers

# Вывод только JSON
echo -e "\n=== Вывод только JSON-содержимого ==="
talkie get https://jsonplaceholder.typicode.com/posts/1 --json

# Подробный вывод
echo -e "\n=== Подробный вывод ==="
talkie get https://jsonplaceholder.typicode.com/posts/1 -v

# Сохранение ответа в файл
echo -e "\n=== Сохранение ответа в файл ==="
talkie get https://jsonplaceholder.typicode.com/posts/1 -o post.json
echo "Ответ сохранен в файл post.json" 