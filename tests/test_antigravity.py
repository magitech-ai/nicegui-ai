"""Hermetic unit and interaction tests for the 1:1 Antigravity Desktop UI/UX suite (nicegui_ai.antigravity)."""

from nicegui_ai.antigravity import (
    ANTIGRAVITY_THEME_CSS,
    AntigravityApp,
    AntigravityIcon,
    AntigravityModelSelector,
    AutomationsView,
    AuxiliaryPane,
    ChatView,
    ConversationHistoryView,
    SearchConversationsModal,
    SettingsModal,
    Sidebar,
    TitleBar,
    WorkspaceCustomizationsView,
    create_default_artifact,
    create_default_automations,
    create_default_sessions,
    create_default_settings,
    create_default_skills,
    create_default_subagents,
    get_antigravity_svg,
)
from nicegui_ai.antigravity.state import ProjectConfig


def test_antigravity_theme_tokens():
    assert "#101010" in ANTIGRAVITY_THEME_CSS
    assert "#151515" in ANTIGRAVITY_THEME_CSS
    assert "#191919" in ANTIGRAVITY_THEME_CSS
    assert "#222222" in ANTIGRAVITY_THEME_CSS
    assert "#272727" in ANTIGRAVITY_THEME_CSS
    assert "#cccccc" in ANTIGRAVITY_THEME_CSS
    assert "#6e6e6e" in ANTIGRAVITY_THEME_CSS


def test_antigravity_icons():
    svg = get_antigravity_svg("antigravity_logo", size=18)
    assert "<svg" in svg
    icon = AntigravityIcon("terminal_tab", size=14)
    assert "<svg" in icon.content


def test_state_factories():
    settings = create_default_settings()
    sessions = create_default_sessions()
    automations = create_default_automations()
    subagents = create_default_subagents()
    skills = create_default_skills()
    artifact = create_default_artifact()

    assert len(settings.projects) == 4
    assert len(settings.mcp_servers) == 3
    assert len(sessions) >= 10
    assert sessions[0].id == "session-zero-state"
    assert sessions[1].id == "session-clone-rea"
    assert len(automations) == 3
    assert len(subagents) == 4
    assert len(skills) == 6
    assert artifact.id == "art-rea-report"


def test_title_bar():
    tb = TitleBar(initial_open_menu="File")
    assert tb.open_menu_name == "File"
    tb.toggle_menu("View")
    assert tb.open_menu_name == "View"
    tb.toggle_menu("View")
    assert tb.open_menu_name is None


def test_sidebar_navigation_and_actions():
    settings = create_default_settings()
    sessions = create_default_sessions()
    selected: list[str] = []
    sb = Sidebar(
        active_session_id="session-clone-rea",
        active_center_view="chat",
        sessions=sessions,
        projects=settings.projects,
        on_select_session=lambda sid: selected.append(sid),
        on_new_conversation=lambda _: None,
        on_open_history=lambda: None,
        on_open_automations=lambda: None,
        on_open_customizations=lambda: None,
        on_open_settings=lambda: None,
        on_open_search_modal=lambda: None,
        on_toggle_sidebar=lambda: None,
    )
    assert sb.active_session_id == "session-clone-rea"
    sb._toggle_project_folder("proj-mvge")
    assert sb.open_projects["proj-mvge"] is False


def test_antigravity_model_selector():
    chosen_models: list[str] = []
    selector = AntigravityModelSelector(
        selected_model="Gemini 3.8 Flash High",
        initial_open=True,
        on_select_model=lambda m: chosen_models.append(m),
    )
    assert selector.is_open is True
    model_def, _ = selector._parse_selected()
    selector._choose_model(model_def, "Medium")
    assert selector.selected_model == "Gemini 3.8 Flash Medium"
    assert chosen_models[-1] == "Gemini 3.8 Flash Medium"


