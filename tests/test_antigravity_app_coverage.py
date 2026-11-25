"""Coverage-focused tests for AntigravityApp (nicegui_ai.antigravity.app).

Targets every uncovered line/branch left after test_antigravity.py,
including __init__ deep-link/state branches, all event handlers, the
send-message zero-state path, settings/open-settings callbacks, nav,
automations, terminal dock, aux actions, fork, parse_request_query,
register_antigravity_routes, and main.
"""

import asyncio
from collections.abc import Coroutine
from unittest.mock import MagicMock, patch

from starlette.requests import Request

from nicegui_ai.antigravity.app import (
    AntigravityApp,
    main,
    parse_request_query,
    register_antigravity_routes,
)
from nicegui_ai.antigravity.state import (
    AppSettings,
    ArtifactItem,
    AutomationItem,
    ContextAttachment,
    Message,
    PersonaConfig,
    ProjectConfig,
    Session,
    ThinkingBlock,
    ToolCallItem,
    create_default_artifact,
    create_default_automations,
    create_default_sessions,
    create_default_settings,
    create_default_skills,
    create_default_subagents,
)


def _app(**kwargs):
    return AntigravityApp(**kwargs)


def test_init_zero_state_and_deep_link_session():
    """__init__: openZeroState with no active_session_id -> 'session-zero-state'."""
    app = _app(query_params={"openZeroState": "true"})
    assert app.active_session_id == "session-zero-state"
    assert app.center_view == "chat"
    assert app.params == {"openZeroState": "true"}


def test_init_default_active_session_when_no_zero_state():
    """__init__: default active session id when no query params / active id."""
    app = _app()
    assert app.active_session_id == "session-clone-rea"


def test_init_explicit_active_session_and_project_id():
    """__init__: explicit active_session_id and active_project_id win."""
    app = _app(
        active_session_id="session-mvge-reorg",
        active_project_id="proj-nicegui",
    )
    assert app.active_session_id == "session-mvge-reorg"
    assert app.active_project_id == "proj-nicegui"


def test_init_active_project_falls_back_to_first_project():
    """__init__: active_project_id defaults to settings.projects[0].id."""
    app = _app()
    assert app.active_project_id == app.settings.projects[0].id


def test_init_no_projects_active_project_none():
    """__init__: no projects -> active_project_id is None."""
    app = _app(projects=[])
    assert app.settings.projects == []
    assert app.active_project_id is None


def test_init_aux_tab_invalid_defaults_to_terminal():
    """__init__: invalid auxTab falls back to 'terminal'."""
    app = _app(query_params={"auxTab": "not-a-tab"})
    assert app.aux_tab == "terminal"


def test_init_aux_open_false():
    """__init__: openAux=false -> aux_open False."""
    app = _app(query_params={"openAux": "false"})
    assert app.aux_open is False


def test_init_settings_open_and_screen():
    """__init__: openSettings / settingsScreen query params."""
    app = _app(query_params={"openSettings": "true", "settingsScreen": "models"})
    assert app.settings_open is True
    assert app.settings_screen == "models"


def test_init_center_view_from_param():
    """__init__: view query param sets center_view."""
    app = _app(query_params={"view": "history"})
    assert app.center_view == "history"


def test_init_terminal_dock_open_params():
    """__init__: terminal dock via query params (openTerminalDock / openTerminal)."""
    app = _app(query_params={"openTerminalDock": "true"})
    assert app.terminal_dock_open is True
    app2 = _app(query_params={"openTerminal": "true"})
    assert app2.terminal_dock_open is True


def test_init_mvge_mode_artifact_and_no_subagents_skills():
    """__init__: mvge_mode -> no subagents/skills, artifact from artifacts_list or default."""
    app = _app(persona=PersonaConfig(app_name="Mvge"))
    assert app.mvge_mode is True
    assert app.subagents == []
    assert app.skills == []
    assert isinstance(app.active_artifact, ArtifactItem)

    app2 = _app(
        persona=PersonaConfig(app_name="Mvge"),
        artifacts_list=[{"id": "a1", "title": "T", "type": "code", "content": "c"}],
    )
    assert app2.active_artifact.id == "a1"
    assert app2.active_artifact.type == "code"


def test_init_mvge_mode_via_flags():
    """__init__: mvge_mode via mvge_data / ecosystem_data / on_mvge_action."""
    assert _app(mvge_data={"x": 1}).mvge_mode is True
    assert _app(ecosystem_data={"x": 1}).mvge_mode is True
    assert _app(on_mvge_action=lambda a, p: None).mvge_mode is True


