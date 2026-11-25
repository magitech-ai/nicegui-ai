"""Hermetic tests for Magitech Harness (MTH) NiceGUI components."""

from typing import Any

import pytest

from nicegui_ai.mth.adapter import MthStreamAdapter
from nicegui_ai.mth.app import MthApp
from nicegui_ai.mth.command_picker import DEFAULT_COMMANDS, MthCommandFastpicker
from nicegui_ai.mth.composer import MthComposer, MthModelSelectDialog
from nicegui_ai.mth.context_meter import MthContextBreakdownDialog, MthContextMeter
from nicegui_ai.mth.session_drawer import MthSessionDrawer
from nicegui_ai.mth.state import (
    MthAppState,
    MthAttachment,
    MthCommandItem,
    MthContextOccupancy,
    MthSession,
    MthToolCallItem,
    MthTurnItem,
    ToolExecutionStatus,
    format_clock_time,
    format_tokens,
)
from nicegui_ai.mth.theme import MTH_THEME_CSS, setup_mth_theme
from nicegui_ai.mth.timeline import (
    MthAssistantBubble,
    MthCompactionItem,
    MthReasoningRow,
    MthRunningTail,
    MthTimeline,
    MthTurnUsageDialog,
    MthUserBubble,
)
from nicegui_ai.mth.tool_card import MthToolCard


def test_mth_theme_setup():
    """Verify MTH theme CSS contains root variables and dark mode colors."""
    setup_mth_theme()
    assert "--mth-bg:" in MTH_THEME_CSS
    assert "--mth-card:" in MTH_THEME_CSS
    assert "--mth-primary:" in MTH_THEME_CSS
    assert "--mth-border:" in MTH_THEME_CSS


def test_mth_app_state_lifecycle():
    """Verify MthAppState session and turn management."""
    state = MthAppState(
        active_profile="default",
        profiles=["default", "code", "research"],
    )
    assert state.active_profile == "default"
    assert len(state.sessions) == 0

    # Create session
    session = state.create_session(title="Refactoring Turn Loop")
    assert session.id is not None
    assert state.active_session_id == session.id
    assert len(state.sessions) == 1

    # Add turn
    turn = state.add_turn(user_text="Optimize caching")
    assert turn.turn_id is not None
    assert turn.user_text == "Optimize caching"
    assert turn.status == "idle"
    assert state.get_active_turn() == turn

    # Add tool call to turn
    tool = state.add_tool_call(
        turn_id=turn.turn_id,
        call_id="call-1",
        name="read_file",
        args={"path": "src/engine.py"},
    )
    assert tool.name == "read_file"
    assert tool.status == ToolExecutionStatus.PENDING

    # Resolve tool call
    state.resolve_tool_call(
        call_id="call-1",
        result="def engine(): pass",
        status=ToolExecutionStatus.COMPLETED,
    )
    assert tool.status == ToolExecutionStatus.COMPLETED
    assert tool.result == "def engine(): pass"

    # Test pin, rename, fork, archive, delete
    assert state.pin_session(session.id) is True
    assert state.pin_session(session.id) is False
    assert state.pin_session("non-existent") is False

    state.rename_session(session.id, "Renamed Session")
    assert session.title == "Renamed Session"
    state.rename_session("non-existent", "Title")

    forked = state.fork_session(session.id)
    assert forked is not None
    assert forked.title == "Fork of Renamed Session"
    assert state.active_session_id == forked.id
    assert state.fork_session("non-existent") is None

    assert state.archive_session(session.id) is True
    assert state.archive_session("non-existent") is False

    assert "default" in state.get_workspaces()

    assert state.delete_session(session.id) is True
    assert state.delete_session("non-existent") is False
    assert len(state.sessions) == 1