def test_history_view_and_search_modal():
    settings = create_default_settings()
    sessions = create_default_sessions()
    hv = ConversationHistoryView(
        sessions=sessions,
        projects=settings.projects,
        active_session_id="session-clone-rea",
        on_select_session=lambda _: None,
        on_toggle_pin=lambda _: None,
        on_toggle_archive=lambda _: None,
        on_delete_session=lambda _: None,
        on_new_conversation=lambda: None,
    )
    assert len(hv._filtered_sessions()) >= 5
    hv._on_search_change("Mvgeos")
    assert all("mvgeos" in s.title.lower() for s in hv._filtered_sessions())

    modal = SearchConversationsModal(
        is_open=True,
        on_close=lambda: None,
        sessions=sessions,
        projects=settings.projects,
        on_select_session=lambda _: None,
        on_new_conversation=lambda: None,
        on_open_automations=lambda: None,
        on_open_settings=lambda: None,
    )
    assert modal.is_open is True
    modal.set_open(False)
    assert modal.is_open is False


def test_automations_view():
    settings = create_default_settings()
    automations = create_default_automations()
    av = AutomationsView(
        automations=automations,
        projects=settings.projects,
        on_toggle_automation=lambda _: None,
        on_delete_automation=lambda _: None,
        on_create_automation=lambda _: None,
        on_update_automation=lambda _: None,
        on_run_automation_now=lambda _: None,
        initial_modal_open=True,
        initial_selected_trigger_id="auto-1",
    )
    assert av.modal_open is True
    assert av.selected_trigger_id == "auto-1"


def test_workspace_customizations_view():
    settings = create_default_settings()
    cv = WorkspaceCustomizationsView(
        projects=settings.projects,
        active_project_id="proj-ag-studio",
        on_select_project=lambda _: None,
        on_open_global_customizations=lambda: None,
    )
    assert cv.scope_filter == "all"
    assert len(cv.skills) >= 3


def test_auxiliary_pane_all_tabs():
    art = create_default_artifact()
    subagents = create_default_subagents()
    pane = AuxiliaryPane(
        is_open=True,
        active_artifact=art,
        subagents=subagents,
        initial_tab="overview",
        initial_open_plus=True,
        initial_open_overview_customize=True,
        initial_open_diff_comment=True,
    )
    assert pane.active_tab == "overview"
    assert pane.plus_dropdown_open is True
    assert pane.customize_overview_open is True

    for tab in ("review", "terminal", "file", "browser", "agents", "new-tab"):
        pane.set_tab(tab)
        assert pane.active_tab == tab

    pane.set_tab("review")
    pane.draft_comment = "Looks great!"
    pane._submit_diff_comment("src/nicegui_ai/antigravity/auxiliary_pane.py", "221")
    assert any(c["text"] == "Looks great!" for c in pane.submitted_comments)

    pane.set_tab("terminal")
    pane.terminal_input = "uv run ruff check ."
    pane._execute_terminal_cmd()
    assert any(
        line_item["cmd"] == "uv run ruff check ." for line_item in pane.terminal_lines
    )


def test_chat_view_and_composer_controls():
    settings = create_default_settings()
    sessions = create_default_sessions()
    active_sess = sessions[1]  # Clone Antigravity UI Using Rea
    sent: list[str] = []

    cv = ChatView(
        session=active_sess,
        all_sessions=sessions,
        projects=settings.projects,
        settings=settings,
        initial_open_kebab=True,
        initial_open_modes=True,
        initial_open_side_question=True,
        initial_open_fastpick=True,
        initial_open_lifted_menu=True,
        initial_open_context=True,
        on_send_message=lambda txt, _: sent.append(txt),
    )
    assert cv.kebab_menu_open is True
    assert cv.modes_open is True
    assert cv.side_question_open is True
    assert cv.fastpick_open is True
    assert cv.lifted_menu_msg_id == active_sess.messages[0].id

    cv._select_slash_command("/goal")
    assert cv.input_text == "/goal "
    assert cv.fastpick_open is False

    cv.input_text = "Build 1:1 NiceGUI suite"
    cv._handle_send()
    assert sent == ["Build 1:1 NiceGUI suite"]

    # Zero-state session
    cv.set_session(sessions[0])
    assert len(cv.session.messages) == 0