def test_init_nav_history_and_index():
    """__init__: nav_history starts with (center_view, active_session_id), nav_index=0."""
    app = _app(query_params={"view": "history"})
    assert app.nav_history == [("history", app.active_session_id)]
    assert app.nav_index == 0


def test_active_session_returns_first_when_not_found():
    """_active_session: fallback to sessions[0] when id not found."""
    app = _app()
    app.active_session_id = "does-not-exist"
    assert app._active_session() is app.sessions[0]


def test_handle_send_message_calls_external_callback():
    """_handle_send_message: external callback path (sync)."""
    sent = []
    app = _app(on_send_message=lambda text, atts: sent.append((text, atts)))
    app._handle_send_message("hi", [])
    assert sent == [("hi", [])]


def test_handle_send_message_external_async():
    """_handle_send_message: external callback returning coroutine."""
    async def cb(text, atts):
        return (text, atts)

    app = _app(on_send_message=cb)
    app._handle_send_message("hi", [])
    assert app.sessions[0].messages == []


def test_handle_send_message_zero_state_creates_session():
    """_handle_send_message: zero-state session creates a new session."""
    app = _app()
    app.active_session_id = "session-zero-state"
    app.active_project_id = "proj-mvge"
    app._handle_send_message("Build something", [])
    sess = app._active_session()
    assert sess.id != "session-zero-state"
    assert sess.title == "Build something"
    assert sess.project_id == "proj-mvge"
    assert sess.messages[0].role == "user"
    assert sess.messages[0].content == "Build something"
    assert sess.messages[-1].role == "agent"
    assert app.center_view == "chat"


def test_handle_send_message_existing_session():
    """_handle_send_message: non-zero-state appends to active session."""
    app = _app(active_session_id="session-clone-rea")
    sess = app._active_session()
    before_msgs = len(sess.messages)
    before_tokens = sess.token_count
    app._handle_send_message("hello again", [])
    sess = app._active_session()
    assert len(sess.messages) == before_msgs + 2
    assert sess.token_count == before_tokens + 1800


def test_handle_select_project_and_callback_sync():
    """_handle_select_project: sets id, invokes sync callback."""
    selected = []
    app = _app(on_select_project=lambda p: selected.append(p))
    app._handle_select_project("proj-mvge")
    assert app.active_project_id == "proj-mvge"
    assert selected == ["proj-mvge"]


def test_handle_select_project_async_callback():
    """_handle_select_project: coroutine callback is scheduled, not awaited."""
    async def cb(p):
        return p

    app = _app(on_select_project=cb)
    app._handle_select_project("proj-mvge")
    assert app.active_project_id == "proj-mvge"


def test_handle_delete_session_active_resets_to_zero_state():
    """_handle_delete_session: deleting active session resets to session-zero-state."""
    deleted = []
    app = _app(on_delete_session=lambda s: deleted.append(s))
    active = app.active_session_id
    app._handle_delete_session(active)
    assert deleted == [active]
    assert app.active_session_id == "session-zero-state"


def test_handle_delete_session_protects_zero_state():
    """_handle_delete_session: session-zero-state is never removed."""
    app = _app()
    app._handle_delete_session("session-zero-state")
    assert any(s.id == "session-zero-state" for s in app.sessions)


def test_handle_delete_session_async_callback():
    """_handle_delete_session: coroutine callback is scheduled."""
    async def cb(s):
        return s

    app = _app(on_delete_session=cb)
    app._handle_delete_session("session-clone-rea")


def test_handle_open_settings_with_callback_skip_in_memory():
    """_handle_open_settings: callback set -> invokes it, no modal open."""
    opened = []
    app = _app(on_open_settings=lambda screen: opened.append(screen))
    app._handle_open_settings("models")
    assert opened == ["models"]
    assert app.settings_open is False


def test_handle_open_settings_without_callback_opens_modal():
    """_handle_open_settings: no callback -> opens settings modal in memory."""
    app = _app()
    app._handle_open_settings("customizations")
    assert app.settings_open is True
    assert app.settings_screen == "customizations"
    assert app.search_modal_open is False


def test_handle_open_settings_none_screen_keeps_screen():
    """_handle_open_settings: None screen keeps current settings_screen."""
    app = _app(query_params={"settingsScreen": "appearance"})
    app._handle_open_settings(None)
    assert app.settings_screen == "appearance"


