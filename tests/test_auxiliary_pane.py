"""Tests for antigravity auxiliary_pane module."""

from nicegui_ai.antigravity.auxiliary_pane import AuxiliaryPane


def test_auxiliary_pane_init():
    pane = AuxiliaryPane()
    assert pane is not None
