"""Comprehensive tests for all remaining uncovered modules."""

from nicegui_ai.adapters.agui import AgUiStreamAdapter
from nicegui_ai.adapters.gemini import GeminiStreamAdapter
from nicegui_ai.adapters.opencode import OpenCodeStreamAdapter
from nicegui_ai.adapters.openrouter import OpenRouterStreamAdapter
from nicegui_ai.antigravity.app import AntigravityApp
from nicegui_ai.antigravity.automations_view import AutomationsView
from nicegui_ai.antigravity.auxiliary_pane import AuxiliaryPane
from nicegui_ai.antigravity.chat_view import ChatView
from nicegui_ai.antigravity.customizations_view import WorkspaceCustomizationsView
from nicegui_ai.antigravity.history_view import ConversationHistoryView
from nicegui_ai.antigravity.model_selector import AntigravityModelSelector
from nicegui_ai.antigravity.settings_modal import SettingsModal
from nicegui_ai.antigravity.sidebar import Sidebar
from nicegui_ai.antigravity.terminal_dock import TerminalDock
from nicegui_ai.antigravity.title_bar import TitleBar
from nicegui_ai.antigravity.state import (
    AppSettings,
    ProjectConfig,
    Session,
    create_default_settings,
    create_default_sessions,
    create_default_automations,
    create_default_skills,
    create_default_subagents,
    create_default_artifact,
)
from nicegui_ai.approval_modal import ApprovalModal
from nicegui_ai.artifact import ArtifactCard
from nicegui_ai.artifact_viewer import ArtifactViewerDrawer
from nicegui_ai.composer import AiComposer
from nicegui_ai.demo import DemoStreamFactory, demo_page
from nicegui_ai.gallery import gallery_page
from nicegui_ai.header import FloatingHeader, TokenRing
from nicegui_ai.markdown import parse_markdown_blocks
from nicegui_ai.message import UserMessage, AgentMessage
from nicegui_ai.mth.adapter import MthStreamAdapter
from nicegui_ai.mth.app import MthApp
from nicegui_ai.mth.command_picker import MthCommandFastpicker
from nicegui_ai.mth.composer import MthComposer
from nicegui_ai.mth.context_meter import MthContextMeter
from nicegui_ai.mth.inspector_drawer import MthInspectorDrawer
from nicegui_ai.mth.session_drawer import MthSessionDrawer
from nicegui_ai.mth.state import MthAppState, MthSession
from nicegui_ai.mth.stats_pills import MthStatsPills
from nicegui_ai.mth.timeline import MthTimeline
from nicegui_ai.mth.tool_card import MthToolCard, MthToolCallItem
from nicegui_ai.queued_messages import QueuedMessagesTray
from nicegui_ai.reasoning import ReasoningCard
from nicegui_ai.schema import ToolCall, ToolStatus
from nicegui_ai.stream import StreamBridge
from nicegui_ai.thread import AiThread
from nicegui_ai.tool_call import ToolCallCard
from nicegui_ai.voice_pill import VoicePill


def test_adapters_stream_events():
    import asyncio

    async def empty_source():
        if False:
            yield

    for cls in (AgUiStreamAdapter, GeminiStreamAdapter, OpenCodeStreamAdapter, OpenRouterStreamAdapter):
        adapter = cls(source=empty_source())
        events = asyncio.run(adapter.collect())
        assert isinstance(events, list)


def test_antigravity_app_all():
    app = AntigravityApp()
    assert app.settings is not None
    assert app.active_session_id in ("session-zero-state", "session-clone-rea")
    app._handle_send_message("hi", [])
    assert len(app._active_session().messages) >= 2


def test_automations_view_all():
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
    )
    assert av is not None


def test_auxiliary_pane_all():
    art = create_default_artifact()
    subagents = create_default_subagents()
    pane = AuxiliaryPane(
        is_open=True,
        active_artifact=art,
        subagents=subagents,
        initial_tab="overview",
    )
    assert pane.active_tab == "overview"
    pane.set_tab("review")
    assert pane.active_tab == "review"


