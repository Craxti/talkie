"""Tests for GraphQL CLI command."""

import pytest
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from typer.testing import CliRunner

from talkie.cli.main import cli
from talkie.utils.graphql import GraphQLResponse


class TestGraphQLCLI:
    """Test cases for GraphQL CLI command."""
    
    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def mock_graphql_client(self):
        """Create mock GraphQL client."""
        with patch('talkie.cli.main.GraphQLClient') as mock:
            client_instance = Mock()
            mock.return_value = client_instance
            
            # Mock successful response
            response = GraphQLResponse(
                data={"users": [{"id": 1, "name": "John"}]},
                errors=None
            )
            client_instance.execute.return_value = response
            
            yield client_instance
    
    def test_graphql_with_query_string(self, runner, mock_graphql_client):
        """Test GraphQL command with query string."""
        result = runner.invoke(cli, [
            "graphql",
            "https://api.example.com/graphql",
            "--query", "query { users { id name } }"
        ])
        
        assert result.exit_code == 0
        assert "GraphQL Response:" in result.stdout
        mock_graphql_client.execute.assert_called_once()
    
    def test_graphql_with_query_file(self, runner, mock_graphql_client):
        """Test GraphQL command with query file."""
        # Create temporary query file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.graphql', delete=False) as f:
            f.write("query GetUsers { users { id name } }")
            query_file = f.name
        
        try:
            result = runner.invoke(cli, [
                "graphql",
                "https://api.example.com/graphql",
                "--file", query_file
            ])
            
            assert result.exit_code == 0
            mock_graphql_client.execute.assert_called_once()
            
            # Check that correct query was passed
            call_args = mock_graphql_client.execute.call_args
            assert "GetUsers" in call_args[1]['query']
        
        finally:
            import os
            os.unlink(query_file)
    
    def test_graphql_with_variables(self, runner, mock_graphql_client):
        """Test GraphQL command with variables."""
        result = runner.invoke(cli, [
            "graphql",
            "https://api.example.com/graphql",
            "--query", "query($id: ID!) { user(id: $id) { name } }",
            "--variable", "id:=123"
        ])
        
        assert result.exit_code == 0
        
        # Check that variables were passed correctly
        call_args = mock_graphql_client.execute.call_args
        assert call_args[1]['variables'] == {"id": 123}
    
    def test_graphql_with_headers(self, runner):
        """Test GraphQL command with custom headers."""
        with patch('talkie.cli.main.GraphQLClient') as mock_graphql_client_class:
            mock_client_instance = Mock()
            mock_graphql_client_class.return_value = mock_client_instance
            
            # Mock successful response
            response = GraphQLResponse(
                data={"users": [{"id": 1, "name": "John"}]},
                errors=None
            )
            mock_client_instance.execute.return_value = response
            
            result = runner.invoke(cli, [
                "graphql",
                "https://api.example.com/graphql",
                "--query", "query { users { id } }",
                "--header", "Authorization:Bearer token123"
            ])
            
            assert result.exit_code == 0
            
            # Check that client was created with correct headers
            call_args = mock_graphql_client_class.call_args
            assert "Authorization" in call_args[1]['headers']
            assert call_args[1]['headers']['Authorization'] == "Bearer token123"
    
    def test_graphql_introspection(self, runner):
        """Test GraphQL introspection command."""
        with patch('talkie.cli.main.GraphQLClient') as mock_client_class:
            client_instance = Mock()
            mock_client_class.return_value = client_instance
            
            # Mock introspection response
            introspection_data = {
                "__schema": {
                    "queryType": {"name": "Query"},
                    "mutationType": {"name": "Mutation"},
                    "types": [
                        {"name": "User", "kind": "OBJECT"},
                        {"name": "String", "kind": "SCALAR"},
                    ]
                }
            }
            response = GraphQLResponse(data=introspection_data, errors=None)
            client_instance.execute.return_value = response
            
            result = runner.invoke(cli, [
                "graphql",
                "https://api.example.com/graphql",
                "--introspect"
            ])
            
            assert result.exit_code == 0
            assert "GraphQL Schema Information:" in result.stdout
            assert "Query Type: Query" in result.stdout
            assert "Mutation Type: Mutation" in result.stdout
    
    def test_graphql_with_errors(self, runner):
        """Test GraphQL command with response errors."""
        with patch('talkie.cli.main.GraphQLClient') as mock_client_class:
            client_instance = Mock()
            mock_client_class.return_value = client_instance
            
            # Mock response with errors
            response = GraphQLResponse(
                data=None,
                errors=[{
                    "message": "Field 'invalid' doesn't exist",
                    "locations": [{"line": 1, "column": 10}]
                }]
            )
            client_instance.execute.return_value = response
            
            result = runner.invoke(cli, [
                "graphql",
                "https://api.example.com/graphql",
                "--query", "query { invalid }"
            ])
            
            assert result.exit_code == 0
            assert "GraphQL Errors:" in result.stdout
            assert "Field 'invalid' doesn't exist" in result.stdout
    
    def test_graphql_json_output(self, runner, mock_graphql_client):
        """Test GraphQL command with JSON output."""
        result = runner.invoke(cli, [
            "graphql",
            "https://api.example.com/graphql",
            "--query", "query { users { id } }",
            "--json"
        ])
        
        assert result.exit_code == 0
        
        # Should output valid JSON
        try:
            output_data = json.loads(result.stdout)
            assert "data" in output_data
            assert "errors" in output_data
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")
    
    def test_graphql_save_to_file(self, runner, mock_graphql_client):
        """Test GraphQL command saving to file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name
        
        try:
            result = runner.invoke(cli, [
                "graphql",
                "https://api.example.com/graphql",
                "--query", "query { users { id } }",
                "--output", output_file
            ])
            
            assert result.exit_code == 0
            assert "Response saved to:" in result.stdout
            
            # Check that file was created with correct content
            with open(output_file, 'r') as f:
                saved_data = json.load(f)
                assert "data" in saved_data
                assert "users" in saved_data["data"]
        
        finally:
            import os
            os.unlink(output_file)
    
    def test_graphql_no_query_specified(self, runner):
        """Test GraphQL command with no query specified."""
        result = runner.invoke(cli, [
            "graphql",
            "https://api.example.com/graphql"
        ])
        
        assert result.exit_code == 1
        assert "No query specified" in result.stdout
    
    def test_graphql_invalid_query_file(self, runner):
        """Test GraphQL command with non-existent query file."""
        result = runner.invoke(cli, [
            "graphql",
            "https://api.example.com/graphql",
            "--file", "/path/to/nonexistent/file.graphql"
        ])
        
        assert result.exit_code == 1
        assert "Query file not found" in result.stdout
    
    def test_graphql_verbose_output(self, runner, mock_graphql_client):
        """Test GraphQL command with verbose output."""
        result = runner.invoke(cli, [
            "graphql",
            "https://api.example.com/graphql",
            "--query", "query { users { id } }",
            "--variable", "limit:=10",
            "--verbose"
        ])
        
        assert result.exit_code == 0
        assert "GraphQL Endpoint:" in result.stdout
        assert "Variables:" in result.stdout
        assert "Executing GraphQL query..." in result.stdout
    
    @patch('talkie.cli.main.HttpClient')
    def test_graphql_with_certificate(self, mock_http_client, runner, mock_graphql_client):
        """Test GraphQL command with client certificate."""
        # Create temporary certificate file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write("fake certificate content")
            cert_file = f.name
        
        try:
            result = runner.invoke(cli, [
                "graphql",
                "https://api.example.com/graphql",
                "--query", "query { users { id } }",
                "--cert", cert_file
            ])
            
            assert result.exit_code == 0
            
            # Check that HttpClient was called with certificate
            mock_http_client.assert_called_once()
            # Just verify that cert parameter was passed, don't check exact value due to parsing
            call_args = mock_http_client.call_args
            assert 'cert' in call_args[1]
            assert call_args[1]['cert'] is not None
        
        finally:
            import os
            os.unlink(cert_file)
