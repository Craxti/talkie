# Video Tutorials

This document provides scripts and outlines for creating Talkie video tutorials. Use these as a guide when recording.

---

## Tutorial 1: Getting Started (5–7 min)

### Outline

1. **Introduction (30 sec)**
   - What is Talkie: CLI HTTP client for developers
   - Why use it: simpler than curl, more features than HTTPie

2. **Installation (1 min)**
   ```bash
   pip install talkie
   talkie --help
   ```

3. **First Request (2 min)**
   ```bash
   talkie get https://jsonplaceholder.typicode.com/posts/1
   ```
   - Show colored output
   - Explain JSON formatting

4. **POST Request (2 min)**
   ```bash
   talkie post https://jsonplaceholder.typicode.com/posts \
     title="My first post" body="Hello Talkie!" userId:=1
   ```
   - Explain `:=` for numbers/booleans
   - Show response

5. **Headers and Parameters (1 min)**
   ```bash
   talkie get https://httpbin.org/get -H "X-Custom: value" -q "page=1"
   ```

6. **Outro (30 sec)**
   - Link to docs
   - Next: GraphQL, WebSocket, OpenAPI

### Recording Tips

- Use a dark terminal theme
- Font size 16–18 for readability
- Record at 1080p
- Keep cursor visible

---

## Tutorial 2: Advanced Features (8–10 min)

### Outline

1. **GraphQL (2 min)**
   ```bash
   talkie graphql https://api.example.com/graphql \
     -q "query { users { id name } }"
   talkie graphql https://api.example.com/graphql -f query.graphql -v id=123
   ```

2. **WebSocket (2 min)**
   ```bash
   talkie ws wss://echo.websocket.org --send "Hello"
   ```

3. **OpenAPI Inspection (2 min)**
   ```bash
   talkie openapi https://api.example.com/openapi.json
   talkie openapi https://api.example.com/openapi.json --endpoints
   talkie openapi https://api.example.com/openapi.json --examples
   ```

4. **Request History (2 min)**
   ```bash
   talkie history list
   talkie history search --method GET --url users
   talkie history repeat <id>
   talkie history export history.json
   ```

5. **Parallel Requests (2 min)**
   ```bash
   echo "GET https://jsonplaceholder.typicode.com/posts/1" > reqs.txt
   echo "GET https://jsonplaceholder.typicode.com/posts/2" >> reqs.txt
   talkie parallel -f reqs.txt --concurrency 5
   ```

---

## Tutorial 3: Configuration & Environments (5 min)

### Outline

1. **Config File Location**
   - `~/.talkie/config.json`
   - `TALKIE_CONFIG_DIR` env var

2. **Default Headers**
   ```json
   {"default_headers": {"Authorization": "Bearer TOKEN"}}
   ```

3. **Environments**
   ```json
   {
     "environments": {
       "dev": {"base_url": "https://dev-api.example.com"},
       "prod": {"base_url": "https://api.example.com"}
     },
     "active_environment": "dev"
   }
   ```

4. **Using Environments**
   ```bash
   talkie get /users  # Uses base_url from active environment
   ```

---

## Suggested Platforms

- **YouTube** — Full tutorials, searchable
- **Dev.to** — Embed videos in articles
- **Habr** — Russian-speaking audience
- **GitHub Discussions** — Link from README

---

## Checklist Before Publishing

- [ ] Audio is clear
- [ ] Terminal text is readable
- [ ] Commands are correct and tested
- [ ] Links in description work
- [ ] Add timestamps in description
