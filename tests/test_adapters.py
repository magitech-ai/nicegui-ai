"""Tests for adapters."""

from nicegui_ai.adapters.agui import AgUiStreamAdapter
from nicegui_ai.adapters.gemini import GeminiStreamAdapter
from nicegui_ai.adapters.opencode import OpenCodeStreamAdapter
from nicegui_ai.adapters.openrouter import OpenRouterStreamAdapter


def test_agui_adapter_init():
    adapter = AgUiStreamAdapter(source=None)
    assert adapter.source is None
    assert adapter.text == ""


def test_gemini_adapter_init():
    adapter = GeminiStreamAdapter(source=None)
    assert adapter.source is None


def test_opencode_adapter_init():
    adapter = OpenCodeStreamAdapter(source=None)
    assert adapter.source is None


def test_openrouter_adapter_init():
    adapter = OpenRouterStreamAdapter(source=None)
    assert adapter.source is None
