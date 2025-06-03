#!/bin/bash
# Примеры использования OpenAPI-функциональности Talkie

# Инспекция спецификации OpenAPI из Petstore
echo "=== Инспекция OpenAPI из Petstore ==="
talkie openapi https://petstore.swagger.io/v2/swagger.json

# Локальная спецификация (предположим, что файл существует)
echo -e "\n=== Инспекция локальной OpenAPI-спецификации ==="
# talkie openapi ./swagger.yaml

# Получение информации об API без отображения эндпоинтов
echo -e "\n=== Инспекция OpenAPI без отображения эндпоинтов ==="
talkie openapi https://petstore.swagger.io/v2/swagger.json --no-endpoints

# Отправка запроса к эндпоинту из OpenAPI спецификации
echo -e "\n=== Отправка запроса к эндпоинту из OpenAPI спецификации ==="
talkie get https://petstore.swagger.io/v2/pet/findByStatus -q "status=available" 