#!/bin/bash
# Examples of using curl command generation functionality in Talkie

# Simple curl command generation
echo "=== Generating curl for GET request ==="
talkie curl https://jsonplaceholder.typicode.com/posts/1

# Generating curl for POST request
echo -e "\n=== Generating curl for POST request ==="
talkie curl https://jsonplaceholder.typicode.com/posts -X POST -d "title=Test post" -d "body=Post content" -d "userId:=1"

# Generating curl with headers
echo -e "\n=== Generating curl with headers ==="
talkie curl https://jsonplaceholder.typicode.com/posts -H "Content-Type: application/json" -H "Authorization: Bearer token123"

# Generating curl with query parameters
echo -e "\n=== Generating curl with query parameters ==="
talkie curl https://jsonplaceholder.typicode.com/posts -q "userId=1" -q "_limit=3"

# Generating curl with verbose and insecure options
echo -e "\n=== Generating curl with additional options ==="
talkie curl https://jsonplaceholder.typicode.com/posts -v -k

# Adding curl command to regular query
echo -e "\n=== Output curl command when executing query ==="
talkie get https://jsonplaceholder.typicode.com/posts/1 --curl

# Getting only curl command without executing query
echo -e "\n=== Getting only curl command without executing query ==="
talkie get https://jsonplaceholder.typicode.com/posts/1 --curl -v 