"""Tests for mth app module."""

from nicegui_ai.mth.app import MthApp, register_mth_routes, main
from nicegui_ai.mth.state import MthAppState


def test_mth_app_init_default():
    app = MthApp()
    assert app.state is not None


def test_mth_app_init_with_state():
    state = MthAppState()
    app = MthApp(state=state)
    assert app.state is state


def test_mth_app_toggle_sidebar():
    app = MthApp()
    app.toggle_sidebar()


def test_mth_app_toggle_inspector():
    app = MthApp()
    app.toggle_inspector()


def test_mth_app_handle_model_change():
    app = MthApp()
    app._handle_model_change("gemini-pro", "High")


def test_mth_app_handle_permission_change():
    app = MthApp()
    app._handle_permission_change("strict")


def test_mth_app_handle_plan_toggle():
    app = MthApp()
    app._handle_plan_toggle(True)
    app._handle_plan_toggle(False)


def test_mth_app_handle_profile_change():
    app = MthApp()
    app._handle_profile_change("default")


def test_mth_app_handle_session_select():
    app = MthApp()
    app._handle_session_select("s1")


def test_mth_app_handle_new_session():
    app = MthApp()
    app._handle_new_session(workspace="default")


def test_mth_app_handle_pin_rename_fork():
    app = MthApp()
    app._handle_pin_session("s1")
    app._handle_rename_session("s1", "New Title")
    app._handle_fork_session("s1")


def test_mth_app_handle_archive_delete():
    app = MthApp()
    app._handle_archive_session("s1")
    app._handle_delete_session("s1")


def test_mth_app_handle_file_select():
    app = MthApp()
    app._handle_file_select("/tmp/test.py")


def test_mth_app_handle_send_abort():
    app = MthApp()
    app._handle_send("hello world")
    app._handle_abort()


def test_mth_app_handle_fork_turn():
    app = MthApp()
    app._handle_fork_turn("turn-1")


def test_mth_app_handle_edit_prompt():
    app = MthApp()
    app._handle_edit_prompt("edited text")


def test_register_mth_routes():
    register_mth_routes()


def test_main_is_callable():
    assert callable(main)