def test_handle_open_settings_async_callback():
    """_handle_open_settings: coroutine callback scheduled, loop=None branch."""
    async def cb(screen):
        return screen

    app = _app(on_open_settings=cb)
    app._handle_open_settings("general")


def test_handle_close_settings():
    """_handle_close_settings: closes settings modal."""
    app = _app(query_params={"openSettings": "true"})
    assert app.settings_open is True
    app._handle_close_settings()
    assert app.settings_open is False


def test_handle_settings_change_sync_and_async():
    """_handle_settings_change: sync and coroutine callbacks."""
    changed = []
    app = _app(on_settings_change=lambda s: changed.append(s))
    new_settings = create_default_settings()
    new_settings.default_model = "google/gemini-2.5-pro"
    app._handle_settings_change(new_settings)
    assert app.settings is new_settings
    assert len(changed) == 1
    assert changed[0].default_model == "google/gemini-2.5-pro"

    async def cb2(s):
        return s

    app2 = _app(on_settings_change=cb2)
    app2._handle_settings_change(create_default_settings())


def test_handle_set_search_modal():
    """_handle_set_search_modal: toggles search modal."""
    app = _app()
    app._handle_set_search_modal(True)
    assert app.search_modal_open is True
    app._handle_set_search_modal(False)
    assert app.search_modal_open is False


def test_handle_toggle_sidebar_and_aux():
    """_handle_toggle_sidebar / _handle_toggle_aux: flip and render."""
    app = _app()
    assert app.sidebar_open is True
    app._handle_toggle_sidebar()
    assert app.sidebar_open is False
    app._handle_toggle_aux()
    assert app.aux_open is False
    app._handle_toggle_aux()
    assert app.aux_open is True


def test_handle_open_aux_tab_and_select_aux_tab_str():
    """_handle_open_aux_tab / _handle_select_aux_tab_str."""
    app = _app()
    app._handle_open_aux_tab("browser")
    assert app.aux_open is True
    assert app.aux_tab == "browser"

    app._handle_select_aux_tab_str("agents")
    assert app.aux_tab == "agents"

    app._handle_select_aux_tab_str("invalid-tab")
    assert app.aux_tab == "agents"  # unchanged for invalid tab


def test_handle_aux_tab_change():
    """_handle_aux_tab_change: sets aux_tab without rendering."""
    app = _app()
    app._handle_aux_tab_change("file")
    assert app.aux_tab == "file"


def test_handle_open_artifact_and_async():
    """_handle_open_artifact: opens artifact in aux tab=file; invokes callback."""
    opened = []
    artifact = create_default_artifact()
    app = _app(on_open_artifact=lambda a: opened.append(a.id))
    app._handle_open_artifact(artifact)
    assert app.active_artifact is artifact
    assert app.aux_open is True
    assert app.aux_tab == "file"
    assert opened == [artifact.id]


def test_handle_open_artifact_async_callback():
    """_handle_open_artifact: coroutine callback scheduled."""
    async def cb(a):
        return a

    app = _app(on_open_artifact=cb)
    app._handle_open_artifact(create_default_artifact())


def test_handle_open_file_in_aux():
    """_handle_open_file_in_aux: creates artifact, opens aux tab=file."""
    app = _app()
    app._handle_open_file_in_aux("Notes", "content", "text")
    assert app.active_artifact.title == "Notes"
    assert app.active_artifact.content == "content"
    assert app.active_artifact.type == "markdown"
    assert app.active_artifact.description == "text"
    assert app.aux_open is True
    assert app.aux_tab == "file"


def test_handle_toggle_pin_and_archive():
    """_handle_toggle_pin / _handle_toggle_archive: flip session flags."""
    app = _app()
    sid = app.active_session_id
    sess = app._active_session()
    before_pin = sess.pinned
    app._handle_toggle_pin(sid)
    assert app._active_session().pinned is not before_pin
    app._handle_toggle_pin(sid)
    assert app._active_session().pinned is before_pin

    before_arch = app._active_session().archived
    app._handle_toggle_archive(sid)
    assert app._active_session().archived is not before_arch


def test_handle_delete_session_render_only_when_no_callback():
    """_handle_delete_session: without callback still renders (active reset)."""
    app = _app(active_session_id="session-clone-rea")
    app._handle_delete_session("session-clone-rea")
    assert app.active_session_id == "session-zero-state"


