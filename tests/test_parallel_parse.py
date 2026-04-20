"""Unit tests for parallel job line parsing (README format)."""

import pytest

from talkie.cli.parallel_parse import ParallelJob, parse_parallel_line


def test_get_absolute_url() -> None:
    j = parse_parallel_line("GET https://example.com/path")
    assert j.method == "GET"
    assert j.url == "https://example.com/path"
    assert j.json_body is None


def test_implicit_get() -> None:
    j = parse_parallel_line("https://api.test/v1")
    assert j.method == "GET"
    assert j.url == "https://api.test/v1"


def test_post_with_form_flags() -> None:
    j = parse_parallel_line(
        'POST https://api.example.com/users -F name=John -F age:=30'
    )
    assert j.method == "POST"
    assert j.url == "https://api.example.com/users"
    assert j.json_body == {"name": "John", "age": 30}


def test_post_positional_fragments() -> None:
    j = parse_parallel_line("POST https://api.example.com/users name=Jane flag:=true")
    assert j.json_body == {"name": "Jane", "flag": True}


def test_comment_raises() -> None:
    with pytest.raises(ValueError):
        parse_parallel_line("# comment")


def test_bad_token() -> None:
    with pytest.raises(ValueError):
        parse_parallel_line("GET https://a.com oops")
