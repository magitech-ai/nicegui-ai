"""Tests for thread, tool_call, voice_pill, task_tray, composer, reasoning modules."""

from nicegui_ai.thread import AiThread
from nicegui_ai.tool_call import ToolCall, ToolCallCard, ToolStatus
from nicegui_ai.voice_pill import VoicePill
from nicegui_ai.task_tray import TaskTray
from nicegui_ai.composer import AiComposer
from nicegui_ai.reasoning import ReasoningCard
from nicegui_ai.message import UserMessage, AgentMessage


def test_thread_all_paths():
    thread = AiThread()
    assert len(thread.messages) == 0

    user = thread.add_user_message("hello")
    assert user.text == "hello"
    assert len(thread.messages) == 1

    agent = thread.add_agent_message(agent_name="A", text="hi")
    assert agent.agent_name == "A"
    assert agent.text == "hi"
    assert len(thread.messages) == 2

    thread.clear()
    assert len(thread.messages) == 0

    # Add after clear
    thread.add_user_message("again")
    assert len(thread.messages) == 1


def test_tool_call_all():
    tc = ToolCall(id="t-1", name="search", status=ToolStatus.EXECUTING)
    assert tc.id == "t-1"
    assert tc.name == "search"
    assert tc.status == ToolStatus.EXECUTING

    card = ToolCallCard(tc)
    card.set_status(ToolStatus.RESOLVED)
    card.set_result("found")
    assert tc.status == ToolStatus.RESOLVED
    assert tc.result == "found"

    card.fail("timeout")
    assert tc.status == ToolStatus.FAILED
    assert tc.result == "timeout"


def test_voice_pill_all_states():
    pill = VoicePill()
    assert pill.state == "idle"
    assert not pill.is_active

    pill.set_state("listening")
    assert pill.state == "listening"
    assert pill.is_active

    pill.set_state("speaking")
    assert pill.state == "speaking"
    assert pill.is_active

    pill.set_state("idle")
    assert pill.state == "idle"
    assert not pill.is_active


def test_task_tray_all():
    tray = TaskTray()
    assert len(tray) == 0
    assert not tray.visible

    h = tray.add_task("Indexing...")
    assert len(tray) == 1
    assert tray.visible

    h.set_text("Updated")
    assert h.text == "Updated"

    h.complete()
    assert len(tray) == 0
    assert not tray.visible


def test_composer_all():
    sent = []
    composer = AiComposer(on_send=lambda t: sent.append(t), on_cancel=lambda: None)
    assert not composer.is_running

    composer.input.set_value("hello")
    composer._update_action_button()
    composer.submit()
    assert sent == ["hello"]

    composer.set_running(True)
    assert composer.is_running
    composer.input.set_value("queued")
    composer._update_action_button()
    composer.submit()
    assert len(composer.queued_tray) == 1

    composer.set_running(False)
    assert sent == ["hello", "queued"]


def test_reasoning_card_all():
    card = ReasoningCard()
    assert card.step_count == 1
    assert not card.is_open

    card.toggle()
    assert card.is_open
    card.toggle()
    assert not card.is_open

    card.append_thought("more", step_count=2)
    assert card.step_count == 2
    assert "more" in card.thought_text
