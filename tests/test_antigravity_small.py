"""Tests for antigravity terminal_dock, title_bar, model_selector, icons, sidebar."""

from nicegui_ai.antigravity.icons import AntigravityIcon, get_antigravity_svg
from nicegui_ai.antigravity.model_selector import AntigravityModelSelector
from nicegui_ai.antigravity.sidebar import Sidebar
from nicegui_ai.antigravity.state import (
    create_default_sessions,
    create_default_settings,
)
from nicegui_ai.antigravity.terminal_dock import TerminalDock
from nicegui_ai.antigravity.title_bar import TitleBar


def test_terminal_dock_init():
    dock = TerminalDock()
    assert dock is not None


def test_title_bar_init():
    bar = TitleBar(initial_open_menu="File")
    assert bar.open_menu_name == "File"
    bar.toggle_menu("View")
    assert bar.open_menu_name == "View"
    bar.toggle_menu("View")
    assert bar.open_menu_name is None


def test_model_selector_init():
    chosen = []
    sel = AntigravityModelSelector(
        selected_model="Gemini 3.8 Flash High",
        initial_open=True,
        on_select_model=lambda m: chosen.append(m),
    )
    assert sel.is_open
    model_def, _ = sel._parse_selected()
    sel._choose_model(model_def, "Medium")
    assert sel.selected_model == "Gemini 3.8 Flash Medium"


def test_icons_all():
    svg = get_antigravity_svg("chevron-right", size=16)
    assert "<svg" in svg
    svg2 = get_antigravity_svg("nonexistent", size=8)
    assert "<svg" in svg2
    icon = AntigravityIcon("terminal_tab", size=14)
    assert "<svg" in icon.content
    icon.set_icon("home", size=24)
    assert icon.icon_name == "home"
    assert icon.icon_size == 24


def test_sidebar_init():
    settings = create_default_settings()
    sessions = create_default_sessions()
    sb = Sidebar(
        active_session_id=sessions[0].id,
        active_center_view="chat",
        sessions=sessions,
        projects=settings.projects,
        on_select_session=lambda _: None,
        on_new_conversation=lambda _: None,
        on_open_history=lambda: None,
        on_open_automations=lambda: None,
        on_open_customizations=lambda: None,
        on_open_settings=lambda: None,
        on_open_search_modal=lambda: None,
        on_toggle_sidebar=lambda: None,
    )
    assert sb is not None
