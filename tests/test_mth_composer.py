"""Tests for mth composer module."""

from nicegui_ai.mth.composer import MthComposer


def test_mth_composer_init():
    composer = MthComposer()
    assert composer is not None
