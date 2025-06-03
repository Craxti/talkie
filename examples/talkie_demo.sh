#!/bin/bash
# talkie_demo.sh - Comprehensive demonstration of Talkie HTTP client functionality
#
# This script demonstrates the main capabilities of Talkie for working with HTTP requests
# and managing configuration. Each section contains comments explaining
# the commands being executed.

# Create output directory
mkdir -p ./demo_output

# Function to display section headers
show_header() {
    echo -e "\n\033[1;36m=== $1 ===\033[0m"
    echo -e "\033[0;90m$2\033[0m\n"
}

# Function to display planned features
show_planned_feature() {
    echo -e "\n\033[1;33m⭐ PLANNED FEATURE ⭐\033[0m"
    echo -e "\033[0;90mThe next example demonstrates how the functionality that is under development will work\033[0m\n"
}

# ---------- PART 1: BASIC HTTP-REQUESTS ----------

show_header "BASIC HTTP-REQUESTS" "Demonstration of basic HTTP methods: GET, POST, PUT, DELETE"

echo -e "\033[0;33m# Simple GET-request - getting data about a post\033[0m"
talkie get https://jsonplaceholder.typicode.com/posts/1

echo -e "\n\033[0;33m# POST-request - creating a new post with automatic JSON type detection\033[0m"
talkie post https://jsonplaceholder.typicode.com/posts title="New post about Talkie" body="This is a demonstration of Talkie's capabilities" userId:=1

echo -e "\n\033[0;33m# PUT-request - updating an existing post\033[0m"
talkie put https://jsonplaceholder.typicode.com/posts/1 title="Updated title" body="Changed content" userId:=1

echo -e "\n\033[0;33m# DELETE-request - deleting a post\033[0m"
talkie delete https://jsonplaceholder.typicode.com/posts/1

# ---------- PART 2: HEADERS AND PARAMETERS ----------

show_header "HEADERS AND PARAMETERS" "Demonstration of working with HTTP headers and request parameters"

echo -e "\033[0;33m# GET-request with custom headers\033[0m"
talkie get https://httpbin.org/headers \
  -H "X-Custom-Header: demo-value" \
  -H "Accept: application/json" \
  -H "User-Agent: Talkie-Demo/1.0"

echo -e "\n\033[0;33m# GET-request with request parameters\033[0m"
talkie get https://httpbin.org/get \
  -q "param1=value1" \
  -q "param2=value2" \
  -q "filter=active"

echo -e "\n\033[0;33m# Combined request with headers and parameters\033[0m"
talkie get https://httpbin.org/get \
  -H "Authorization: Bearer demo-token" \
  -q "page=1" \
  -q "limit=10"

# ---------- PART 3: OUTPUT FORMATS ----------

show_header "OUTPUT FORMATS" "Demonstration of different output formats of responses"

echo -e "\033[0;33m# Detailed output with information about the request and response\033[0m"
talkie get https://jsonplaceholder.typicode.com/posts/1 -v

echo -e "\n\033[0;33m# Output only JSON-content\033[0m"
talkie get https://jsonplaceholder.typicode.com/posts/1 --json

echo -e "\n\033[0;33m# Output only response headers\033[0m"
talkie get https://jsonplaceholder.typicode.com/posts/1 --headers

echo -e "\n\033[0;33m# Saving response to file\033[0m"
talkie get https://jsonplaceholder.typicode.com/posts/1 -o ./demo_output/post.json
echo "Result saved in ./demo_output/post.json"

# ---------- PART 4: CURL COMMAND GENERATION ----------

show_header "CURL COMMAND GENERATION" "Demonstration of generating curl commands for compatibility"

echo -e "\033[0;33m# Generating equivalent curl command\033[0m"
talkie curl https://jsonplaceholder.typicode.com/posts/1

echo -e "\n\033[0;33m# Generating curl command with headers and POST method\033[0m"
talkie curl https://jsonplaceholder.typicode.com/posts \
  -X POST \
  -H "Content-Type: application/json" \
  -d "title=Test post" \
  -d "body=Content of test post" \
  -d "userId:=1"

