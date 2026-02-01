# Architecture

This document describes the architecture of Talkie.

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI (talkie / tlk)                        │
│                    talkie.cli.main / __main__                     │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Core Layer                              │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────────┐  │
│  │ HttpClient  │ │RequestBuilder│ │ ResponseFormatter       │  │
│  └─────────────┘ └──────────────┘ └─────────────────────────┘  │
│  ┌─────────────────┐ ┌──────────────────┐                     │
│  │ AsyncClient     │ │ WebSocketClient   │                     │
│  └─────────────────┘ └──────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Utils Layer                              │
│  config │ formatter │ curl_generator │ openapi │ graphql        │
│  history │ colors │ logger │ cache │ validators │ error_handler │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      External Dependencies                       │
│  httpx │ typer │ rich │ pydantic │ pyyaml │ websockets          │
└─────────────────────────────────────────────────────────────────┘
```

## Component Diagram (Mermaid)

```mermaid
flowchart TB
    subgraph CLI["CLI Layer"]
        Main["main()"]
        Commands["get, post, put, delete\ncurl, openapi, format\nws, graphql, history, parallel"]
    end

    subgraph Core["Core Layer"]
        HttpClient["HttpClient"]
        RequestBuilder["RequestBuilder"]
        ResponseFormatter["ResponseFormatter"]
        WebSocketClient["WebSocketClient"]
        AsyncClient["AsyncClient"]
    end

    subgraph Utils["Utils Layer"]
        Config["config"]
        Formatter["formatter"]
        CurlGen["curl_generator"]
        OpenAPI["openapi"]
        GraphQL["graphql"]
        History["history"]
        Cache["cache"]
        Logger["logger"]
    end

    Main --> Commands
    Commands --> HttpClient
    Commands --> WebSocketClient
    Commands --> RequestBuilder
    HttpClient --> ResponseFormatter
    HttpClient --> Config
    HttpClient --> Cache
    RequestBuilder --> Config
    ResponseFormatter --> Formatter
    ResponseFormatter --> Utils
```

## Request Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Config
    participant RequestBuilder
    participant HttpClient
    participant Cache
    participant API

    User->>CLI: talkie get /users
    CLI->>Config: get base_url, headers
    CLI->>RequestBuilder: build request
    RequestBuilder->>RequestBuilder: add env base_url
    CLI->>Cache: check cache
    alt Cache hit
        Cache-->>CLI: cached response
        CLI-->>User: formatted output
    else Cache miss
        CLI->>HttpClient: execute request
        HttpClient->>API: HTTP GET
        API-->>HttpClient: response
        HttpClient->>Cache: store response
        HttpClient-->>CLI: response
        CLI-->>User: formatted output
    end
```

## Module Dependencies

```mermaid
graph LR
    cli[cli.main] --> client[core.client]
    cli --> builder[core.request_builder]
    cli --> formatter[core.response_formatter]
    cli --> config[utils.config]
    cli --> output[cli.output]

    client --> httpx[httpx]
    client --> config
    client --> cache[utils.cache]

    formatter --> formatter_util[utils.formatter]
    formatter --> colors[utils.colors]

    config --> pydantic[pydantic]
    formatter_util --> rich[rich]
```

## Directory Structure

```
talkie/
├── __init__.py
├── __main__.py              # Entry point
├── cli/
│   ├── main.py              # CLI commands
│   └── output.py            # Output formatting
├── core/
│   ├── client.py            # HTTP client (sync)
│   ├── async_client.py      # HTTP client (async)
│   ├── request_builder.py    # Request construction
│   ├── response_formatter.py # Response formatting
│   └── websocket_client.py   # WebSocket support
└── utils/
    ├── config.py            # Configuration
    ├── formatter.py         # Data formatting
    ├── curl_generator.py    # Curl command generation
    ├── openapi.py           # OpenAPI inspection
    ├── graphql.py           # GraphQL support
    ├── history.py           # Request history
    ├── cache.py             # Response caching
    ├── colors.py            # Terminal colors
    ├── logger.py            # Logging
    ├── validators.py        # Input validation
    └── error_handler.py     # Error handling
```

## Data Flow

1. **CLI** parses arguments and routes to appropriate handler
2. **Config** provides base URL, headers from active environment
3. **RequestBuilder** constructs full request (URL + params + headers + body)
4. **Cache** checks for cached response (if enabled)
5. **HttpClient** executes request via httpx
6. **ResponseFormatter** formats output (JSON/XML/HTML syntax highlighting)
7. **Output** displays to user via Rich console
