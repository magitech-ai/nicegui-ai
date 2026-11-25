"""Tests for code_block module."""

from nicegui_ai.code_block import CodeBlock


def test_code_block_init():
    block = CodeBlock(code="print('hi')", language="python", filename="test.py")
    assert block.code == "print('hi')"
    assert block.language == "python"
    assert block.filename == "test.py"


def test_code_block_defaults():
    block = CodeBlock(code="x = 1")
    assert block.code == "x = 1"
    assert block.language == "text"
    assert block.filename is None
