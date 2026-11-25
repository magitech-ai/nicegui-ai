"""Tests for antigravity theme module."""

from nicegui_ai.antigravity.theme import (
    apply_antigravity_theme_mode,
    setup_antigravity_theme,
)


def test_setup_antigravity_theme_dark():
    setup_antigravity_theme("dark")


def test_setup_antigravity_theme_light():
    setup_antigravity_theme("light")


def test_setup_antigravity_theme_oled():
    setup_antigravity_theme("oled")


def test_apply_antigravity_theme_mode_light():
    apply_antigravity_theme_mode("light")


def test_apply_antigravity_theme_mode_oled():
    apply_antigravity_theme_mode("oled")


def test_apply_antigravity_theme_mode_dark():
    apply_antigravity_theme_mode("dark")
