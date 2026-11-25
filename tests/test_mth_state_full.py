"""Tests for mth state module - pure logic, easy to cover."""

from nicegui_ai.mth.state import (
    MthAppState,
    MthSession,
    MthSessionStats,
    MthDiffItem,
    MthToolCallItem,
    MthTurnItem,
    MthAttachment,
    MthCommandItem,
    MthContextOccupancy,
    ToolExecutionStatus,
)


def test_mth_session_stats_all():
    stats = MthSessionStats(
        turns=5, steps=10, llm_ms=100.0, tool_ms=50.0,
        ttft_ms=200.0, ttft_steps=3, decode_ms=300.0,
        decode_tokens=150, uncached_input_tokens=50,
        cache_read_tokens=25, cache_write_tokens=10,
        output_tokens=75,
    )
    assert stats.tokens_per_second() == 150 / 0.3
    assert stats.billed_input_tokens() == 85


def test_mth_session_stats_zero_decode():
    stats = MthSessionStats()
    assert stats.tokens_per_second() == 0.0


def test_mth_tool_call_item():
    item = MthToolCallItem(call_id="c1", name="search", args={"q": "x"})
    assert item.call_id == "c1"
    assert item.name == "search"


def test_mth_turn_item():
    turn = MthTurnItem(turn_id="t1", user_text="hello", status="executing")
    assert turn.turn_id == "t1"
    assert turn.status == "executing"


def test_mth_diff_item():
    diff = MthDiffItem(file_path="/tmp/test.py", diff_text="--- a\n+++ b")
    assert diff.file_path == "/tmp/test.py"


def test_mth_attachment():
    att = MthAttachment(id="a1", name="file.txt")
    assert att.id == "a1"


def test_mth_command_item():
    cmd = MthCommandItem(token="/run", name="Run", description="Run command")
    assert cmd.token == "/run"


def test_mth_context_occupancy():
    occ = MthContextOccupancy(used_tokens=500, context_window=1000)
    assert occ.used_tokens == 500


def test_mth_app_state_all():
    state = MthAppState()
    assert state.active_profile == "default"
    assert len(state.sessions) >= 0
    sess = state.create_session(workspace="default")
    assert sess.id is not None
    assert state.get_active_session() is not None


def test_mth_session_all():
    session = MthSession(id="s1", title="Test Session")
    session.turns.append(type("T", (), {"turn_id": "t1", "text": "hi", "is_deliberating": False, "status": "idle", "is_compacted": False, "compaction_summary": None, "reasoning": [], "assistant_text": "", "tool_calls": [], "tokens_used": 0})())
    assert len(session.turns) == 1


def test_tool_execution_status():
    assert ToolExecutionStatus.PENDING == "pending"
    assert ToolExecutionStatus.EXECUTING == "executing"
    assert ToolExecutionStatus.COMPLETED == "completed"
    assert ToolExecutionStatus.FAILED == "failed"
