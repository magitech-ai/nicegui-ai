"""Tests for task_tray module."""

from nicegui_ai.task_tray import TaskTray


def test_task_tray_init():
    tray = TaskTray()
    assert len(tray) == 0
    assert not tray.visible


def test_task_tray_add_and_complete():
    tray = TaskTray()
    h = tray.add_task("Indexing...")
    assert len(tray) == 1
    assert tray.visible

    h.complete()
    assert len(tray) == 0
    assert not tray.visible


def test_task_tray_set_text():
    tray = TaskTray()
    h = tray.add_task("Task")
    h.set_text("Updated task")
    assert h.text == "Updated task"