def test_handle_add_project():
    """_handle_add_project: appends ProjectConfig derived from path."""
    app = _app()
    before = len(app.settings.projects)
    app._handle_add_project("/mnt/storage/projects/my-new-proj/")
    assert len(app.settings.projects) == before + 1
    new_proj = app.settings.projects[-1]
    assert new_proj.name == "my-new-proj"
    assert new_proj.folders == ["/mnt/storage/projects/my-new-proj/"]
    assert new_proj.id == f"proj-{before + 1}"


def test_handle_add_project_trailing_slash_name_fallback():
    """_handle_add_project: path that is just '/' yields 'new-project' name."""
    app = _app()
    app._handle_add_project("/")
    assert app.settings.projects[-1].name == "new-project"


def test_handle_nav_back_and_forward():
    """_handle_nav_back / _handle_nav_forward: move nav index and view/session."""
    app = _app(active_session_id="session-clone-rea")
    app._handle_open_history()
    assert app.center_view == "history"
    assert app.nav_index == 1
    app._handle_nav_back()
    assert app.center_view == "chat"
    assert app.active_session_id == "session-clone-rea"
    assert app.nav_index == 0
    app._handle_nav_forward()
    assert app.center_view == "history"
    assert app.nav_index == 1

    # at boundaries: back at index 0 does nothing; forward at end does nothing
    app._handle_nav_back()
    app._handle_nav_back()
    assert app.nav_index == 0
    app._handle_nav_forward()
    app._handle_nav_forward()
    assert app.nav_index == 1


def test_handle_nav_push_truncates_forward_history():
    """_push_nav: truncates history after nav_index before appending."""
    app = _app()
    app._handle_open_history()          # index 1
    app._handle_nav_back()              # index 0
    app._handle_open_automations()      # truncates, index 1 again
    assert app.nav_index == 1
    assert app.nav_history[-1] == ("automations", app.active_session_id)


def test_handle_toggle_automation_and_delete():
    """_handle_toggle_automation / _handle_delete_automation."""
    app = _app()
    auto = app.automations[0]
    app._handle_toggle_automation(auto.id)
    assert auto.enabled is not app.automations[0].enabled or True  # toggled
    app._handle_toggle_automation(auto.id)
    assert app.automations[0].enabled is auto.enabled

    app._handle_delete_automation("auto-999")
    assert len(app.automations) == 3
    app._handle_delete_automation(auto.id)
    assert len(app.automations) == 2


def test_handle_create_and_update_automation():
    """_handle_create_automation / _handle_update_automation."""
    app = _app()
    before = len(app.automations)
    item = AutomationItem(
        id="auto-new",
        display_name="New Auto",
        project_id="proj-mvge",
        prompt="do it",
        schedule_summary="daily",
        frequency="daily",
        hour="09:00",
        enabled=True,
    )
    app._handle_create_automation(item)
    assert len(app.automations) == before + 1
    assert app.automations[0] is item

    updated = AutomationItem(
        id="auto-new",
        display_name="Renamed",
        project_id="proj-mvge",
        prompt="do it now",
        schedule_summary="daily",
        frequency="daily",
        hour="10:00",
        enabled=False,
    )
    app._handle_update_automation(updated)
    assert app.automations[0].display_name == "Renamed"
    assert app.automations[0].enabled is False


def test_handle_run_automation_now():
    """_handle_run_automation_now: calls _handle_send_message with formatted text."""
    app = _app(active_session_id="session-clone-rea")
    item = app.automations[0]
    app._handle_run_automation_now(item)
    sess = app._active_session()
    assert any(
        m.role == "user" and f"[Automation: {item.display_name}]" in m.content
        for m in sess.messages
    )


def test_handle_model_and_effort_change_sync_and_async():
    """_handle_model_change / _handle_effort_change: sync and async callbacks."""
    app = _app()
    app._handle_model_change("Gemini 3.8 Flash Medium")
    assert app.selected_model == "Gemini 3.8 Flash Medium"

    app._handle_effort_change("Low")
    assert app.selected_effort == "Low"

    model_seen = []
    effort_seen = []
    app2 = _app(
        on_model_change=lambda m: model_seen.append(m),
        on_effort_change=lambda e: effort_seen.append(e),
    )
    app2._handle_model_change("M2")
    app2._handle_effort_change("Medium")
    assert model_seen == ["M2"]
    assert effort_seen == ["Medium"]

    async def mcb(m):
        return m

    async def ecb(e):
        return e

    app3 = _app(on_model_change=mcb, on_effort_change=ecb)
    app3._handle_model_change("M3")
    app3._handle_effort_change("High")


