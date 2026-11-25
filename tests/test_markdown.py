"""Tests for markdown module."""

from nicegui_ai.markdown import parse_markdown_blocks


def test_parse_markdown_blocks_plain():
    blocks = parse_markdown_blocks("Just text")
    assert len(blocks) == 1
    assert blocks[0]["type"] == "text"
    assert blocks[0]["content"] == "Just text"


def test_parse_markdown_blocks_code():
    text = "```python\nprint(1)\n```"
    blocks = parse_markdown_blocks(text)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "code"
    assert blocks[0]["language"] == "python"
    assert "print(1)" in blocks[0]["code"]


def test_parse_markdown_blocks_mixed():
    text = "Intro\n```python\nprint(1)\n```\nOutro"
    blocks = parse_markdown_blocks(text)
    assert len(blocks) == 3
    assert blocks[0]["type"] == "text"
    assert blocks[1]["type"] == "code"
    assert blocks[2]["type"] == "text"