def test_mth_tool_card_rendering_and_approval():
    """Verify MthToolCard states and approval gate callbacks."""
    approved_calls: list[str] = []
    vetoed_calls: list[str] = []

    tool_item = MthToolCallItem(
        call_id="t-100",
        name="bash",
        args={"command": "rm -rf tmp/"},
        status=ToolExecutionStatus.AWAITING_APPROVAL,
        approval_required=True,
    )

    card = MthToolCard(
        tool_item=tool_item,
        on_approve=lambda call_id: approved_calls.append(call_id),
        on_veto=lambda call_id: vetoed_calls.append(call_id),
    )

    assert card.tool_item.name == "bash"
    assert card.tool_item.status == ToolExecutionStatus.AWAITING_APPROVAL

    # Trigger approval
    card.approve()
    assert "t-100" in approved_calls
    assert card.tool_item.status == ToolExecutionStatus.EXECUTING

    # Complete
    card.complete("Directory cleaned")
    assert card.tool_item.status == ToolExecutionStatus.COMPLETED
    assert card.tool_item.result == "Directory cleaned"


def test_mth_specialized_tool_cards():
    """Verify specialized tool card rendering for bash, file mutation, and ask question."""
    from nicegui_ai.mth.tool_card import (
        AskQuestionToolCard,
        BashToolCard,
        FileMutationToolCard,
    )

    # 1. Bash Tool Card
    bash_item = MthToolCallItem(
        call_id="b-1",
        name="bash",
        args={"command": "uv run pytest", "cwd": "/repo"},
    )
    bash_card = BashToolCard(bash_item)
    assert bash_card.command == "uv run pytest"
    assert bash_card.cwd == "/repo"
    bash_card.set_output("10 passed in 0.2s", exit_code=0)
    assert bash_card.exit_code == 0
    assert bash_card.tool_item.status == ToolExecutionStatus.COMPLETED

    # 2. File Mutation Card
    file_item = MthToolCallItem(
        call_id="f-1",
        name="edit_file",
        args={"path": "src/main.py", "diff": "--- a\n+++ b\n@@ -1 +1 @@\n-old\n+new"},
    )
    file_card = FileMutationToolCard(file_item)
    assert file_card.file_path == "src/main.py"
    assert file_card.diff_content.startswith("--- a")
    file_card.complete("File updated successfully")
    assert file_card.tool_item.result == "File updated successfully"

    # 3. Ask Question Card
    answered: list[dict[str, Any]] = []
    question_item = MthToolCallItem(
        call_id="q-1",
        name="ask_question",
        args={
            "question": "Which architecture pattern do you prefer?",
            "options": ["Hexagonal", "Layered", "Microkernel"],
        },
    )
    question_card = AskQuestionToolCard(
        question_item,
        on_answer=lambda ans: answered.append(ans),
    )
    assert question_card.question_text == "Which architecture pattern do you prefer?"
    assert len(question_card.options) == 3
    question_card.submit_answer(selected=["Hexagonal"], custom="With async seams")
    assert answered == [{"selected": ["Hexagonal"], "custom": "With async seams"}]

    # 4. Read Tool Card
    read_item = MthToolCallItem(
        call_id="r-1",
        name="read_file",
        args={"path": "README.md"},
    )
    from nicegui_ai.mth.tool_card import (
        MthApprovalPanel,
        ReadToolCard,
        create_tool_card,
    )

    read_card = ReadToolCard(read_item)
    assert read_card.target_path == "README.md"
    read_card.complete("# Title")
    assert read_card.tool_item.result == "# Title"

    # 5. Tool Card Factory
    c1 = create_tool_card(bash_item)
    assert isinstance(c1, BashToolCard)
    c2 = create_tool_card(file_item)
    assert isinstance(c2, FileMutationToolCard)
    c3 = create_tool_card(question_item)
    assert isinstance(c3, AskQuestionToolCard)
    c4 = create_tool_card(read_item)
    assert isinstance(c4, ReadToolCard)
    generic_item = MthToolCallItem(call_id="g-1", name="custom_tool")
    c5 = create_tool_card(generic_item)
    assert type(c5) is MthToolCard

    # 6. MthApprovalPanel
    allowed_calls: list[str] = []
    rejected_calls: list[str] = []
    panel = MthApprovalPanel(
        call_id="appr-1",
        tool_name="bash",
        reason="Bash command execution requires permission: rm -rf tmp/",
        command_detail="rm -rf tmp/",
        on_allow=lambda cid: allowed_calls.append(cid),
        on_reject=lambda cid: rejected_calls.append(cid),
    )
    assert not panel.answered
    panel.allow()
    assert panel.answered
    assert allowed_calls == ["appr-1"]
    panel.allow()  # idempotent
    assert len(allowed_calls) == 1

    panel2 = MthApprovalPanel(
        call_id="appr-2",
        tool_name="edit_file",
        on_reject=lambda cid: rejected_calls.append(cid),
    )
    panel2.reject()
    assert panel2.answered
    assert rejected_calls == ["appr-2"]