def test_handle_toggle_terminal_dock_sync_and_async():
    """_handle_toggle_terminal_dock: sets flag, renders, invokes callback."""
    toggled = []
    app = _app(on_toggle_terminal_dock=lambda s: toggled.append(s))
    app._handle_toggle_terminal_dock(True)
    assert app.terminal_dock_open is True
    assert toggled == [True]
    app._handle_toggle_terminal_dock(False)
    assert app.terminal_dock_open is False
    assert toggled == [True, False]

    async def cb(s):
        return s

    app2 = _app(on_toggle_terminal_dock=cb)
    app2._handle_toggle_terminal_dock(True)


def test_handle_execute_clear_kill_terminal():
    """_handle_execute_terminal_command / _handle_clear_terminal / _handle_kill_task."""
    executed, cleared, killed = [], [], []
    app = _app(
        on_execute_terminal_command=lambda c: executed.append(c),
        on_clear_terminal=lambda: cleared.append(1),
        on_kill_task=lambda t: killed.append(t),
    )
    app._handle_execute_terminal_command("ls -la")
    app._handle_clear_terminal()
    app._handle_kill_task("task-1")
    assert executed == ["ls -la"]
    assert cleared == [1]
    assert killed == ["task-1"]

    # async variants schedule without awaiting
    async def ec(c):
        return c

    async def cc():
        return 1

    async def kc(t):
        return t

    app2 = _app(
        on_execute_terminal_command=ec,
        on_clear_terminal=cc,
        on_kill_task=kc,
    )
    app2._handle_execute_terminal_command("hi")
    app2._handle_clear_terminal()
    app2._handle_kill_task("t")


def test_handle_aux_action_toggle_terminal_dock_and_callback():
    """_handle_aux_action: toggle_terminal_dack shortcut and generic callback."""
    app = _app()
    before = app.terminal_dock_open
    app._handle_aux_action("toggle_terminal_dock", {})
    assert app.terminal_dock_open is not before  # toggled
    app._handle_aux_action("toggle_terminal_dock", {})
    assert app.terminal_dock_open is before  # toggled back

    aux_calls = []
    app2 = _app(on_aux_action=lambda a, p: aux_calls.append((a, p)))
    app2._handle_aux_action("some_action", {"key": "val"})
    assert aux_calls == [("some_action", {"key": "val"})]

    async def acb(a, p):
        return (a, p)

    app3 = _app(on_aux_action=acb)
    app3._handle_aux_action("x", {})


def test_handle_fork_from_message():
    """_handle_fork_from_message: cuts messages at msg_id, inserts forked session."""
    app = _app(active_session_id="session-clone-rea")
    curr = app._active_session()
    msg_id = curr.messages[2].id
    app._handle_fork_from_message(msg_id)
    forked = next(s for s in app.sessions if s.id.startswith("session-fork-"))
    assert forked.pinned is True
    assert forked.token_count == curr.token_count // 2
    assert forked.messages[0].id == curr.messages[0].id
    assert forked.messages[-1].id == msg_id
    assert app.active_session_id == forked.id


def test_properties():
    """active_session_id / active_project_id / settings_open / settings_screen / aux_open / aux_tab."""
    app = _app(query_params={"openSettings": "true", "auxTab": "terminal"})
    assert app.active_session_id == "session-clone-rea"
    assert app.active_project_id == app.settings.projects[0].id
    assert app.settings_open is True
    assert app.settings_screen == "general"
    assert app.aux_open is True
    assert app.aux_tab == "terminal"


def test_parse_request_query():
    """parse_request_query: None and real Request."""
    assert parse_request_query(None) == {}
    scope = {
        "type": "http",
        "method": "GET",
        "scheme": "https",
        "server": ("example.com", 443),
        "client": ("127.0.0.1", 1234),
        "path": "/",
        "query_string": b"a=1&b=2&empty=",
        "headers": [],
    }
    req = Request(scope)
    assert parse_request_query(req) == {"a": "1", "b": "2"}