def test_settings_modal_all_screens():
    settings = create_default_settings()
    skills = create_default_skills()
    sm = SettingsModal(
        is_open=True,
        initial_screen="general",
        settings=settings,
        skills=skills,
    )
    for screen in (
        "general",
        "browser",
        "notifications",
        "terminal",
        "workspaces",
        "labs",
        "appearance",
        "editor",
        "billing",
        "models",
        "customizations",
        "advanced",
        "about",
        "project:proj-mvge",
        "not-in-project",
        "shortcuts",
        "feedback",
        "account",
    ):
        sm.set_screen(screen)
        assert sm.active_screen == screen

    for subview in (
        "mcp-servers",
        "skills-manager",
        "hooks-manager",
        "browser-urls",
        "file-access-rules",
    ):
        sm.set_subview(subview)
        assert sm.active_subview == subview


def test_antigravity_app_orchestrator_and_deep_links():
    app = AntigravityApp(
        query_params={
            "openSettings": "true",
            "settingsScreen": "customizations",
            "openAux": "true",
            "auxTab": "review",
            "openDiffComment": "true",
        }
    )
    assert app.settings_open is True
    assert app.settings_screen == "customizations"
    assert app.aux_open is True
    assert app.aux_tab == "review"

    app._handle_send_message("Run full verification", [])
    assert app._active_session().messages[-2].content == "Run full verification"
    assert app._active_session().messages[-1].role == "agent"


def test_antigravity_app_callbacks():
    selected_project = []
    deleted_session = []
    opened_settings = []

    projs = [
        ProjectConfig(
            id="proj-mvge",
            name="mvge-desktop",
            folders=["/mnt/storage/projects/mvge-desktop"],
            active_conversations=2,
            archived_conversations=0,
        )
    ]

    app = AntigravityApp(
        projects=projs,
        on_select_project=lambda p: selected_project.append(p),
        on_delete_session=lambda s: deleted_session.append(s),
        on_open_settings=lambda screen: opened_settings.append(screen),
    )

    assert app.active_project_id == "proj-mvge"
    assert len(app.settings.projects) == 1

    app._handle_select_project("proj-mvge")
    assert selected_project == ["proj-mvge"]

    # Deleting active session resets to session-zero-state
    active_id = app.active_session_id
    app._handle_delete_session(active_id)
    assert deleted_session == [active_id]
    assert app.active_session_id == "session-zero-state"

    # Opening settings invokes callback without forcing in-memory modal open
    app._handle_open_settings("models")
    assert opened_settings == ["models"]
    assert app.settings_open is False


def test_chat_view_composer_hints_and_enter_handling():
    sent = []
    cv = ChatView(
        session=create_default_sessions()[0],
        all_sessions=create_default_sessions(),
        projects=[],
        settings=create_default_settings(),
        selected_model="test-model",
        on_send_message=lambda text, atts: sent.append(text),
    )
    cv.input_text = "Hello world"
    cv._handle_enter_press()
    assert sent == ["Hello world"]


def test_antigravity_app_settings_change_callback():
    changed = []
    app = AntigravityApp(
        on_settings_change=lambda s: changed.append(s),
    )
    app.settings.default_model = "google/gemini-2.5-pro"
    app._handle_settings_change(app.settings)
    assert len(changed) == 1
    assert changed[0].default_model == "google/gemini-2.5-pro"


def test_settings_modal_project_screen_contemplation():
    settings = create_default_settings()
    skills = create_default_skills()
    changed = []
    sm = SettingsModal(
        is_open=True,
        initial_screen="project:proj-mvge",
        settings=settings,
        skills=skills,
        on_settings_change=lambda s: changed.append(s),
    )
    proj = next(p for p in settings.projects if p.id == "proj-mvge")
    sm._update_project_field(proj, "contemplation_level", "x-high")
    assert proj.contemplation_level == "x-high"
    assert len(changed) == 1
    assert changed[0].projects[0].contemplation_level == "x-high"