def test_mth_composer_interaction():
    """Verify MthComposer text submission, cancellation, attachments, and tool row actions."""
    sent_prompts: list[str] = []
    aborted: list[bool] = []
    model_changes: list[tuple[str, str]] = []
    perm_changes: list[str] = []
    plan_toggles: list[bool] = []
    added_attachments: list[MthAttachment] = []
    removed_attachments: list[str] = []

    composer = MthComposer(
        on_send=lambda text: sent_prompts.append(text),
        on_abort=lambda: aborted.append(True),
        on_model_change=lambda m, eff: model_changes.append((m, eff)),
        on_permission_change=lambda p: perm_changes.append(p),
        on_plan_toggle=lambda active: plan_toggles.append(active),
        on_attachment_add=lambda att: added_attachments.append(att),
        on_attachment_remove=lambda aid: removed_attachments.append(aid),
        slash_commands=["/compact", "/clear", "/profile", "/help", "/plan", "/goal"],
    )

    # Set prompt and submit
    composer.set_text("Hello agent")
    composer.submit()
    assert sent_prompts == ["Hello agent"]
    assert composer.get_text() == ""

    # Test running state toggling action button to abort
    composer.set_running(True)
    assert composer.is_running
    composer.abort()
    assert aborted == [True]
    composer.set_running(False)
    assert not composer.is_running

    # Slash command fastpicker detection
    assert composer.matches_slash_command("/com") == ["/compact"]
    assert composer.matches_slash_command("/p") == ["/profile", "/plan"]

    # Input change and ghost hints
    composer.input.set_value("/plan ")
    composer._handle_input_change(None)
    assert not composer.hint_label.classes.count("hidden")

    composer.input.set_value("normal prompt")
    composer._handle_input_change(None)
    assert "hidden" in composer.hint_label.classes

    # Permission preset selection
    composer._set_permission("workspace-write")
    assert composer.permission_preset == "workspace-write"
    assert perm_changes == ["workspace-write"]

    # Plan mode toggle
    composer._toggle_plan_mode()
    assert composer.plan_mode is True
    assert plan_toggles == [True]
    composer._toggle_plan_mode()
    assert composer.plan_mode is False
    assert plan_toggles == [True, False]

    # Model selection handler
    composer._handle_model_selected("reasoner-pro", "high")
    assert composer.current_model == "reasoner-pro"
    assert composer.reasoning_effort == "high"
    assert model_changes == [("reasoner-pro", "high")]

    # Attachments
    att = composer.add_attachment(name="specs.md", size_bytes=2048, is_image=False)
    assert att.name == "specs.md"
    assert len(composer.attachments) == 1
    assert added_attachments == [att]

    img = composer.add_attachment(name="screenshot.png", size_bytes=5120, is_image=True)
    assert img.is_image is True
    assert len(composer.attachments) == 2

    composer._remove_attachment(att.id)
    assert len(composer.attachments) == 1
    assert removed_attachments == [att.id]

    # Submitting with attachment clears attachments
    composer.submit()
    assert len(composer.attachments) == 0

    # Test attach click helper
    composer._handle_attach_click()
    assert len(composer.attachments) == 1

    # Context occupancy update
    occ = MthContextOccupancy(used_tokens=50000, context_window=100000)
    composer.update_context_occupancy(occ)
    assert composer.context_occupancy.used_tokens == 50000


