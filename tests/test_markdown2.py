"""Tests for markdown uncovered branches."""

from nicegui_ai.markdown import parse_markdown_blocks


def test_parse_markdown_blocks_empty():
    blocks = parse_markdown_blocks("")
    assert len(blocks) == 1
    assert blocks[0]["type"] == "text"


def test_parse_markdown_blocks_multiple_code():
    text = "```python\nprint(1)\n```\n```js\nconsole.log(1)\n```"
    blocks = parse_markdown_blocks(text)
    code_blocks = [b for b in blocks if b["type"] == "code"]
    assert len(code_blocks) == 2