echo -e "\n\033[0;33m# Executing GET-request with curl command display\033[0m"
talkie get https://jsonplaceholder.typicode.com/posts/1 --curl

# ---------- PART 5: OPENAPI INSPECTION ----------

show_header "OPENAPI INSPECTION" "Demonstration of inspecting OpenAPI specifications"

echo -e "\033[0;33m# Inspection of public OpenAPI specification\033[0m"
talkie openapi https://petstore.swagger.io/v2/swagger.json

# ---------- PART 6: FILE FORMATTING ----------

show_header "FILE FORMATTING" "Demonstration of formatting different types of files"

# Create test JSON file
echo '{"name":"Talkie Demo","version":"1.0","features":["HTTP-client","Formatting","OpenAPI"],"settings":{"verbose":true,"timeout":30}}' > ./demo_output/test.json

echo -e "\033[0;33m# Formatting JSON file with output to screen\033[0m"
talkie format ./demo_output/test.json

echo -e "\n\033[0;33m# Formatting JSON file and saving result\033[0m"
talkie format ./demo_output/test.json -o ./demo_output/formatted.json
echo "Formatted JSON saved in ./demo_output/formatted.json"

# Create test XML file
echo '<root><item id="1"><name>Item 1</name><enabled>true</enabled></item><item id="2"><name>Item 2</name><enabled>false</enabled></item></root>' > ./demo_output/test.xml

echo -e "\n\033[0;33m# Formatting XML file\033[0m"
talkie format ./demo_output/test.xml -o ./demo_output/formatted.xml
echo "Formatted XML saved in ./demo_output/formatted.xml"

# ---------- PART 7: CONFIGURATION MANAGEMENT ----------

show_header "CONFIGURATION MANAGEMENT" "Demonstration of working with configuration file and environments"

echo -e "\033[0;33m# Creating test configuration file\033[0m"
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
echo "Created test configuration file ~/.talkie/config.json"

echo -e "\n\033[0;33m# Using active environment (jsonplaceholder)\033[0m"
talkie get /posts/1

echo -e "\n\033[0;33m# Adding new headers on top of configuration\033[0m"
talkie get /posts/1 -H "X-Additional-Header: test-value"

# ---------- PART 8: PARALLEL REQUESTS ----------

show_header "PARALLEL REQUESTS" "Demonstration of executing multiple requests in parallel"
show_planned_feature

# Create test file with requests
cat > ./demo_output/requests.txt << EOF
GET https://jsonplaceholder.typicode.com/posts/1
GET https://jsonplaceholder.typicode.com/posts/2
GET https://jsonplaceholder.typicode.com/posts/3
GET https://jsonplaceholder.typicode.com/users/1
GET https://jsonplaceholder.typicode.com/users/2
EOF

echo -e "\033[0;33m# Executing multiple requests in parallel from file\033[0m"
echo -e "\033[0;90m# talkie parallel -f ./demo_output/requests.txt --concurrency 3\033[0m"
echo -e "[ Will execute 5 requests with maximum concurrency 3 ]"

echo -e "\n\033[0;33m# Parallel execution of requests with delay between them\033[0m"
echo -e "\033[0;90m# talkie parallel -f ./demo_output/requests.txt --delay 0.5 --concurrency 2\033[0m"
echo -e "[ Will execute 5 requests with delay 0.5s and concurrency 2 ]"

echo -e "\n\033[0;33m# Parallel requests with saving results to separate files\033[0m"
echo -e "\033[0;90m# talkie parallel -f ./demo_output/requests.txt --output-dir ./demo_output/results\033[0m"
echo -e "[ Results will be saved to separate files in directory ./demo_output/results ]"

echo -e "\n\033[0;33m# Parallel requests with using URL template\033[0m"
echo -e "\033[0;90m# talkie parallel --url \"https://jsonplaceholder.typicode.com/posts/{1..10}\" --concurrency 5\033[0m"
echo -e "[ Will execute 10 requests with substituting values from 1 to 10 ]"