def test_mth_context_meter_and_breakdown_dialog():
    """Verify MthContextMeter visual calculations and MthContextBreakdownDialog."""
    assert format_tokens(500) == "500"
    assert format_tokens(1500) == "1.5K"
    assert format_tokens(45000) == "45.0K"
    assert format_tokens(100000) == "100K"
    assert format_tokens(1500000) == "1.5M"
    assert format_tokens(100000000) == "100M"

    occ = MthContextOccupancy(
        used_tokens=64000,
        context_window=128000,
        system_tokens=8000,
        tools_tokens=12000,
        message_tokens=44000,
    )
    assert occ.percent() == 50.0

    meter = MthContextMeter(occupancy=occ)
    assert meter.occupancy.percent() == 50.0

    # High occupancy ring color trigger
    high_occ = MthContextOccupancy(used_tokens=120000, context_window=128000)
    meter.set_occupancy(high_occ)
    assert meter.occupancy.percent() >= 90.0

    # Zero window defensive check
    zero_occ = MthContextOccupancy(used_tokens=0, context_window=0)
    assert zero_occ.percent() == 0.0

    # Test breakdown dialog
    dialog = MthContextBreakdownDialog(occupancy=occ)
    assert dialog.occupancy == occ


def test_mth_command_fastpicker():
    """Verify MthCommandFastpicker search filtering, category grouping, and selection."""
    selected_commands: list[MthCommandItem] = []
    picker = MthCommandFastpicker(
        commands=DEFAULT_COMMANDS,
        on_select=lambda cmd: selected_commands.append(cmd),
    )

    # All commands when query is empty
    assert len(picker._get_filtered_commands()) == len(DEFAULT_COMMANDS)

    # Filter by slash token
    picker.filter_text = "/pla"
    filtered = picker._get_filtered_commands()
    assert len(filtered) == 1
    assert filtered[0].token == "/plan"

    # Filter by description
    picker.filter_text = "checkpoint"
    filtered_desc = picker._get_filtered_commands()
    assert len(filtered_desc) == 1
    assert filtered_desc[0].token == "/compact"

    # Enter key selection
    picker.filter_text = "/goal"
    picker._on_enter(None)
    assert len(selected_commands) == 1
    assert selected_commands[0].token == "/goal"


def test_mth_model_select_dialog():
    """Verify MthModelSelectDialog search, reasoning effort toggle, and confirmation."""
    selected: list[tuple[str, str]] = []
    models = ["default-chat", "reasoner-pro", "gpt-4o", "claude-3-5-sonnet"]
    dialog = MthModelSelectDialog(
        current_model="default-chat",
        available_models=models,
        reasoning_effort="medium",
        on_select=lambda m, eff: selected.append((m, eff)),
    )

    # Search filter
    dialog.search_query = "reasoner"
    dialog._render_model_list()

    # Change effort
    dialog._set_effort("high")
    assert dialog.reasoning_effort == "high"

    # Select model and confirm
    dialog._select_model("reasoner-pro")
    assert dialog.selected_model == "reasoner-pro"
    dialog._confirm()
    assert selected == [("reasoner-pro", "high")]


def test_mth_timeline_extended_components():
    """Verify MthUserBubble, MthAssistantBubble, MthTurnUsageDialog, and MthCompactionItem."""
    from datetime import UTC, datetime

    now_iso = datetime.now(UTC).isoformat()
    assert format_clock_time(now_iso) != ""
    assert format_clock_time("invalid") == ""

    # User bubble actions
    copied_prompts: list[str] = []
    forked_turns: list[str] = []
    edited_prompts: list[str] = []

    turn = MthTurnItem(
        turn_id="turn-42",
        user_text="Deploy release v2",
        assistant_text="Release v2 deployed.",
        tokens_used=1200,
        uncached_input_tokens=200,
        cache_read_tokens=800,
        cache_write_tokens=100,
        output_tokens=100,
        model_name="default-chat",
    )

    user_bubble = MthUserBubble(
        turn=turn,
        on_copy=lambda t: copied_prompts.append(t),
        on_fork=lambda tid: forked_turns.append(tid),
        on_edit=lambda t: edited_prompts.append(t),
    )
    user_bubble._handle_copy()
    user_bubble._handle_fork()
    user_bubble._handle_edit()
    assert copied_prompts == ["Deploy release v2"]
    assert forked_turns == ["turn-42"]
    assert edited_prompts == ["Deploy release v2"]

    # Assistant bubble
    copied_assistant: list[str] = []
    assistant_bubble = MthAssistantBubble(
        turn=turn,
        on_copy=lambda t: copied_assistant.append(t),
        on_fork=lambda tid: forked_turns.append(tid),
    )
    assistant_bubble._handle_copy()
    assistant_bubble._handle_fork()
    assert copied_assistant == ["Release v2 deployed."]

    # Turn usage dialog
    MthTurnUsageDialog.show(turn)

    # Compaction Item
    compaction = MthCompactionItem(
        summary="Initial setup folded",
        folded_count=6,
        tokens_saved=8400,
    )
    assert compaction.folded_count == 6
    assert compaction.tokens_saved == 8400

    # Running tail
    tail = MthRunningTail(status_label="Executing bash...")
    assert tail.label.text == "Executing bash..."
    tail.tick()
    tail.update_label("Waiting for token...")
    assert tail.label.text == "Waiting for token..."


