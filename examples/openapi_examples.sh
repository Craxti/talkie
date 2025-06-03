#!/bin/bash
# Examples of using OpenAPI functionality in Talkie

# Inspecting OpenAPI specification from Petstore
echo "=== Inspecting OpenAPI from Petstore ==="
talkie openapi https://petstore.swagger.io/v2/swagger.json

# Local specification (assuming the file exists)
echo -e "\n=== Inspecting local OpenAPI specification ==="
# talkie openapi ./swagger.yaml

# Getting API information without displaying endpoints
echo -e "\n=== Inspecting OpenAPI without displaying endpoints ==="
talkie openapi https://petstore.swagger.io/v2/swagger.json --no-endpoints

# Sending request to endpoint from OpenAPI specification
echo -e "\n=== Sending request to endpoint from OpenAPI specification ==="
talkie get https://petstore.swagger.io/v2/pet/findByStatus -q "status=available" 