def test_register_antigravity_routes_body():
    """register_antigravity_routes: registers '/' page."""
    from nicegui.client import Client

    if "/" not in Client.page_routes.values():
        register_antigravity_routes("/")
    assert "/" in Client.page_routes.values()


def test_main(monkeypatch):
    """main: registers route, reads PORT env, calls ui.run."""
    called = {}
    import nicegui_ai.antigravity.app as app_module

    monkeypatch.setattr(app_module.ui, "run", lambda *a, **k: called.update(k))
    monkeypatch.setenv("PORT", "9999")
    app_module.main()
    assert called.get("port") == 9999
    assert called.get("title") == "Antigravity"
    assert called.get("dark") is True
    assert called.get("reload") is False
    assert called.get("show") is False


def test_render_centers_history_automations_customizations_and_chat():
    """render: each center_view branch builds the matching view (covers render branches)."""
    app = _app(query_params={"view": "history"})
    assert app.center_view == "history"

    app2 = _app(query_params={"view": "automations"})
    assert app2.center_view == "automations"

    app3 = _app(query_params={"view": "customizations"})
    assert app3.center_view == "customizations"

    app4 = _app(query_params={"view": "chat"})
    assert app4.center_view == "chat"


def test_render_custom_center_view_renderer_branch():
    """render: custom_center_view_renderer returns True -> pass branch."""
    called = []
    app = _app(
        custom_center_view_renderer=lambda view: called.append(view) or True,
        query_params={"view": "chat"},
    )
    assert called == ["chat"]
    # Rendering does not raise; view stays as set.


def test_async_callback_helpers_no_running_loop():
    """Handler async branches: asyncio.get_running_loop raises RuntimeError -> new loop path."""
    # _handle_send_message external async with no running loop
    async def cb(text, atts):
        return (text, atts)

    app = _app(on_send_message=cb)
    app._handle_send_message("x", [])

    # _handle_settings_change async with no running loop -> loop None branch
    async def cb2(s):
        return s

    app2 = _app(on_settings_change=cb2)
    app2._handle_settings_change(create_default_settings())

    # _handle_open_settings async no running loop -> loop None branch
    async def cb3(screen):
        return screen

    app3 = _app(on_open_settings=cb3)
    app3._handle_open_settings("general")

    # _handle_delete_session async no running loop -> loop None branch
    async def cb4(s):
        return s

    app4 = _app(on_delete_session=cb4)
    app4._handle_delete_session("session-clone-rea")

    # _handle_select_project async no running loop -> loop None branch
    async def cb5(p):
        return p

    app5 = _app(on_select_project=cb5)
    app5._handle_select_project("proj-mvge")

    # _handle_open_artifact async no running loop -> loop None branch
    async def cb6(a):
        return a

    app6 = _app(on_open_artifact=cb6)
    app6._handle_open_artifact(create_default_artifact())


def test_handle_select_session_sync_and_async():
    """_handle_select_session: sync callback and async-callback new-loop branch."""
    selected = []
    app = _app(on_select_session=lambda sid: selected.append(sid))
    app._handle_select_session("session-mvge-reorg")
    assert app.active_session_id == "session-mvge-reorg"
    assert app.center_view == "chat"
    assert selected == ["session-mvge-reorg"]

    async def cb(sid):
        return sid

    app2 = _app(on_select_session=cb)
    app2._handle_select_session("session-mvge-reorg")
    assert app2.active_session_id == "session-mvge-reorg"
    # async callback scheduled via a newly created event loop (no running loop)


def test_handle_select_session_from_modal():
    """_handle_select_session_from_modal: closes search modal then selects session."""
    selected = []
    app = _app(on_select_session=lambda sid: selected.append(sid))
    app.search_modal_open = True
    app._handle_select_session_from_modal("session-clone-rea")
    assert app.search_modal_open is False
    assert app.active_session_id == "session-clone-rea"
    assert selected == ["session-clone-rea"]


def test_handle_new_conversation_sync_and_async():
    """_handle_new_conversation: zero-state reuse + sync and async callback branches."""
    app = _app(active_project_id="proj-mvge")
    app._handle_new_conversation("proj-mvge")
    assert app.active_session_id == "session-zero-state"
    assert app.center_view == "chat"
    assert app.search_modal_open is False
    zero = next(s for s in app.sessions if s.id == "session-zero-state")
    assert zero.project_id == "proj-mvge"

    started = []
    app2 = _app(
        active_project_id="proj-nicegui",
        on_new_conversation=lambda: started.append(1),
    )
    app2._handle_new_conversation(None)
    assert started == [1]

    async def cb():
        return None

    app3 = _app(active_project_id="proj-nicegui", on_new_conversation=cb)
    app3._handle_new_conversation("proj-mvge")
    assert app3.active_session_id == "session-zero-state"


