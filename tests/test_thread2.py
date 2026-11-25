"""Tests for thread uncovered branches."""

from nicegui_ai.thread import AiThread


def test_thread_add_agent_message():
    thread = AiThread()
    msg = thread.add_agent_message(agent_name="Agent", text="Hi")
    assert msg.agent_name == "Agent"
    assert msg.text == "Hi"
    assert len(thread.messages) == 1


def test_thread_clear_all():
    thread = AiThread()
    thread.add_user_message("Hello")
    assert len(thread.messages) == 1
    thread.clear()
    assert len(thread.messages) == 0
