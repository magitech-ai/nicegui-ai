"""Tests for thread module."""

from nicegui_ai.thread import AiThread


def test_thread_init():
    thread = AiThread()
    assert thread is not None


def test_thread_add_message():
    thread = AiThread()
    msg = thread.add_user_message("Hello")
    assert msg.text == "Hello"
    assert len(thread.messages) == 1


def test_thread_clear():
    thread = AiThread()
    thread.add_user_message("Hello")
    assert len(thread.messages) == 1
    thread.clear()
    assert len(thread.messages) == 0
