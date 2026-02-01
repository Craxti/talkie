# CLI Reference

Complete reference for all Talkie command-line options.

## Command Overview

| Command | Description |
|---------|-------------|
| `talkie get` | GET request |
| `talkie post` | POST request |
| `talkie put` | PUT request |
| `talkie patch` | PATCH request |
| `talkie delete` | DELETE request |
| `talkie curl` | Generate curl command |
| `talkie openapi` | Inspect OpenAPI specification |
| `talkie format` | Format JSON/XML/HTML files |
| `talkie ws` | WebSocket connection |
| `talkie graphql` | GraphQL request |
| `talkie history` | Request history management |
| `talkie parallel` | Execute multiple requests in parallel |

**Alias:** `tlk` can be used instead of `talkie`.

---

## HTTP Methods: get, post, put, patch, delete

### Syntax

```bash
talkie <method> <url> [key=value ...] [options]
```

### URL

- Full URL: `https://api.example.com/users`
- Relative (with environment): `/users` — uses `base_url` from active environment

### Data Parameters

| Syntax | Type | Example |
|--------|------|---------|
| `key=value` | String | `name=John` |
| `key:=value` | Number/Boolean | `age:=30`, `active:=true` |

### Common Options

| Option | Short | Description |
|--------|-------|-------------|
| `--header` | `-H` | Add header (can repeat) |
| `--query` | `-q` | Add query parameter (can repeat) |
| `--output` | `-o` | Save response to file |
| `--verbose` | `-v` | Verbose output |
| `--json` | | Output JSON body only |
| `--headers` | | Output response headers only |
| `--format` | `-f` | Output format: json, xml, html |
| `--curl` | | Show equivalent curl command |
| `--timeout` | | Request timeout (seconds) |
| `--insecure` | `-k` | Skip SSL verification |

### Examples

```bash
# GET with headers
talkie get https://api.example.com/users -H "Authorization: Bearer TOKEN"

# POST with JSON data
talkie post https://api.example.com/users name=John age:=30

# PUT with query params
talkie put https://api.example.com/users/1 -q "dry_run=true"

# Save to file
talkie get https://api.example.com/data -o response.json
```

---

## curl — Generate curl Command

### Syntax

```bash
talkie curl <url> [options]
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--request` | `-X` | HTTP method |
| `--header` | `-H` | Add header |
| `--data` | `-d` | Request body data |
| `--query` | `-q` | Query parameters |
| `--verbose` | `-v` | Verbose output |
| `--insecure` | `-k` | Skip SSL verification |

### Examples

```bash
talkie curl https://api.example.com/users -H "Authorization: Bearer TOKEN"
talkie curl https://api.example.com/users -X POST -d "name=John" -d "age:=30"
```

---

## openapi — Inspect OpenAPI Specification

### Syntax

```bash
talkie openapi <url_or_file> [options]
```

### Arguments

- `url_or_file` — URL to OpenAPI spec (JSON/YAML) or local file path

### Options

| Option | Description |
|--------|-------------|
| `--endpoints` | List endpoints only |
| `--examples` | Generate request examples |

### Examples

```bash
talkie openapi https://api.example.com/openapi.json
talkie openapi ./openapi.yaml --endpoints
talkie openapi ./openapi.yaml --examples
```

---

## format — Format Files

### Syntax

```bash
talkie format <file> [options]
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output file |
| `--type` | `-t` | Force format: json, xml, html |

### Examples

```bash
talkie format data.json
talkie format data.json -o formatted.json
talkie format data.txt -t json
```

---

## ws — WebSocket Connection

### Syntax

```bash
talkie ws <url> [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--send` | Message to send |
| `--header` | `-H` | Add header |

### Examples

```bash
talkie ws wss://echo.websocket.org
talkie ws wss://echo.websocket.org --send "Hello"
talkie ws wss://api.example.com/ws -H "Authorization: Bearer TOKEN"
```

---

## graphql — GraphQL Requests

### Syntax

```bash
talkie graphql <url> [options]
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--query` | `-q` | GraphQL query string |
| `--file` | `-f` | Query from file |
| `--variable` | `-v` | Variable (key=value, can repeat) |
| `--header` | `-H` | Add header |

### Examples

```bash
talkie graphql https://api.example.com/graphql -q "query { users { id name } }"
talkie graphql https://api.example.com/graphql -f query.graphql -v id=123
```

---

## history — Request History

### Subcommands

| Subcommand | Description |
|------------|-------------|
| `list` | Show history |
| `search` | Search history |
| `repeat` | Repeat request by ID |
| `export` | Export to file |
| `import` | Import from file |

### history list

```bash
talkie history list [--limit N]
```

| Option | Description |
|--------|-------------|
| `--limit` | Max number of entries |

### history search

```bash
talkie history search [--method METHOD] [--url PATTERN] [--status CODE]
```

| Option | Description |
|--------|-------------|
| `--method` | Filter by HTTP method |
| `--url` | Filter by URL pattern |
| `--status` | Filter by response status |

### history repeat

```bash
talkie history repeat <request_id>
```

### history export / import

```bash
talkie history export <file>
talkie history import <file>
```

---

## parallel — Parallel Requests

### Syntax

```bash
# From file
talkie parallel -f <file> [options]

# From command line
talkie parallel -X <method> -u <path> [-u <path> ...] -b <base_url> [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--file` | `-f` | File with requests (one per line: METHOD URL) |
| `--method` | `-X` | HTTP method for all requests |
| `--url` | `-u` | URL path (can repeat, combined with base) |
| `--base` | `-b` | Base URL for -u paths |
| `--concurrency` | | Max concurrent requests |
| `--delay` | | Delay between requests (seconds) |
| `--output-dir` | | Save results to directory |
| `--no-summary` | | Disable result summary |

### File Format

```
METHOD URL
# Comments allowed
GET https://api.example.com/users/1
POST https://api.example.com/users name=John
```

### Examples

```bash
talkie parallel -f requests.txt --concurrency 5
talkie parallel -X GET -u "/users/1" -u "/users/2" -b "https://api.example.com"
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TALKIE_CONFIG_DIR` | Override config directory (default: `~/.talkie`) |

---

## Configuration File

Location: `~/.talkie/config.json`

```json
{
  "default_headers": {
    "User-Agent": "Talkie/0.1.3",
    "Accept": "application/json"
  },
  "environments": {
    "dev": {
      "name": "dev",
      "base_url": "https://dev-api.example.com",
      "default_headers": {}
    }
  },
  "active_environment": "dev"
}
```
