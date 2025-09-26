"""Module for GraphQL operations and utilities."""

import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class GraphQLResponse:
    """GraphQL response data structure."""
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[Dict[str, Any]]] = None
    extensions: Optional[Dict[str, Any]] = None


class GraphQLClient:
    """Client for GraphQL operations."""

    def __init__(self, endpoint: str, headers: Optional[Dict[str, str]] = None):
        """Initialize GraphQL client.

        Args:
            endpoint: GraphQL endpoint URL
            headers: Default headers for requests
        """
        self.endpoint = endpoint
        self.headers = headers or {}
        self.headers.setdefault("Content-Type", "application/json")

    def query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None
    ) -> GraphQLResponse:
        """Execute GraphQL query.

        Args:
            query: GraphQL query string
            variables: Query variables
            operation_name: Operation name

        Returns:
            GraphQLResponse: Response data
        """
        payload = {
            "query": query,
            "variables": variables or {},
        }

        if operation_name:
            payload["operationName"] = operation_name

        # In a real implementation, this would make an HTTP request
        # For now, return a mock response
        return GraphQLResponse(
            data={"message": "GraphQL query executed"},
            errors=None
        )

    def mutation(
        self,
        mutation: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None
    ) -> GraphQLResponse:
        """Execute GraphQL mutation.

        Args:
            mutation: GraphQL mutation string
            variables: Mutation variables
            operation_name: Operation name

        Returns:
            GraphQLResponse: Response data
        """
        payload = {
            "query": mutation,
            "variables": variables or {},
        }

        if operation_name:
            payload["operationName"] = operation_name

        # In a real implementation, this would make an HTTP request
        # For now, return a mock response
        return GraphQLResponse(
            data={"message": "GraphQL mutation executed"},
            errors=None
        )


def build_graphql_query(
    fields: List[str],
    filters: Optional[Dict[str, Any]] = None,
    pagination: Optional[Dict[str, int]] = None
) -> str:
    """Build GraphQL query from field specifications.

    Args:
        fields: List of fields to select
        filters: Filter conditions
        pagination: Pagination parameters

    Returns:
        str: GraphQL query string
    """
    query_parts = []

    # Add fields
    field_selection = " ".join(fields)
    query_parts.append(f"query {{ {field_selection} }}")

    # Add filters if provided
    if filters:
        filter_vars = []
        for key, value in filters.items():
            if isinstance(value, str):
                filter_vars.append(f'{key}: "{value}"')
            else:
                filter_vars.append(f"{key}: {value}")

        if filter_vars:
            query_parts.append(f"where: {{ {', '.join(filter_vars)} }}")

    # Add pagination if provided
    if pagination:
        pagination_vars = []
        if "limit" in pagination:
            pagination_vars.append(f"limit: {pagination['limit']}")
        if "offset" in pagination:
            pagination_vars.append(f"offset: {pagination['offset']}")

        if pagination_vars:
            query_parts.append(f"pagination: {{ {', '.join(pagination_vars)} }}")

    return " ".join(query_parts)


def build_graphql_mutation(
    operation: str,
    input_data: Dict[str, Any],
    return_fields: List[str]
) -> str:
    """Build GraphQL mutation from operation and data.

    Args:
        operation: Mutation operation name
        input_data: Input data for mutation
        return_fields: Fields to return

    Returns:
        str: GraphQL mutation string
    """
    # Convert input data to GraphQL format
    input_vars = []
    for key, value in input_data.items():
        if isinstance(value, str):
            input_vars.append(f'{key}: "{value}"')
        elif isinstance(value, dict):
            # Handle nested objects
            nested_vars = []
            for nested_key, nested_value in value.items():
                if isinstance(nested_value, str):
                    nested_vars.append(f'{nested_key}: "{nested_value}"')
                else:
                    nested_vars.append(f"{nested_key}: {nested_value}")
            input_vars.append(f"{key}: {{ {', '.join(nested_vars)} }}")
        else:
            input_vars.append(f"{key}: {value}")

    input_string = ", ".join(input_vars)
    return_fields_string = " ".join(return_fields)

    return (f"mutation {{ {operation}(input: {{ {input_string} }}) "
            f"{{ {return_fields_string} }} }}")


def parse_graphql_response(response_text: str) -> GraphQLResponse:
    """Parse GraphQL response from JSON string.

    Args:
        response_text: JSON response string

    Returns:
        GraphQLResponse: Parsed response
    """
    try:
        data = json.loads(response_text)
        return GraphQLResponse(
            data=data.get("data"),
            errors=data.get("errors"),
            extensions=data.get("extensions")
        )
    except json.JSONDecodeError:
        return GraphQLResponse(
            data=None,
            errors=[{"message": "Invalid JSON response"}]
        )


def validate_graphql_query(query: str) -> bool:
    """Validate GraphQL query syntax.

    Args:
        query: GraphQL query string

    Returns:
        bool: True if query is valid
    """
    # Basic validation - check for required GraphQL keywords
    required_keywords = ["query", "mutation", "subscription"]
    query_lower = query.lower().strip()

    # Check if query starts with a valid operation type
    for keyword in required_keywords:
        if query_lower.startswith(keyword):
            return True

    return False


def get_input_value_fragment() -> str:
    """Get GraphQL fragment for input value types.

    Returns:
        str: GraphQL fragment string
    """
    return """
    fragment InputValue on __InputValue {
        name
        description
        type {
            name
            kind
            ofType {
                name
                kind
            }
        }
        defaultValue
    }
    """


def get_type_ref_fragment() -> str:
    """Get GraphQL fragment for type references.

    Returns:
        str: GraphQL fragment string
    """
    return """
    fragment TypeRef on __Type {
        name
        kind
        description
        ofType {
            name
            kind
        }
    }
    """


def introspect_schema(endpoint: str) -> Dict[str, Any]:
    """Introspect GraphQL schema.

    Args:
        endpoint: GraphQL endpoint URL

    Returns:
        Dict[str, Any]: Schema introspection data
    """
    # In a real implementation, this would make an HTTP request with introspection query
    # For now, return mock introspection data
    return {
        "__schema": {
            "queryType": {"name": "Query"},
            "mutationType": {"name": "Mutation"},
            "subscriptionType": None,
            "types": [],
            "directives": []
        }
    }
