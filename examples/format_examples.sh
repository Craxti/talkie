#!/bin/bash
# Examples of using formatting functionality in Talkie

# Creating test files
echo '{"id": 1, "name": "Test", "tags": ["api", "example"], "active": true, "details": {"type": "user", "role": "admin"}}' > test.json
echo '<?xml version="1.0" encoding="UTF-8"?><root><user id="1"><name>Test</name><email>test@example.com</email><roles><role>admin</role><role>user</role></roles></user></root>' > test.xml
echo '<html><head><title>Test Page</title></head><body><h1>Hello, World!</h1><p>This is a <b>test</b> page.</p><ul><li>Item 1</li><li>Item 2</li></ul></body></html>' > test.html

# JSON Formatting
echo "=== JSON Formatting ==="
talkie format test.json

# Formatting JSON and saving the result
echo -e "\n=== Formatting JSON with saving the result ==="
talkie format test.json -o formatted.json
echo "Result saved in formatted.json"

# Formatting XML
echo -e "\n=== Formatting XML ==="
talkie format test.xml

# Converting HTML to Markdown
echo -e "\n=== Converting HTML to Markdown ==="
talkie format test.html --type markdown

# Formatting with explicit type specification
echo -e "\n=== Formatting XML with explicit type specification ==="
talkie format test.xml --type xml

# Using formatting in HTTP request
echo -e "\n=== Formatting in HTTP request ==="
talkie get https://jsonplaceholder.typicode.com/posts/1 --format json

# Cleaning test files
echo -e "\n=== Cleaning test files ==="
rm test.json test.xml test.html formatted.json 