"""Tests for antigravity icons module."""

from nicegui_ai.antigravity.icons import AntigravityIcon, get_antigravity_svg


def test_get_antigravity_svg():
    svg = get_antigravity_svg("chevron-right", size=16)
    assert "<svg" in svg
    assert 'width="16"' in svg
    assert 'height="16"' in svg


def test_get_antigravity_svg_default_size():
    svg = get_antigravity_svg("home")
    assert "<svg" in svg
    assert 'width="16"' in svg


def test_get_antigravity_svg_unknown_uses_sparkles():
    svg = get_antigravity_svg("nonexistent-icon")
    assert "<svg" in svg


def test_antigravity_icon_init():
    icon = AntigravityIcon("chevron-right", size=16)
    assert icon is not None
    assert icon.icon_name == "chevron-right"
    assert icon.icon_size == 16


def test_antigravity_icon_set_icon():
    icon = AntigravityIcon("chevron-right")
    icon.set_icon("home", size=24)
    assert icon.icon_name == "home"
    assert icon.icon_size == 24
