#!/bin/bash

# Демонстрация выполнения параллельных запросов с помощью Talkie

# Создаем каталог для вывода
mkdir -p ./demo_output
mkdir -p ./demo_output/results

# Цветовые константы для вывода
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
GRAY='\033[0;90m'

# Функция для форматированного вывода
print_header() {
    echo -e "\n${BLUE}==========================================${NC}"
    echo -e "${BLUE}>> ${YELLOW}$1${NC}"
    echo -e "${GRAY}$2${NC}"
    echo -e "${BLUE}==========================================${NC}\n"
}

# Функция для ожидания
wait_user() {
    echo -e "\n${YELLOW}Нажмите Enter, чтобы продолжить...${NC}"
    read
}

# Введение
echo -e "${GREEN}=================================================${NC}"
echo -e "${GREEN}        Демонстрация Talkie - Параллельные запросы${NC}"
echo -e "${GREEN}=================================================${NC}"
echo -e "${CYAN}Talkie позволяет выполнять HTTP-запросы параллельно,${NC}"
echo -e "${CYAN}значительно ускоряя выполнение множественных запросов.${NC}"
echo

wait_user

# Создаем тестовый файл с запросами
print_header "1. Создание файла с запросами" "Каждая строка содержит HTTP-метод и URL, разделенные пробелом"

cat > ./demo_output/requests.txt << EOF
GET https://jsonplaceholder.typicode.com/posts/1
GET https://jsonplaceholder.typicode.com/posts/2
GET https://jsonplaceholder.typicode.com/posts/3
GET https://jsonplaceholder.typicode.com/posts/4
GET https://jsonplaceholder.typicode.com/posts/5
GET https://jsonplaceholder.typicode.com/users/1
GET https://jsonplaceholder.typicode.com/users/2
GET https://jsonplaceholder.typicode.com/users/3
# Это комментарий - он будет пропущен
GET https://jsonplaceholder.typicode.com/albums/1
EOF

echo -e "${YELLOW}Содержимое файла с запросами:${NC}"
cat ./demo_output/requests.txt

wait_user

# Демонстрация базового использования
print_header "2. Базовое выполнение запросов" "Выполняем все запросы с параллелизмом по умолчанию (10)"
echo -e "${YELLOW}Выполнение запросов из файла:${NC}"
talkie parallel -f ./demo_output/requests.txt

wait_user

# Демонстрация ограничения параллелизма
print_header "3. Ограничение параллелизма" "Контролируем количество одновременно выполняемых запросов"
echo -e "${YELLOW}Выполнение с параллелизмом 2:${NC}"
talkie parallel -f ./demo_output/requests.txt --concurrency 2

wait_user

# Демонстрация задержки между запросами
print_header "4. Добавление задержки" "Добавляем задержку между запросами для снижения нагрузки"
echo -e "${YELLOW}Выполнение с задержкой 0.5 секунды между запросами:${NC}"
talkie parallel -f ./demo_output/requests.txt --delay 0.5 --concurrency 3

wait_user

# Демонстрация сохранения результатов
print_header "5. Сохранение результатов в файлы" "Каждый запрос сохраняется в отдельный файл"
echo -e "${YELLOW}Сохранение результатов в директорию:${NC}"
talkie parallel -f ./demo_output/requests.txt --output-dir ./demo_output/results

echo -e "\n${YELLOW}Проверка созданных файлов:${NC}"
ls -l ./demo_output/results/ | head -n 5

echo -e "\n${YELLOW}Пример содержимого файла:${NC}"
head -n 10 ./demo_output/results/req_1.txt

wait_user

# Демонстрация выполнения запросов из командной строки
print_header "6. Запросы из командной строки" "Выполнение без файла с указанием URL и базового URL"
echo -e "${YELLOW}Выполнение запросов к одному API с разными путями:${NC}"
talkie parallel -X GET \
  -u "/posts/1" \
  -u "/posts/2" \
  -u "/users/1" \
  -b "https://jsonplaceholder.typicode.com"

wait_user

# Демонстрация вывода без сводки
print_header "7. Дополнительные опции" "Настройка вывода и дополнительные параметры"
echo -e "${YELLOW}Выполнение без сводки результатов:${NC}"
talkie parallel -f ./demo_output/requests.txt --no-summary

wait_user

# Демонстрация обработки ошибок
print_header "8. Обработка ошибок" "Talkie продолжает выполнение даже при возникновении ошибок"

# Создаем файл с некоторыми неверными URL
cat > ./demo_output/errors.txt << EOF
GET https://jsonplaceholder.typicode.com/posts/1
GET https://non-existent-domain-123456789.com/api
GET https://jsonplaceholder.typicode.com/posts/2
GET https://localhost:9999/not-found
GET https://jsonplaceholder.typicode.com/posts/3
EOF

echo -e "${YELLOW}Содержимое файла с ошибочными запросами:${NC}"
cat ./demo_output/errors.txt

echo -e "\n${YELLOW}Выполнение запросов с обработкой ошибок:${NC}"
talkie parallel -f ./demo_output/errors.txt

wait_user

# Заключение
echo -e "${GREEN}=================================================${NC}"
echo -e "${GREEN}        Демонстрация завершена${NC}"
echo -e "${GREEN}=================================================${NC}"
echo -e "${CYAN}Talkie позволяет легко и эффективно выполнять множественные${NC}"
echo -e "${CYAN}HTTP-запросы параллельно с гибкими настройками параллелизма${NC}"
echo -e "${CYAN}и удобными опциями для контроля выполнения и вывода.${NC}"
echo

# Очистка (опционально)
# rm -rf ./demo_output 