def test_mth_session_drawer():
    """Verify MthSessionDrawer lists sessions, groups by workspace, supports search, pin, and rail mode."""
    from datetime import UTC, datetime, timedelta

    from nicegui_ai.mth.session_drawer import MthSessionRow
    from nicegui_ai.mth.state import format_relative_time

    now = datetime.now(UTC)
    assert format_relative_time(now.isoformat()) == "just now"
    assert format_relative_time((now - timedelta(minutes=5)).isoformat()) == "5m"
    assert format_relative_time((now - timedelta(hours=3)).isoformat()) == "3h"
    assert format_relative_time((now - timedelta(days=2)).isoformat()) == "2d"
    assert format_relative_time("invalid-date") == "recently"

    switched_sessions: list[str] = []
    new_sessions_created: list[str] = []
    pinned_sessions: list[str] = []
    renamed_sessions: list[tuple[str, str]] = []
    forked_sessions: list[str] = []
    archived_sessions: list[str] = []
    deleted_sessions: list[str] = []
    settings_opened: list[bool] = []

    s1 = MthSession(
        id="s1", title="Alpha Project", workspace="backend", tokens_used=1200
    )
    s2 = MthSession(
        id="s2",
        title="Beta Feature",
        workspace="frontend",
        tokens_used=4500,
        pinned=True,
    )
    s3 = MthSession(id="s3", title="Archived Task", workspace="backend", archived=True)
    sessions = [s1, s2, s3]

    drawer = MthSessionDrawer(
        sessions=sessions,
        active_session_id="s1",
        on_select_session=lambda sid: switched_sessions.append(sid),
        on_new_session=lambda ws: new_sessions_created.append(ws),
        on_pin_session=lambda sid: pinned_sessions.append(sid),
        on_rename_session=lambda sid, title: renamed_sessions.append((sid, title)),
        on_fork_session=lambda sid: forked_sessions.append(sid),
        on_archive_session=lambda sid: archived_sessions.append(sid),
        on_delete_session=lambda sid: deleted_sessions.append(sid),
        on_open_settings=lambda: settings_opened.append(True),
    )

    # Expanded drawer checks
    assert not drawer.collapsed
    drawer.select("s2")
    assert switched_sessions == ["s2"]
    drawer.create_new()
    assert new_sessions_created == ["default"]

    # Search filter
    drawer._toggle_search()
    assert drawer.show_search_input
    drawer.search_filter = "beta"
    filtered = drawer._get_filtered_sessions()
    assert len(filtered) == 1
    assert filtered[0].id == "s2"
    drawer._clear_search()
    assert drawer.search_filter == ""

    # Group by flat vs workspace
    drawer._set_group_by("flat")
    assert drawer.group_by == "flat"
    drawer._set_group_by("workspace")
    assert drawer.group_by == "workspace"

    # Filter archived
    drawer._set_filter_archived("only")
    assert drawer.filter_archived == "only"
    assert len(drawer._get_filtered_sessions()) == 1
    assert drawer._get_filtered_sessions()[0].id == "s3"
    drawer._set_filter_archived("hide")
    assert len(drawer._get_filtered_sessions()) == 2

    # Folder toggle
    drawer._toggle_folder("backend")
    assert "backend" in drawer.collapsed_folders
    drawer._toggle_folder("backend")
    assert "backend" not in drawer.collapsed_folders

    # Action triggers on drawer
    drawer._handle_pin("s1")
    assert pinned_sessions == ["s1"]
    drawer._handle_rename("s1", "Alpha Renamed")
    assert renamed_sessions == [("s1", "Alpha Renamed")]
    drawer._handle_fork("s1")
    assert forked_sessions == ["s1"]
    drawer._handle_archive("s1")
    assert archived_sessions == ["s1"]
    drawer._handle_delete_session("s1")
    assert deleted_sessions == ["s1"]
    drawer._handle_settings()
    assert settings_opened == [True]

    # Test MthSessionRow component directly
    row = MthSessionRow(
        session=s2,
        is_active=True,
        on_select=lambda sid: switched_sessions.append(sid),
        on_pin=lambda sid: pinned_sessions.append(sid),
        on_rename=lambda sid, t: renamed_sessions.append((sid, t)),
        on_fork=lambda sid: forked_sessions.append(sid),
        on_archive=lambda sid: archived_sessions.append(sid),
        on_delete=lambda sid: deleted_sessions.append(sid),
    )
    assert row.is_active
    row._handle_pin()
    row._handle_fork()
    row._handle_archive()

    # Toggle to Collapsed Rail mode (56px)
    drawer.toggle()
    assert drawer.collapsed
    assert "w-14" in drawer.classes
    drawer.select("s2")
    # Rail search expands drawer
    drawer._handle_rail_search()
    assert not drawer.collapsed
    assert drawer.show_search_input


