"""Tests for remaining uncovered core modules."""

from nicegui_ai.composer import AiComposer
from nicegui_ai.reasoning import ReasoningCard
from nicegui_ai.task_tray import TaskTray
from nicegui_ai.thread import AiThread
from nicegui_ai.tool_call import ToolCall, ToolCallCard, ToolStatus
from nicegui_ai.voice_pill import VoicePill


def test_thread_lines_95_96():
    """Cover thread.py lines 95-96 (clear and add after clear)."""
    thread = AiThread()
    thread.add_user_message("first")
    thread.clear()
    assert len(thread.messages) == 0
    thread.add_user_message("second")
    assert len(thread.messages) == 1
    assert thread.messages[0].text == "second"


def test_voice_pill_lines_70_73_76():
    """Cover voice_pill.py lines 70-73, 76."""
    pill = VoicePill(state="processing")
    assert pill.state == "processing"
    assert pill.is_active


def test_composer_queue_drain():
    """Cover composer.py queue drain paths."""
    sent = []
    composer = AiComposer(on_send=lambda t: sent.append(t))
    composer.set_running(True)
    composer.input.set_value("queued msg")
    composer.submit()
    assert len(composer.queued_tray) == 1
    composer.set_running(False)
    assert sent == ["queued msg"]
    assert len(composer.queued_tray) == 0


def test_tool_call_fail_path():
    """Cover tool_call.py fail path."""
    tc = ToolCall(id="t-1", name="search", status=ToolStatus.EXECUTING)
    card = ToolCallCard(tc)
    card.fail("boom")
    assert tc.status == ToolStatus.FAILED
    assert tc.result == "boom"


def test_task_tray_complete_empty():
    """Cover task_tray.py complete on empty."""
    tray = TaskTray()
    tray.add_task("x").complete()
    assert len(tray) == 0


def test_reasoning_card_append_empty():
    """Cover reasoning.py append_thought with empty text."""
    card = ReasoningCard(thought_text="start", step_count=0)
    card.append_thought("", step_count=1)
    assert card.step_count == 1