# ---------- PART 9: INTERACTIVE MODE ----------

show_header "INTERACTIVE MODE" "Demonstration of interactive mode of working with request history"
show_planned_feature

echo -e "\033[0;33m# Starting Talkie in interactive mode\033[0m"
echo -e "\033[0;90m# talkie interactive\033[0m"
echo -e "[ Starts interactive shell with auto-completion and history ]"

echo -e "\n\033[0;33m# Example of working in interactive mode\033[0m"
cat << 'EOF' | sed 's/^/    /'
talkie> get https://jsonplaceholder.typicode.com/posts/1
{
  "userId": 1,
  "id": 1,
  "title": "...",
  "body": "..."
}

talkie> !last --headers  # Repeating last request with output only headers
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
...

talkie> history  # Viewing request history
1: get https://jsonplaceholder.typicode.com/posts/1
2: get https://jsonplaceholder.typicode.com/posts/1 --headers

talkie> save history ./demo_output/session.log  # Saving request history

talkie> env switch httpbin  # Switching to another environment

talkie> exit  # Exit from interactive mode
EOF

echo -e "\n\033[0;33m# Restoring session from request history file\033[0m"
echo -e "\033[0;90m# talkie interactive --history ./demo_output/session.log\033[0m"
echo -e "[ Loads previously saved request history ]"

# ---------- PART 10: INTEGRATION WITH CI/CD ----------

show_header "INTEGRATION WITH CI/CD" "Demonstration of integration with continuous integration tools"
show_planned_feature

# Create test configuration file for CI/CD
cat > ./demo_output/ci-config.yml << EOF
# Example configuration for CI/CD
base_url: https://api.example.com
headers:
  Authorization: Bearer \${CI_API_TOKEN}
tests:
  - name: "Checking API status"
    request:
      method: GET
      path: /status
    expect:
      status: 200
      body:
        contains: "operational"
  - name: "Creating new resource"
    request:
      method: POST
      path: /resources
      json:
        name: "Test Resource"
        active: true
    expect:
      status: 201
EOF

echo -e "\033[0;33m# Running API tests in CI/CD environment\033[0m"
echo -e "\033[0;90m# talkie ci run --config ./demo_output/ci-config.yml --reporter junit\033[0m"
echo -e "[ Runs set of tests and formats report in JUnit XML format ]"

echo -e "\n\033[0;33m# Checking API contract against specification\033[0m"
echo -e "\033[0;90m# talkie ci validate --spec https://api.example.com/openapi.json --env production\033[0m"
echo -e "[ Checks API against specification ]"

echo -e "\n\033[0;33m# Checking performance budget in CI\033[0m"
echo -e "\033[0;90m# talkie ci performance --config ./demo_output/ci-config.yml --budget 200ms\033[0m"
echo -e "[ Checks that all requests are executed within time budget ]"

echo -e "\n\033[0;33m# Integration with GitHub Actions\033[0m"
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

# ---------- PART 11: TEST SCENARIOS ----------

show_header "TEST SCENARIOS" "Demonstration of creating and executing test scenarios"
show_planned_feature

# Create test scenario
cat > ./demo_output/test-scenario.yaml << EOF
name: "Test scenario for API users"
description: "Demonstration of creating and checking users"
variables:
  base_url: https://jsonplaceholder.typicode.com
  user_id: null

steps:
  - name: "Getting user list"
    request:
      method: GET
      url: "\${base_url}/users"
    assertions:
      - "status == 200"
      - "body is array"
      - "body.length > 0"
    extract:
      first_user_id: "body[0].id"
      
  - name: "Creating new user"
    request:
      method: POST
      url: "\${base_url}/users"
      json:
        name: "Test user"
        email: "test@example.com"
    assertions:
      - "status == 201"
      - "body.name == 'Test user'"
    extract:
      user_id: "body.id"
      
  - name: "Getting created user"
    request:
      method: GET
      url: "\${base_url}/users/\${user_id}"
    assertions:
      - "status == 200"
      - "body.email == 'test@example.com'"