def test_mth_timeline_progression():
    """Verify MthTimeline handles user messages, deliberation, and tool cards."""
    timeline = MthTimeline()
    turn = MthTurnItem(turn_id="turn-1", user_text="Inspect repository")
    timeline.render_turn(turn)

    # Add reasoning thought
    timeline.append_reasoning(
        turn_id="turn-1", thought="Reading directory structure..."
    )
    # Add assistant markdown text
    timeline.append_assistant_text(turn_id="turn-1", text="Repository inspected.")

    assert len(timeline.rendered_turns) == 1
    assert timeline.rendered_turns["turn-1"].user_text == "Inspect repository"


@pytest.mark.asyncio
async def test_mth_stream_adapter():
    """Verify MthStreamAdapter processes streamed events."""
    adapter = MthStreamAdapter()
    received_tokens: list[str] = []
    received_reasoning: list[str] = []
    resolved_tools: list[str] = []

    adapter.on_token(lambda chunk: received_tokens.append(chunk))
    adapter.on_reasoning(lambda thought: received_reasoning.append(thought))
    adapter.on_tool_resolved(lambda name, res: resolved_tools.append(f"{name}:{res}"))

    await adapter.feed_token("Hello ")
    await adapter.feed_token("world!")
    await adapter.feed_reasoning("Planning steps...")
    await adapter.feed_tool_resolution("read_file", "file contents")

    assert received_tokens == ["Hello ", "world!"]
    assert received_reasoning == ["Planning steps..."]
    assert resolved_tools == ["read_file:file contents"]


def test_mth_app_assembly():
    """Verify MthApp mounts without error and sets up the full interface."""
    state = MthAppState(active_profile="default")
    app = MthApp(state=state)
    assert app.state == state
    assert app.timeline is not None
    assert app.composer is not None
    assert app.session_drawer is not None
    assert app.inspector_drawer is not None

    # Test toggles
    app.toggle_sidebar()
    assert state.sidebar_collapsed
    app.toggle_inspector()
    assert state.inspector_open

    # Test show diff
    from nicegui_ai.mth.state import MthDiffItem

    diff = MthDiffItem(
        file_path="src/code.py", diff_text="+new\n-old", added_lines=1, removed_lines=1
    )
    app.show_diff(diff)
    assert state.active_diff == diff
    assert state.inspector_open

    # Test profile change
    app._handle_profile_change("research")
    assert state.active_profile == "research"

    # Test send and abort
    app._handle_send("Analyze performance")
    assert len(state.get_active_session().turns) == 1
    assert app.composer.is_running
    app._handle_abort()
    assert not app.composer.is_running


