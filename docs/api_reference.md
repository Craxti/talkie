# Talkie API Reference

This document contains a detailed description of the Talkie programming interface for developers who want to extend or integrate Talkie with other applications.

## Main Components

Talkie consists of the following main components:

1. **CLI** - Command line interface (`talkie.cli.main`)
2. **Core** - Core with main HTTP client functions (`talkie.core`)
3. **Utils** - Helper utilities and tools (`talkie.utils`)

## talkie.core

### HttpClient

Main HTTP client for executing requests.

```python
from talkie.core.client import HttpClient

# Create client instance
client = HttpClient(timeout=30, verify=True, follow_redirects=True)

# Execute GET request
response = client.get("https://api.example.com/users", 
                      headers={"Accept": "application/json"})

# Execute POST request
response = client.post("https://api.example.com/users",
                       json_data={"name": "John Doe"})

# Close client
client.close()
```

#### Methods

- `request(method, url, headers=None, params=None, json_data=None, data=None, files=None)` - Execute HTTP request
- `get(url, headers=None, params=None)` - Execute GET request
- `post(url, headers=None, params=None, json_data=None, data=None, files=None)` - Execute POST request
- `close()` - Close HTTP connection

### RequestBuilder

HTTP request builder.

```python
from talkie.core.request_builder import RequestBuilder

# Create request builder
builder = RequestBuilder()

# Configure request
builder.method("GET").url("https://api.example.com/users")
builder.header("Accept", "application/json")
builder.param("page", "1")

# Get ready request
request = builder.build()
```

#### Methods

- `method(method)` - Set HTTP method
- `url(url)` - Set request URL
- `header(name, value)` - Add request header
- `headers(headers_dict)` - Add multiple headers
- `param(name, value)` - Add request parameter
- `params(params_dict)` - Add multiple parameters
- `json(data)` - Set request JSON data
- `form(data)` - Set form data
- `file(name, file_path)` - Add file to request
- `build()` - Build and return ready request

### WebSocketClient

Client for working with WebSocket connections.

```python
import asyncio
from talkie.core.websocket_client import WebSocketClient

async def main():
    # Create WebSocket client
    client = WebSocketClient("wss://echo.websocket.org")
    
    # Connect
    await client.connect()
    
    # Send message
    await client.send("Hello, WebSocket!")
    
    # Get response
    response = await client.receive()
    print(f"Received: {response.data}")
    
    # Close connection
    await client.disconnect()

asyncio.run(main())
```

#### Methods

- `connect()` - Establish WebSocket connection
- `disconnect()` - Close WebSocket connection
- `send(message)` - Send message
- `receive()` - Receive message
- `stream()` - Get message stream
- `on(event, handler)` - Register event handler
- `off(event, handler)` - Unregister event handler

## talkie.utils

### openapi

Module for working with OpenAPI specifications.

```python
from talkie.utils.openapi import load_openapi_spec, extract_endpoints

# Load specification
spec = load_openapi_spec("openapi.json")

# Extract endpoints
endpoints = extract_endpoints(spec)
```

#### Functions

- `load_openapi_spec(spec_path)` - Load specification from file
- `validate_openapi_spec(spec)` - Validate specification
- `extract_endpoints(spec)` - Extract endpoint list from specification
- `extract_endpoint_details(spec, path, method)` - Extract endpoint details
- `format_openapi_spec(spec)` - Format specification for display

### history

Module for saving and managing HTTP request history.

```python
from talkie.utils.history import RequestHistory, RequestRecord

# Create history manager
history = RequestHistory()

# Create request record
record = RequestRecord(
    method="GET",
    url="https://api.example.com/users",
    response_status=200
)

# Add record to history
history.add_record(record)

# Search in history
results = history.search(method="GET", status_range=(200, 299))
```

#### Classes

**RequestRecord**
- Model for storing data about executed HTTP request

**RequestHistory**
- `add_record(record)` - Add record to history
- `get_record(record_id)` - Get record by ID
- `delete_record(record_id)` - Delete record from history
- `clear()` - Clear all history
- `search(...)` - Search in history
- `get_all(limit=None)` - Get all records
- `save()` - Save history to file
- `load()` - Load history from file
- `export_to_file(file_path)` - Export history to file
- `import_from_file(file_path, replace=False)` - Import history from file

### graphql

Module for working with GraphQL requests.