EOF

echo -e "\033[0;33m# Executing test scenario\033[0m"
echo -e "\033[0;90m# talkie scenario run ./demo_output/test-scenario.yaml\033[0m"
echo -e "[ Executes series of interconnected requests with checks ]"

echo -e "\n\033[0;33m# Recording test scenario from interactive session\033[0m"
echo -e "\033[0;90m# talkie scenario record --output ./demo_output/recorded-scenario.yaml\033[0m"
echo -e "[ Starts interactive mode with recording all actions in scenario ]"

echo -e "\n\033[0;33m# Executing multiple scenarios with parallel execution\033[0m"
echo -e "\033[0;90m# talkie scenario run ./demo_output/scenarios/ --parallel 3 --reporter html\033[0m"
echo -e "[ Executes all scenarios from directory parallel and creates HTML report ]"

echo -e "\n\033[0;33m# Scenario parameterization with data from file\033[0m"
echo -e "\033[0;90m# talkie scenario run ./demo_output/test-scenario.yaml --data ./demo_output/test-data.csv\033[0m"
echo -e "[ Executes scenario several times with different data sets ]"

# ---------- PART 12: WEBSOCKET SUPPORT ----------

show_header "WEBSOCKET SUPPORT" "Demonstration of working with WebSocket for API real-time"
show_planned_feature

echo -e "\033[0;33m# Connecting to WebSocket server and sending message\033[0m"
echo -e "\033[0;90m# talkie ws connect wss://echo.websocket.org\033[0m"
cat << 'EOF' | sed 's/^/    /'
Connected to wss://echo.websocket.org
Type 'exit' or press Ctrl+C to disconnect

> {"message": "Hello WebSocket!"}
< {"message": "Hello WebSocket!"}

> exit
Connection closed
EOF

echo -e "\n\033[0;33m# Sending message and output only response\033[0m"
echo -e "\033[0;90m# talkie ws send wss://echo.websocket.org '{\"message\": \"Hello\"}'\033[0m"
echo -e '    {"message": "Hello"}'

echo -e "\n\033[0;33m# Monitoring WebSocket connection during specified time\033[0m"
echo -e "\033[0;90m# talkie ws monitor wss://stream.example.com/prices --duration 10s\033[0m"
cat << 'EOF' | sed 's/^/    /'
Monitoring wss://stream.example.com/prices for 10 seconds...
< {"symbol": "BTC", "price": 50123.45}
< {"symbol": "ETH", "price": 2987.12}
< {"symbol": "BTC", "price": 50128.33}
...
Monitoring completed. Received 15 messages.
EOF

echo -e "\n\033[0;33m# Using WebSocket subscriptions for getting updates\033[0m"
echo -e "\033[0;90m# talkie ws subscribe wss://stream.example.com --topic 'updates/products' --filter 'category=electronics'\033[0m"
cat << 'EOF' | sed 's/^/    /'
Subscribing to 'updates/products' with filter 'category=electronics'
Subscription established
< {"id": "prod-123", "name": "Smartphone", "price": 599.99, "in_stock": true}
< {"id": "prod-456", "name": "Laptop", "price": 1299.99, "in_stock": false}
...
EOF

# ---------- CONCLUSION ----------

show_header "DEMONSTRATION COMPLETED" "You saw current and planned capabilities of Talkie HTTP client"

echo -e "Visit documentation for detailed information about available Talkie capabilities."
echo -e "All demonstration output files saved in ./demo_output/\n"

echo -e "\033[1;33mPlanned features:\033[0m"
echo -e " - Parallel requests for performance improvement"
echo -e " - Interactive mode with request history"
echo -e " - Integration with continuous integration tools"
echo -e " - Creating and executing test scenarios"
echo -e " - WebSocket support for API real-time\n" 