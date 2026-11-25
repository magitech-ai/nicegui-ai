"""Tests for code_block module uncovered branches."""

from nicegui_ai.code_block import CodeBlock


def test_code_block_no_language():
    block = CodeBlock(code="x = 1")
    assert block.language == "text"


def test_code_block_no_filename():
    block = CodeBlock(code="x = 1", language="python")
    assert block.filename is None