```python
from talkie.utils.graphql import GraphQLClient, GraphQLQuery

# Create GraphQL client
client = GraphQLClient("https://api.example.com/graphql")

# Create query
query = """
query GetUsers {
    users {
        id
        name
    }
}
"""

# Execute query
response = client.execute(query)

# Process results
if response.data:
    users = response.data.get("users", [])
    for user in users:
        print(f"User: {user['name']}")
```

#### Classes

**GraphQLClient**
- `execute(query, variables=None, operation_name=None)` - Execute GraphQL query
- `extract_variables(query)` - Extract variables from query
- `extract_operation_name(query)` - Extract operation name from query
- `validate_query(query)` - Check query syntax
- `format_query(query)` - Format query
- `build_query(operation_type, operation_name, fields, variables=None)` - Build query

**GraphQLIntrospection**
- `fetch_schema()` - Get GraphQL API schema
- `get_query_type()` - Get root query type
- `get_mutation_type()` - Get root mutation type
- `get_type_by_name(name)` - Get type by name
- `get_queries()` - Get list of available queries
- `get_mutations()` - Get list of available mutations

## talkie.cli

### main

Module with command line interface.

```python
import typer
from talkie.cli.main import app

# Run application
if __name__ == "__main__":
    app()
```

#### CLI Commands

- `get [URL]` - Execute GET request
- `post [URL]` - Execute POST request
- `put [URL]` - Execute PUT request
- `delete [URL]` - Execute DELETE request
- `patch [URL]` - Execute PATCH request
- `head [URL]` - Execute HEAD request
- `options [URL]` - Execute OPTIONS request
- `curl [URL]` - Generate curl command
- `openapi [SPEC]` - Analyze OpenAPI specification
- `format [FILE]` - Format file
- `ws [URL]` - Connect to WebSocket server
- `history` - Manage request history
- `config` - Manage configuration
- `graphql [URL]` - Execute GraphQL query

## Usage Examples

### Basic HTTP Request

```python
from talkie.core.client import HttpClient

client = HttpClient()
response = client.get("https://api.example.com/users")

print(f"Status: {response.status_code}")
print(f"Data: {response.json()}")
```

### Building Complex Request

```python
from talkie.core.request_builder import RequestBuilder
from talkie.core.client import HttpClient

builder = RequestBuilder()
builder.method("POST").url("https://api.example.com/users")
builder.header("Content-Type", "application/json")
builder.json({"name": "John Doe", "email": "john@example.com"})

request = builder.build()

client = HttpClient()
response = client.request(**request)
```

### Working with WebSocket

```python
import asyncio
from talkie.core.websocket_client import WebSocketClient, WebSocketMessage

async def handle_message(message):
    print(f"Received: {message.data}")

async def main():
    client = WebSocketClient("wss://echo.websocket.org")
    
    # Register message handler
    client.on("message", handle_message)
    
    # Connect
    await client.connect()
    
    # Send message
    await client.send("Hello, WebSocket!")
    
    # Wait 5 seconds for response
    await asyncio.sleep(5)
    
    # Close connection
    await client.disconnect()

asyncio.run(main())
```

### Working with Request History

```python
from talkie.utils.history import RequestHistory, RequestRecord
import datetime

# Create history manager
history = RequestHistory()

# Create record
record = RequestRecord(
    method="GET",
    url="https://api.example.com/users",
    response_status=200,
    response_body={"users": [{"id": 1, "name": "John"}]},
    timestamp=datetime.datetime.now(),
    duration_ms=120
)

# Add record
history.add_record(record)

# Search in history
yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
today = datetime.datetime.now()
results = history.search(
    method="GET",
    status_range=(200, 299),
    time_range=(yesterday, today)
)

# Output results
for record in results:
    print(f"{record.method} {record.url} -> {record.response_status}")
```

### Working with GraphQL

```python
from talkie.utils.graphql import GraphQLClient, GraphQLResponse

# Create client
client = GraphQLClient("https://api.example.com/graphql")

# Query with variables
query = """
query GetUser($id: ID!) {
    user(id: $id) {
        name
        email
        posts {
            id
            title
        }
    }
}
"""

variables = {"id": "123"}

# Execute query
response = client.execute(query, variables)

# Process results
if response.data:
    user = response.data.get("user")
    if user:
        print(f"User: {user['name']}")
        print(f"Email: {user['email']}")
        print("Posts:")
        for post in user.get("posts", []):
            print(f"  - {post['title']}")
``` 