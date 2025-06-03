# Использование Talkie

## Параллельное выполнение запросов

Talkie позволяет выполнять несколько HTTP-запросов параллельно, что значительно экономит время при работе с множественными API-вызовами.

### Основное использование

Наиболее простой способ использования параллельных запросов — создать файл со списком запросов:

```bash
# Создаем файл с запросами
cat > requests.txt << EOF
GET https://jsonplaceholder.typicode.com/posts/1
GET https://jsonplaceholder.typicode.com/posts/2
GET https://jsonplaceholder.typicode.com/posts/3
GET https://jsonplaceholder.typicode.com/users/1
GET https://jsonplaceholder.typicode.com/users/2
EOF

# Выполняем запросы параллельно
talkie parallel -f requests.txt
```

### Формат файла запросов

Каждая строка файла должна содержать HTTP-метод и URL, разделенные пробелом:

```
METHOD URL
```

Например:

```
GET https://api.example.com/users/1
POST https://api.example.com/users
PUT https://api.example.com/users/1
DELETE https://api.example.com/users/2
```

Комментарии в файле начинаются с символа `#`:

```
# Это комментарий
GET https://api.example.com/users/1  # Это тоже комментарий
```

### Управление параллелизмом

Вы можете контролировать количество одновременно выполняемых запросов с помощью опции `--concurrency`:

```bash
# Максимум 5 одновременных запросов
talkie parallel -f requests.txt --concurrency 5
```

Для распределения нагрузки можно добавить задержку между запросами:

```bash
# Задержка 0.5 секунды между запросами
talkie parallel -f requests.txt --delay 0.5
```

### Сохранение результатов

Результаты параллельных запросов можно сохранить в отдельные файлы:

```bash
# Сохранение в директорию ./results
talkie parallel -f requests.txt --output-dir ./results
```

Для каждого запроса будет создан отдельный файл с именем вида `req_N.txt`, содержащий статус, заголовки и тело ответа.

### Выполнение запросов из командной строки

Вместо файла можно указать запросы непосредственно в командной строке:

```bash
# Выполнение нескольких GET-запросов
talkie parallel -X GET -u "/posts/1" -u "/posts/2" -u "/users/1" -b "https://jsonplaceholder.typicode.com"
```

Здесь:
- `-X GET` — HTTP-метод для всех запросов
- `-u "/posts/1"` — относительные пути (можно указать несколько)
- `-b "https://jsonplaceholder.typicode.com"` — базовый URL для всех запросов

### Отображение прогресса и сводки

Talkie показывает прогресс выполнения запросов и выводит сводку после завершения:

```
Сводка по результатам:
Всего запросов: 5
Успешно выполнено: 5

Коды ответа:
  200: 5

Результаты сохранены в директорию: ./results
```

Для отключения вывода сводки используйте флаг `--no-summary`:

```bash
talkie parallel -f requests.txt --no-summary
```

### Примеры использования

#### Мониторинг множества сервисов

```bash
# Проверка доступности нескольких сервисов
cat > healthchecks.txt << EOF
GET https://service1.example.com/health
GET https://service2.example.com/health
GET https://service3.example.com/health
GET https://service4.example.com/health
EOF

talkie parallel -f healthchecks.txt --concurrency 10
```

#### Пакетное получение данных

```bash
# Получение данных по нескольким пользователям
cat > users.txt << EOF
GET https://api.example.com/users/1
GET https://api.example.com/users/2
GET https://api.example.com/users/3
GET https://api.example.com/users/4
GET https://api.example.com/users/5
EOF

talkie parallel -f users.txt --output-dir ./users_data
```

#### Загрузка множества ресурсов

```bash
# Загрузка нескольких изображений
talkie parallel -X GET \
  -u "/logo.png" \
  -u "/banner.jpg" \
  -u "/icon.svg" \
  -b "https://static.example.com" \
  --output-dir ./images
```

### Обработка ошибок

При возникновении ошибок в запросах, Talkie продолжит выполнение остальных запросов и включит информацию об ошибках в сводку:

```
Сводка по результатам:
Всего запросов: 5
Успешно выполнено: 3
Завершилось с ошибками: 2

Ошибки:
  req_2: ConnectTimeout: Connection timed out
  req_4: ConnectError: Connection refused

Коды ответа:
  200: 3
``` 