def test_mth_session_stats_and_formatting():
    """Verify MthSessionStats computations and duration formatting."""
    from nicegui_ai.mth.state import MthSessionStats
    from nicegui_ai.mth.stats_pills import MthStatsPills, format_duration

    assert format_duration(0) == "0.0s"
    assert format_duration(1500) == "1.5s"
    assert format_duration(75000) == "1m 15s"

    stats = MthSessionStats(
        turns=2,
        steps=5,
        llm_ms=2000.0,
        tool_ms=500.0,
        ttft_ms=600.0,
        ttft_steps=2,
        decode_ms=1000.0,
        decode_tokens=40,
        uncached_input_tokens=100,
        cache_read_tokens=400,
        cache_write_tokens=50,
        output_tokens=60,
    )
    assert stats.tokens_per_second() == 40.0
    assert stats.billed_input_tokens() == 550
    assert stats.total_tokens() == 610
    # cache read 400 / 550 * 100 = 72.7%
    assert stats.cache_hit_percent() == 72.7

    pills = MthStatsPills(metrics=stats)
    assert "40.0 tok/s" in pills.activity_label.text
    assert "610 tokens" in pills.usage_label.text
    assert "Cache 72.7%" in pills.usage_label.text

    # Test empty stats
    empty_stats = MthSessionStats()
    assert empty_stats.tokens_per_second() == 0.0
    assert empty_stats.cache_hit_percent() is None
    pills.update_metrics(empty_stats)
    assert "0.0 tok/s" in pills.activity_label.text


def test_mth_reasoning_row_and_turn_navigator():
    """Verify deliberation accordion and turn navigator behavior."""
    from nicegui_ai.mth.timeline import (
        MthTurnNavigator,
        clean_first_line,
    )

    assert clean_first_line("**Thinking:** step 1\nstep 2") == "Thinking: step 1"
    assert clean_first_line("") == ""

    row = MthReasoningRow(initial_thought="First thought", is_running=True)
    assert row.preview_label.text == "First thought"
    row.append_thought("Second thought")
    assert "Second thought" in row.body_label.text
    row.set_running(False)
    assert not row.is_running

    # Turn navigator
    jumped: list[str] = []
    nav = MthTurnNavigator()
    nav.add_turn_mark("t-1", "Inspect files", lambda _, tid="t-1": jumped.append(tid))
    assert len(nav.turn_marks) == 1


def test_mth_inspector_drawer_and_unified_diff(tmp_path):
    """Verify Right Inspector Drawer tabs, diff generator, and terminal dock."""
    from nicegui_ai.mth.inspector_drawer import (
        MthDiffPreview,
        MthFileTree,
        MthInspectorDrawer,
        MthTerminalDock,
        generate_unified_diff,
    )

    diff = generate_unified_diff(
        "test.py",
        "print('hello')\n",
        "print('hello world')\n",
    )
    assert diff.added_lines == 1
    assert diff.removed_lines == 1
    assert "+print('hello world')" in diff.diff_text

    preview = MthDiffPreview(diff_item=diff)
    assert preview.diff_item == diff
    preview._copy_diff()

    # File tree
    test_file = tmp_path / "example.txt"
    test_file.write_text("sample content")
    selected_files: list[str] = []
    tree = MthFileTree(
        workspace_root=str(tmp_path), on_file_select=lambda p: selected_files.append(p)
    )
    tree._handle_click(str(test_file))
    assert str(test_file) in selected_files

    # Terminal dock
    ran_cmds: list[str] = []
    terminal = MthTerminalDock(on_run_command=lambda cmd: ran_cmds.append(cmd))
    terminal.cmd_input.set_value("echo 42")
    terminal._handle_run()
    assert ran_cmds == ["echo 42"]
    terminal.append_output("echo 42", "42", exit_code=0)
    assert len(terminal.history) == 1
    terminal.clear_history()
    assert len(terminal.history) == 0

    # Inspector Drawer assembly
    closed: list[bool] = []
    drawer = MthInspectorDrawer(
        workspace_root=str(tmp_path),
        active_diff=diff,
        on_close=lambda: closed.append(True),
    )
    assert drawer.active_tab == "diff"
    drawer.set_tab("files")
    assert drawer.active_tab == "files"
    drawer.set_tab("terminal")
    assert drawer.active_tab == "terminal"

    # Fullscreen presentation toggle
    assert not drawer.is_fullscreen
    drawer.toggle_fullscreen()
    assert drawer.is_fullscreen
    drawer.toggle_fullscreen()
    assert not drawer.is_fullscreen

    drawer._handle_close()
    assert closed == [True]
    drawer.show_file(str(test_file))
    assert drawer.active_diff is not None
