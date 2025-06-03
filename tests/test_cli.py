import pytest
from typer.testing import CliRunner
from talkie.cli.main import cli

runner = CliRunner()


@pytest.fixture
def mock_http_response(monkeypatch):
    """Мок для HTTP-ответов в тестах CLI."""
    class MockResponse:
        def __init__(self, status_code=200, content=None, headers=None):
            self.status_code = status_code
            self._content = content or b'{"status": "ok", "code": 200, "data": {"name": "Test", "value": 123}}'
            self.headers = headers or {"Content-Type": "application/json; charset=utf-8"}
            self.reason_phrase = "OK" if status_code == 200 else "Error"
            from datetime import timedelta
            self.elapsed = timedelta(milliseconds=100)
            
        @property
        def content(self):
            return self._content
            
        @property
        def text(self):
            return self._content.decode('utf-8')
            
        def json(self):
            import json
            return json.loads(self.text)
            
        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP Error: {self.status_code}")
    
    class MockClient:
        def __init__(self, *args, **kwargs):
            pass
            
        def request(self, *args, **kwargs):
            return MockResponse()
    
    monkeypatch.setattr("talkie.core.client.httpx.Client", MockClient)


def test_get_command(mock_http_response):
    """Тест базовой GET команды."""
    result = runner.invoke(cli, ["get", "https://example.com/api"])
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_post_command(mock_http_response):
    """Тест базовой POST команды с передачей данных."""
    result = runner.invoke(cli, ["post", "https://example.com/api", "-d", "name=Test", "-d", "value:=123"])
    assert result.exit_code == 0
    assert "200" in result.stdout  # Check status code
    assert "Test" in result.stdout  # Check response content


def test_headers_option(mock_http_response):
    """Тест опции добавления заголовков."""
    result = runner.invoke(cli, [
        "get", 
        "https://example.com/api", 
        "-H", "Authorization: Bearer test", 
        "-H", "Accept: application/json"
    ])
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_format_option(mock_http_response):
    """Тест опции форматирования вывода."""
    result = runner.invoke(cli, ["get", "https://example.com/api", "--format", "json"])
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_verbose_option(mock_http_response):
    """Test verbose output option."""
    result = runner.invoke(cli, ["get", "https://example.com/api", "-v"])
    assert result.exit_code == 0
    assert "200" in result.stdout
    assert "Request Headers" in result.stdout or "Response Headers" in result.stdout
    assert "Content-Type" in result.stdout


def test_output_file_option(mock_http_response, tmp_path):
    """Тест сохранения вывода в файл."""
    output_file = tmp_path / "output.json"
    result = runner.invoke(cli, ["get", "https://example.com/api", "-o", str(output_file)])
    assert result.exit_code == 0
    assert output_file.exists() 