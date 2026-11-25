"""Tests for header module uncovered branches."""

from nicegui_ai.header import FloatingHeader


def test_floating_header_no_model():
    header = FloatingHeader(agent_name="Agent", tokens_used=10, token_limit=100)
    assert header is not None


def test_floating_header_no_tokens():
    header = FloatingHeader(agent_name="Agent", model="gpt-4")
    assert header is not None
