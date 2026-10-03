"""Tests for runtime request builder."""

from mcp_forge.templates.server_project.runtime.request_builder import build_request


def test_build_request_path_and_query() -> None:
    base_url = "https://api.example.com/v1"
    template = "/books/{book_id}/authors"
    args = {
        "book_id": "book/special#1",
        "limit": 10,
        "tags": ["fiction", "bestseller"],
        "active": True,
    }
    locs = {"book_id": "path", "limit": "query", "tags": "query", "active": "query"}

    url, q, headers, json_body, form_body = build_request(base_url, template, args, locs)

    # Path parameter must be percent-encoded
    assert url == "https://api.example.com/v1/books/book%2Fspecial%231/authors"
    assert q["limit"] == "10"
    assert q["tags"] == ["fiction", "bestseller"]
    assert q["active"] == "true"
    assert json_body is None
    assert form_body is None


def test_build_request_json_body_flattened() -> None:
    base_url = "https://api.example.com"
    template = "/books"
    args = {"title": "Rust Book", "price": 45.0, "store_id": "store_1"}
    locs = {"title": "body", "price": "body", "store_id": "query"}

    url, q, headers, json_body, form_body = build_request(
        base_url, template, args, locs, is_flattened_body=True, content_type="application/json"
    )

    assert url == "https://api.example.com/books"
    assert q["store_id"] == "store_1"
    assert json_body == {"title": "Rust Book", "price": 45.0}
    assert headers["Content-Type"] == "application/json"


def test_build_request_form_urlencoded() -> None:
    base_url = "https://api.example.com"
    template = "/login"
    args = {"username": "alice", "password": "secret"}
    locs = {"username": "body", "password": "body"}

    url, q, headers, json_body, form_body = build_request(
        base_url,
        template,
        args,
        locs,
        is_flattened_body=True,
        content_type="application/x-www-form-urlencoded",
    )

    assert form_body == {"username": "alice", "password": "secret"}
    assert headers["Content-Type"] == "application/x-www-form-urlencoded"