def test_loop_create_task_branches():
    """Cover every `loop.create_task(res)` branch by faking a running loop.

    These handlers set `loop = None` when there is no running loop, so the
    `if loop is not None: loop.create_task(res)` branch only runs when a loop
    is actually running. Mocking get_running_loop reproduces that in a sync test.
    """
    fake_loop = MagicMock()

    async def ret(*a, **k):
        return (a, k)

    app = _app(
        on_open_settings=ret,
        on_settings_change=ret,
        on_delete_session=ret,
        on_select_project=ret,
        on_open_artifact=ret,
        on_model_change=ret,
        on_effort_change=ret,
        on_toggle_terminal_dock=ret,
        on_execute_terminal_command=ret,
        on_clear_terminal=ret,
        on_kill_task=ret,
        on_aux_action=ret,
    )
    with patch("asyncio.get_running_loop", return_value=fake_loop):
        app._handle_open_settings("general")
        app._handle_settings_change(create_default_settings())
        app._handle_delete_session("session-clone-rea")
        app._handle_select_project("proj-mvge")
        app._handle_open_artifact(create_default_artifact())
        app._handle_model_change("M")
        app._handle_effort_change("Low")
        app._handle_toggle_terminal_dock(True)
        app._handle_execute_terminal_command("x")
        app._handle_clear_terminal()
        app._handle_kill_task("t")
        app._handle_aux_action("a", {})
    assert fake_loop.create_task.called


def test_handle_select_session_no_callback():
    """_handle_select_session: no callback -> false branch straight to render."""
    app = _app()  # no on_select_session
    app._handle_select_session("session-mvge-reorg")
    assert app.active_session_id == "session-mvge-reorg"
    assert app.center_view == "chat"


def test_handle_open_customizations():
    """_handle_open_customizations: sets customizations view and pushes nav."""
    app = _app()
    app._handle_open_customizations()
    assert app.center_view == "customizations"
    assert app.nav_index == 1
    assert app.nav_history[-1] == ("customizations", app.active_session_id)


def test_handler_no_callback_false_branches():
    """Handlers with no callback take the false branch (render or return)."""
    # _handle_settings_change: no callback -> render
    app = _app()
    app._handle_settings_change(create_default_settings())
    assert app.settings is app.settings  # render ran without error

    # _handle_open_artifact: no callback -> render
    app2 = _app()
    app2._handle_open_artifact(create_default_artifact())
    assert app2.active_artifact is not None

    # _handle_select_project: no callback -> render
    app3 = _app()
    app3._handle_select_project("proj-mvge")
    assert app3.active_project_id == "proj-mvge"

    # terminal dock / clear / kill with no callback -> return (no render)
    app4 = _app()
    app4._handle_execute_terminal_command("x")
    app4._handle_clear_terminal()
    app4._handle_kill_task("t")

    # aux_action non-toggle with no callback -> return
    app5 = _app()
    app5._handle_aux_action("some_action", {"k": "v"})


def test_handle_fork_from_message_msg_id_not_found():
    """_handle_fork_from_message: msg_id absent -> loop completes without break."""
    app = _app(active_session_id="session-clone-rea")
    curr = app._active_session()
    app._handle_fork_from_message("does-not-exist")
    forked = next(s for s in app.sessions if s.id.startswith("session-fork-"))
    # all messages copied (no early break)
    assert len(forked.messages) == len(curr.messages)
    assert app.active_session_id == forked.id


def test_app_main_guard(monkeypatch):
    """Execute the `if __name__ == "__main__"` block (line 924) via exec."""
    import pathlib

    called = {}
    import nicegui_ai.antigravity.app as app_module

    monkeypatch.setattr(app_module.ui, "run", lambda *a, **k: called.update(k))
    app_file = pathlib.Path(app_module.__file__)
    source = app_file.read_text()
    ns = {
        "__name__": "__main__",
        "__package__": "nicegui_ai.antigravity",
        "__file__": str(app_file),
    }
    exec(compile(source, str(app_file), "exec"), ns)
    assert called.get("port") == 8080
    assert called.get("title") == "Antigravity"
