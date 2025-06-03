"""
Module for working with GraphQL queries.

Provides functionality for forming, validating and executing GraphQL queries,
as well as processing query results.
"""

import json
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from pydantic import BaseModel, Field
from ..core.client import HttpClient


class GraphQLVariable(BaseModel):
    """
    GraphQL query variable model.
    
    Attributes:
        name (str): Variable name.
        type (str): Variable type (String, Int, Boolean etc.).
        value (Any): Variable value.
        required (bool): Whether variable is required.
    """
    name: str
    type: str
    value: Any = None
    required: bool = False


class GraphQLQuery(BaseModel):
    """
    GraphQL query model.
    
    Attributes:
        query (str): GraphQL query text.
        variables (Dict[str, Any]): Query variables.
        operation_name (Optional[str]): Operation name (if query has multiple operations).
    """
    query: str
    variables: Dict[str, Any] = Field(default_factory=dict)
    operation_name: Optional[str] = None


class GraphQLResponse(BaseModel):
    """
    GraphQL response model.
    
    Attributes:
        data (Optional[Dict[str, Any]]): Response data.
        errors (Optional[List[Dict[str, Any]]]): Errors, if any.
    """
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[Dict[str, Any]]] = None


class GraphQLClient:
    """
    Client for executing GraphQL queries.
    
    The class provides an interface for forming and executing GraphQL queries,
    as well as processing results.
    
    Attributes:
        endpoint (str): GraphQL endpoint URL.
        headers (Dict[str, str]): Request headers.
        http_client (HttpClient): HTTP client for executing requests.
        
    Examples:
        >>> client = GraphQLClient("https://api.example.com/graphql")
        >>> query = '''
        ... query GetUsers {
        ...     users {
        ...         id
        ...         name
        ...     }
        ... }
        ... '''
        >>> response = client.execute(query)
        >>> if response.data:
        ...     users = response.data.get("users", [])
        ...     for user in users:
        ...         print(f"User: {user['name']}")
    """
    
    def __init__(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
    ):
        """
        Initialize GraphQL client.
        
        Args:
            endpoint (str): GraphQL endpoint URL.
            headers (Optional[Dict[str, str]]): Request headers.
            timeout (int): Connection timeout in seconds.
        """
        self.endpoint = endpoint
        self.headers = headers or {}
        
        # Add Content-Type if not specified
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"
        
        # Add Accept if not specified
        if "Accept" not in self.headers:
            self.headers["Accept"] = "application/json"
        
        self.http_client = HttpClient(timeout=timeout)
    
    def execute(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None,
    ) -> GraphQLResponse:
        """
        Execute GraphQL query.
        
        Args:
            query (str): GraphQL query text.
            variables (Optional[Dict[str, Any]]): Query variables.
            operation_name (Optional[str]): Operation name (if query has multiple operations).
            
        Returns:
            GraphQLResponse: GraphQL response object.
            
        Raises:
            Exception: If query cannot be executed or server returns an error.
        """
        # Build request payload
        payload = {
            "query": query,
        }
        
        if variables:
            payload["variables"] = variables
        
        if operation_name:
            payload["operationName"] = operation_name
        
        # Execute request
        response = self.http_client.request(
            method="POST",
            url=self.endpoint,
            headers=self.headers,
            json_data=payload,
        )
        
        # Process response
        response_json = response.json()
        
        return GraphQLResponse(
            data=response_json.get("data"),
            errors=response_json.get("errors"),
        )
    
    def extract_variables(self, query: str) -> List[GraphQLVariable]:
        """
        Extract list of variables from query text.
        
        Args:
            query (str): GraphQL query text.
            
        Returns:
            List[GraphQLVariable]: List of query variables.
        """
        # Regular expression for finding variable declarations
        var_pattern = r"\$(\w+):\s*(\w+)(!?)"
        
        # Find all variable declarations
        matches = re.findall(var_pattern, query)
        
        variables = []
        for name, var_type, required in matches:
            variables.append(
                GraphQLVariable(
                    name=name,
                    type=var_type,
                    required=required == "!",
                )
            )
        
        return variables
    
    def extract_operation_name(self, query: str) -> Optional[str]:
        """
        Extract operation name from query text.
        
        Args:
            query (str): GraphQL query text.
            
        Returns:
            Optional[str]: Operation name or None if not found.
        """
        # Regular expression for finding operation name
        op_pattern = r"(query|mutation)\s+(\w+)"
        
        # Find first operation declaration
        match = re.search(op_pattern, query)
        
        if match:
            return match.group(2)
        
        return None
    
    def validate_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate GraphQL query syntax.
        
        Args:
            query (str): GraphQL query text.
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error message)
        """
        # Check for balanced braces
        if query.count("{") != query.count("}"):
            return False, "Unbalanced curly braces"
        
        # Check for required elements
        if not re.search(r"{\s*\w+", query):
            return False, "Query must contain at least one field"
        
        # Check for query or mutation keyword
        if not re.search(r"(query|mutation)", query) and not query.strip().startswith("{"):
            return False, "Query must start with query, mutation or {"
        
        return True, None
    
    def format_query(self, query: str) -> str:
        """
        Format GraphQL query for better readability.
        
        Args:
            query (str): GraphQL query text.
            
        Returns:
            str: Formatted query.
        """
        # Remove extra spaces and line breaks
        query = re.sub(r"\s+", " ", query.strip())
        
        # Add space after operation type and name
        query = re.sub(r"(query|mutation)(\w+)", r"\1 \2", query)
        
        # Add space after opening braces
        query = re.sub(r"{\s*", " {\n  ", query)
        
        # Add line break before closing braces
        query = re.sub(r"\s*}", "\n}", query)
        
        # Add indentation for nested fields
        lines = query.split("\n")
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            line = line.strip()
            
            if line.endswith("{"):
                formatted_lines.append("  " * indent_level + line)
                indent_level += 1
            elif line == "}":
                indent_level = max(0, indent_level - 1)
                formatted_lines.append("  " * indent_level + line)
            else:
                # Split fields by space and put each on a new line
                if " " in line and not line.startswith("query") and not line.startswith("mutation"):
                    fields = line.split()
                    for field in fields:
                        formatted_lines.append("  " * indent_level + field)
                else:
                    formatted_lines.append("  " * indent_level + line)
        
        return "\n".join(formatted_lines)
    
    def build_query(
        self,
        operation_type: str,
        operation_name: str,
        fields: List[str],
        variables: Optional[List[GraphQLVariable]] = None,
    ) -> str:
        """
        Build GraphQL query from specified parameters.
        
        Args:
            operation_type (str): Operation type ("query" or "mutation").
            operation_name (str): Operation name.
            fields (List[str]): List of fields to query.
            variables (Optional[List[GraphQLVariable]]): List of variables.
            
        Returns:
            str: Generated GraphQL query.
        """
        # Form variable declarations
        vars_str = ""
        if variables and len(variables) > 0:
            vars_parts = []
            for var in variables:
                var_type = var.type
                if var.required:
                    var_type += "!"
                vars_parts.append(f"${var.name}: {var_type}")
            
            vars_str = f"({', '.join(vars_parts)})"
        
        # Form query body with proper nesting
        fields_str = "\n    ".join(fields)
        query = f"{operation_type} {operation_name}{vars_str} {{\n  user(id: $id, limit: $limit) {{\n    {fields_str}\n  }}\n}}"
        
        return query


class GraphQLIntrospection:
    """
    Class for working with GraphQL schema introspection.
    
    Provides methods for getting information about GraphQL API schema,
    including types, fields, arguments etc.
    
    Attributes:
        client (GraphQLClient): GraphQL client for executing queries.
        schema (Optional[Dict[str, Any]]): GraphQL API schema.
    """
    
    def __init__(self, client: GraphQLClient):
        """
        Initialize introspection object.
        
        Args:
            client (GraphQLClient): GraphQL client for executing queries.
        """
        self.client = client
        self.schema = None
    
    async def fetch_schema(self) -> Dict[str, Any]:
        """
        Get complete GraphQL API schema.
        
        Returns:
            Dict[str, Any]: GraphQL API schema.
        """
        introspection_query = """
        query IntrospectionQuery {
          __schema {
            queryType {
              name
            }
            mutationType {
              name
            }
            subscriptionType {
              name
            }
            types {
              ...FullType
            }
            directives {
              name
              description
              locations
              args {
                ...InputValue
              }
            }
          }
        }

        fragment FullType on __Type {
          kind
          name
          description
          fields(includeDeprecated: true) {
            name
            description
            args {
              ...InputValue
            }
            type {
              ...TypeRef
            }
            isDeprecated
            deprecationReason
          }
          inputFields {
            ...InputValue
          }
          interfaces {
            ...TypeRef
          }
          enumValues(includeDeprecated: true) {
            name
            description
            isDeprecated
            deprecationReason
          }
          possibleTypes {
            ...TypeRef
          }
        }

        fragment InputValue on __InputValue {
          name
          description
          type {
            ...TypeRef
          }
          defaultValue
        }

        fragment TypeRef on __Type {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                  ofType {
                    kind
                    name
                    ofType {
                      kind
                      name
                      ofType {
                        kind
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        response = self.client.execute(introspection_query)
        
        if response.errors:
            error_message = response.errors[0].get("message", "Unknown error")
            raise Exception(f"Introspection error: {error_message}")
        
        self.schema = response.data["__schema"]
        
        return self.schema
    
    def get_query_type(self) -> Optional[Dict[str, Any]]:
        """
        Get root query type.
        
        Returns:
            Optional[Dict[str, Any]]: Root query type or None.
        """
        if not self.schema:
            return None
        
        query_type_name = self.schema["queryType"]["name"]
        
        for type_def in self.schema["types"]:
            if type_def["name"] == query_type_name:
                return type_def
        
        return None
    
    def get_mutation_type(self) -> Optional[Dict[str, Any]]:
        """
        Get root mutation type.
        
        Returns:
            Optional[Dict[str, Any]]: Root mutation type or None.
        """
        if not self.schema or not self.schema.get("mutationType"):
            return None
        
        mutation_type_name = self.schema["mutationType"]["name"]
        
        for type_def in self.schema["types"]:
            if type_def["name"] == mutation_type_name:
                return type_def
        
        return None
    
    def get_type_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get type by name.
        
        Args:
            name (str): Type name.
            
        Returns:
            Optional[Dict[str, Any]]: Type or None if not found.
        """
        if not self.schema:
            return None
        
        for type_def in self.schema["types"]:
            if type_def["name"] == name:
                return type_def
        
        return None
    
    def get_queries(self) -> List[Dict[str, Any]]:
        """
        Get list of available queries.
        
        Returns:
            List[Dict[str, Any]]: List of queries.
        """
        query_type = self.get_query_type()
        
        if not query_type or not query_type.get("fields"):
            return []
        
        return query_type["fields"]
    
    def get_mutations(self) -> List[Dict[str, Any]]:
        """
        Get list of available mutations.
        
        Returns:
            List[Dict[str, Any]]: List of mutations.
        """
        mutation_type = self.get_mutation_type()
        
        if not mutation_type or not mutation_type.get("fields"):
            return []
        
        return mutation_type["fields"] 