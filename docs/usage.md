#sing Talkie

## Parallel execution of requests

Talkie allows you to execute multiple HTTP requests in parallel, which saves significant time when dealing with multiple API calls.

### Basic Use

The simplest way to use parallel queries is to create a file with a list of queries:

```bash
# Create a request file

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

### Query file format

Each line of the file must contain an HTTP method and URL, separated by a space:

```
METHOD URL
```

For example:

```
GET https://api.example.com/users/1
POST https://api.example.com/users
PUT https://api.example.com/users/1
DELETE https://api.example.com/users/2
```

Comments in the file start with the `#` character:

```
# This is a comment
GET https://api.example.com/users/1 # This is also a comment
```

### Controlling parallelism

You can control the number of concurrent requests with the `--concurrency` option:

```bash
# Maximum 5 concurrent requests
talkie parallel -f requests.txt --concurrency 5
```

To distribute the load, you can add a delay between requests:

```bash
# 0.5 second delay between requests
talkie parallel -f requests.txt --delay 0.5
```

### Saving results

You can save the results of parallel requests to separate files:

```bash
# Save to the ./results directory
talkie parallel -f requests.txt --output-dir ./results
```

For each request, a separate file will be created with a name like `req_N.txt`, containing the status, headers and body of the response.

### Executing queries from the command line

Instead of a file, you can specify queries directly on the command line:

```bash
# Executing multiple GET requests
talkie parallel -X GET -u "/posts/1" -u "/posts/2" -u "/users/1" -b "https://jsonplaceholder.typicode.com"
```

Here:
- `-X GET` — HTTP method for all requests
- `-u "/posts/1"` — relative paths (multiple can be specified)
- `-b "https://jsonplaceholder.typicode.com"` — base URL for all requests

### Displaying progress and summary

Talkie shows the progress of queries and displays a summary after completion:

```
Result summary:
Total requests: 5
Successful: 5

Response codes:
200: 5

Results saved to directory: ./results
```

To disable summary output, use the `--no-summary` flag:

```bash
talkie parallel -f requests.txt --no-summary
```

### Usage examples

#### Monitoring multiple services

```bash
# Checking availability of multiple services
cat > healthchecks.txt << EOF
GET https://service1.example.com/health
GET https://service2.example.com/health
GET https://service3.example.com/health
GET https://service4.example.com/health
EOF

talkie parallel -f healthchecks.txt --concurrency 10
```

#### Batch data retrieval

```bash
# Retrieving data for multiple users
cat > users.txt << EOF
GET https://api.example.com/users/1
GET https://api.example.com/users/2
GET https://api.example.com/users/3
GET https://api.example.com/users/4
GET https://api.example.com/users/5
EOF

talkie parallel -f users.txt --output-dir ./users_data
```

#### Loading multiple resources

```bash
# Loading multiple images
talkie parallel -X GET \
-u "/logo.png" \
-u "/banner.jpg" \
-u "/icon.svg" \
-b "https://static.example.com" \
--output-dir ./images
```

### Error handling

When an error occurs errors in requests, Talkie will continue to process the remaining requests and include the error information in the summary:

```
Result Summary:
Total Requests: 5
Successful: 3
Failed with Errors: 2

Errors:
req_2: ConnectTimeout: Connection timed out
req_4: ConnectError: Connection refused

Response Codes:
200: 3
```

# Making parallel requests

You can execute multiple requests in parallel using the `--parallel` flag:

```bash
talkie get https://api.example.com/users/1 https://api.example.com/users/2 https://api.example.com/users/3 --parallel
```