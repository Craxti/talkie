"""Тесты для GraphQL клиента."""

import json
import pytest
from unittest.mock import Mock, patch

from talkie.utils.graphql import (
    GraphQLClient,
    GraphQLVariable,
    GraphQLQuery,
    GraphQLResponse,
    GraphQLIntrospection
)


@pytest.fixture
def mock_http_response():
    """Мок для HTTP-ответа."""
    class MockResponse:
        def __init__(self, data=None, errors=None):
            self._data = data or {}
            self._errors = errors
            
        def json(self):
            response = {}
            if self._data:
                response["data"] = self._data
            if self._errors:
                response["errors"] = self._errors
            return response
    
    return MockResponse


@pytest.fixture
def graphql_client():
    """Создает экземпляр GraphQL клиента для тестов."""
    return GraphQLClient("https://api.example.com/graphql")


def test_graphql_client_init():
    """Тест инициализации GraphQL клиента."""
    client = GraphQLClient(
        endpoint="https://api.example.com/graphql",
        headers={"Authorization": "Bearer token"},
        timeout=60
    )
    
    assert client.endpoint == "https://api.example.com/graphql"
    assert client.headers["Authorization"] == "Bearer token"
    assert client.headers["Content-Type"] == "application/json"
    assert client.headers["Accept"] == "application/json"
    assert client.http_client.timeout == 60


def test_graphql_client_execute(graphql_client, mock_http_response):
    """Тест выполнения GraphQL запроса."""
    query = """
    query GetUser($id: ID!) {
        user(id: $id) {
            id
            name
            email
        }
    }
    """
    
    variables = {"id": "123"}
    mock_data = {
        "user": {
            "id": "123",
            "name": "John Doe",
            "email": "john@example.com"
        }
    }
    
    with patch("talkie.core.client.HttpClient.request",
              return_value=mock_http_response(data=mock_data)):
        response = graphql_client.execute(query, variables)
        
        assert isinstance(response, GraphQLResponse)
        assert response.data == mock_data
        assert response.errors is None


def test_graphql_client_execute_with_error(graphql_client, mock_http_response):
    """Тест выполнения GraphQL запроса с ошибкой."""
    query = "query { invalidField }"
    mock_errors = [{"message": "Field 'invalidField' doesn't exist"}]
    
    with patch("talkie.core.client.HttpClient.request",
              return_value=mock_http_response(errors=mock_errors)):
        response = graphql_client.execute(query)
        
        assert isinstance(response, GraphQLResponse)
        assert response.data is None
        assert response.errors == mock_errors


def test_extract_variables(graphql_client):
    """Тест извлечения переменных из запроса."""
    query = """
    query GetUser($id: ID!, $includeEmail: Boolean) {
        user(id: $id) {
            name
            email @include(if: $includeEmail)
        }
    }
    """
    
    variables = graphql_client.extract_variables(query)
    
    assert len(variables) == 2
    assert variables[0].name == "id"
    assert variables[0].type == "ID"
    assert variables[0].required is True
    assert variables[1].name == "includeEmail"
    assert variables[1].type == "Boolean"
    assert variables[1].required is False


def test_extract_operation_name(graphql_client):
    """Тест извлечения имени операции из запроса."""
    query = """
    query GetUserProfile {
        user {
            profile {
                name
            }
        }
    }
    """
    
    operation_name = graphql_client.extract_operation_name(query)
    assert operation_name == "GetUserProfile"


def test_validate_query(graphql_client):
    """Тест валидации GraphQL запроса."""
    # Валидный запрос
    valid_query = """
    query {
        user {
            id
            name
        }
    }
    """
    is_valid, error = graphql_client.validate_query(valid_query)
    assert is_valid is True
    assert error is None
    
    # Невалидный запрос
    invalid_query = """
    query {
        user {
            id
            name
        }
    """
    is_valid, error = graphql_client.validate_query(invalid_query)
    assert is_valid is False
    assert error is not None


def test_format_query(graphql_client):
    """Тест форматирования GraphQL запроса."""
    unformatted_query = """query{user{id name email}}"""
    formatted_query = graphql_client.format_query(unformatted_query)
    
    expected = """query {
  user {
    id
    name
    email
  }
}"""
    
    assert formatted_query.strip() == expected.strip()


def test_build_query(graphql_client):
    """Тест построения GraphQL запроса."""
    variables = [
        GraphQLVariable(name="id", type="ID", required=True),
        GraphQLVariable(name="limit", type="Int", value=10)
    ]
    
    query = graphql_client.build_query(
        operation_type="query",
        operation_name="GetUser",
        fields=["id", "name", "email"],
        variables=variables
    )
    
    expected = """query GetUser($id: ID!, $limit: Int) {
  user(id: $id, limit: $limit) {
    id
    name
    email
  }
}"""
    
    assert query.strip() == expected.strip()


@pytest.mark.asyncio
async def test_introspection_fetch_schema():
    """Тест получения схемы через интроспекцию."""
    mock_schema = {
        "__schema": {
            "types": [
                {
                    "name": "Query",
                    "fields": [
                        {
                            "name": "user",
                            "type": {"name": "User"}
                        }
                    ]
                }
            ]
        }
    }
    
    client = GraphQLClient("https://api.example.com/graphql")
    with patch.object(client, "execute", return_value=GraphQLResponse(data=mock_schema)):
        introspection = GraphQLIntrospection(client)
        schema = await introspection.fetch_schema()
        
        assert schema == mock_schema["__schema"]


def test_introspection_get_types(graphql_client):
    """Test getting types through introspection."""
    mock_schema = {
        "queryType": {"name": "Query"},
        "types": [
            {"name": "Query", "kind": "OBJECT"},
            {"name": "User", "kind": "OBJECT"},
            {"name": "String", "kind": "SCALAR"}
        ]
    }
    
    introspection = GraphQLIntrospection(graphql_client)
    introspection.schema = mock_schema
    
    # Test getting query type
    query_type = introspection.get_query_type()
    assert query_type["name"] == "Query"
    
    # Test getting type by name
    user_type = introspection.get_type_by_name("User")
    assert user_type["name"] == "User"
    
    # Test getting list of queries
    queries = introspection.get_queries()
    assert isinstance(queries, list) 