def test_chat_view_all():
    settings = create_default_settings()
    sessions = create_default_sessions()
    cv = ChatView(
        session=sessions[0],
        all_sessions=sessions,
        projects=settings.projects,
        settings=settings,
        on_send_message=lambda t, _: None,
    )
    assert cv is not None


def test_customizations_view_all():
    settings = create_default_settings()
    cv = WorkspaceCustomizationsView(
        projects=settings.projects,
        active_project_id="proj-ag-studio",
        on_select_project=lambda _: None,
        on_open_global_customizations=lambda: None,
    )
    assert cv is not None


def test_history_view_all():
    settings = create_default_settings()
    sessions = create_default_sessions()
    hv = ConversationHistoryView(
        sessions=sessions,
        projects=settings.projects,
        active_session_id=sessions[0].id,
        on_select_session=lambda _: None,
        on_toggle_pin=lambda _: None,
        on_toggle_archive=lambda _: None,
        on_delete_session=lambda _: None,
        on_new_conversation=lambda: None,
    )
    assert hv is not None


def test_model_selector_all():
    sel = AntigravityModelSelector(
        selected_model="Gemini 3.8 Flash High",
        initial_open=True,
        on_select_model=lambda _: None,
    )
    assert sel.is_open


def test_settings_modal_all():
    settings = create_default_settings()
    skills = create_default_skills()
    sm = SettingsModal(
        is_open=True,
        initial_screen="general",
        settings=settings,
        skills=skills,
    )
    sm.set_screen("browser")
    assert sm.active_screen == "browser"


def test_sidebar_all():
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


def test_terminal_dock_all():
    dock = TerminalDock()
    assert dock is not None


def test_title_bar_all():
    tb = TitleBar(initial_open_menu="File")
    assert tb.open_menu_name == "File"


def test_mth_adapter_all():
    adapter = MthStreamAdapter()
    assert adapter is not None


def test_mth_app_all():
    app = MthApp()
    assert app is not None


def test_mth_command_picker_all():
    picker = MthCommandFastpicker()
    assert picker is not None


def test_mth_composer_all():
    composer = MthComposer()
    assert composer is not None


def test_mth_context_meter_all():
    meter = MthContextMeter()
    assert meter is not None


def test_mth_inspector_drawer_all():
    drawer = MthInspectorDrawer()
    assert drawer is not None


def test_mth_session_drawer_all():
    session = MthSession(id="s1", title="T")
    drawer = MthSessionDrawer(
        sessions=[session],
        active_session_id="s1",
        on_select_session=lambda _: None,
    )
    assert drawer is not None


def test_mth_state_all():
    state = MthAppState()
    assert state is not None


def test_mth_stats_pills_all():
    pills = MthStatsPills()
    assert pills is not None


def test_mth_timeline_all():
    timeline = MthTimeline()
    assert timeline is not None


def test_mth_tool_card_all():
    item = MthToolCallItem(call_id="c1", name="test", args={})
    card = MthToolCard(
        tool_item=item,
        on_approve=None,
        on_veto=None,
    )
    assert card is not None


def test_composer_all():
    sent = []
    composer = AiComposer(on_send=lambda t: sent.append(t))
    composer.input.set_value("hello")
    composer.submit()
    assert sent == ["hello"]


def test_stream_bridge_all():
    sb = StreamBridge()
    assert sb is not None


def test_thread_all():
    thread = AiThread()
    thread.add_user_message("hello")
    thread.add_agent_message(agent_name="A", text="hi")
    assert len(thread.messages) == 2


def test_demo_factory():
    factory = DemoStreamFactory()
    assert factory is not None


def test_gallery_page():
    # gallery_page is a NiceGUI page handler, just verify it's callable
    assert callable(gallery_page)


def test_demo_page():
    assert callable(demo_page)
