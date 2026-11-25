"""Tests for SlideOverDrawer."""

from nicegui_ai.drawer import SlideOverDrawer


def test_drawer_init_default():
    drawer = SlideOverDrawer()
    assert drawer.title == "Details"
    assert drawer.icon_name == "scroll"
    assert drawer.side == "right"
    assert drawer.width_px == 420
    assert not drawer.is_open


def test_drawer_init_custom():
    drawer = SlideOverDrawer(title="Custom", icon="help", side="left", width_px=300)
    assert drawer.title == "Custom"
    assert drawer.icon_name == "help"
    assert drawer.side == "left"
    assert drawer.width_px == 300
    assert not drawer.is_open


def test_drawer_open_close():
    drawer = SlideOverDrawer()
    assert not drawer.is_open

    drawer.open()
    assert drawer.is_open

    drawer.close()
    assert not drawer.is_open


def test_drawer_toggle():
    drawer = SlideOverDrawer()
    assert not drawer.is_open

    drawer.toggle()
    assert drawer.is_open

    drawer.toggle()
    assert not drawer.is_open
