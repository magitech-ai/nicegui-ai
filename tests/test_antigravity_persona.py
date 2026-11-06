"""Tests for Antigravity PersonaConfig, custom diffs, and approval gates."""

from nicegui_ai.antigravity import (
    AuxiliaryPane,
    PersonaConfig,
    Sidebar,
    TitleBar,
    create_default_sessions,
    create_default_settings,
)
from nicegui_ai.antigravity.auxiliary_pane import ChangedFile, DiffLine
from nicegui_ai.antigravity.chat_view import ChatView
from nicegui_ai.antigravity.state import Session, ToolCallItem


def test_persona_config_defaults():
    persona = PersonaConfig()
    assert persona.app_name == "Antigravity"
    assert persona.session_label == "Conversation"
    assert persona.sessions_label == "Conversations"
    assert persona.tool_label == "Tool"
    assert persona.tools_label == "Tools"
    assert persona.token_label == "Tokens"
    assert persona.agent_label == "Agent"
    assert persona.extension_label == "Extension"
    assert persona.extensions_label == "Extensions"


def test_persona_config_mvge():
    persona = PersonaConfig(
        app_name="Mvge",
        session_label="Tome",
        sessions_label="Tomes",
        tool_label="Spell",
        tools_label="Spells",
        token_label="Mana",
        extension_label="Rune",
        extensions_label="Runes",
    )
    assert persona.app_name == "Mvge"
    assert persona.session_label == "Tome"
    assert persona.tool_label == "Spell"


def test_title_bar_with_mvge_persona():
    persona = PersonaConfig(app_name="Mvge")
    tb = TitleBar(persona=persona)
    assert "Mvge" in tb._menus
    assert "Antigravity" not in tb._menus
    menu_labels = [entry.label for entry in tb._menus["Mvge"]]
    assert any("About Mvge" in label for label in menu_labels)
    assert any("Quit Mvge" in label for label in menu_labels)


def test_sidebar_with_mvge_persona():
    settings = create_default_settings()
    sessions = create_default_sessions()
    persona = PersonaConfig(session_label="Tome", sessions_label="Tomes")
    sb = Sidebar(
        active_session_id="session-clone-rea",
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
        persona=persona,
    )
    assert sb.persona.session_label == "Tome"


def test_auxiliary_pane_custom_changed_files():
    custom_diffs = [
        ChangedFile(
            name="test_file.py",
            path="tests/test_file.py",
            additions=12,
            deletions=3,
            status="modified",
            lines=[
                DiffLine(type="hunk", text="@@ -1,3 +1,12 @@"),
                DiffLine(type="add", text="+import pytest", new_num=1),
            ],
        )
    ]
    pane = AuxiliaryPane(
        is_open=True,
        initial_tab="review",
        changed_files=custom_diffs,
    )
    assert pane.changed_files == custom_diffs
    assert len(pane.changed_files) == 1
    assert pane.changed_files[0].name == "test_file.py"


def test_chat_view_tool_approval_buttons():
    approved: list[str] = []
    vetoed: list[str] = []

    pending_tool = ToolCallItem(
        id="tc-pending-1",
        tool_name="run_command",
        action="Run dangerous command",
        parameters={"command": "rm -rf /tmp/test"},
        output="",
        status="approval_required",
    )
    from nicegui_ai.antigravity.state import Message

    sess = Session(
        id="sess-approval",
        title="Approval Test",
        timestamp="Just now",
        token_count=100,
        messages=[
            Message(
                id="msg-1",
                role="agent",
                content="Need approval",
                timestamp="Just now",
                tool_calls=[pending_tool],
            )
        ],
    )
    settings = create_default_settings()
    cv = ChatView(
        session=sess,
        all_sessions=[sess],
        projects=settings.projects,
        settings=settings,
        on_send_message=lambda _t, _a: None,
        on_approve_tool=lambda tid: approved.append(tid),
        on_veto_tool=lambda tid: vetoed.append(tid),
    )
    assert cv.on_approve_tool is not None
    assert cv.on_veto_tool is not None
    cv._handle_approve_tool("tc-pending-1")
    assert approved == ["tc-pending-1"]
    cv._handle_veto_tool("tc-pending-1")
    assert vetoed == ["tc-pending-1"]
