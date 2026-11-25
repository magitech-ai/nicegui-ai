"""Tests for task_tray uncovered branches."""

from nicegui_ai.task_tray import TaskTray


def test_task_tray_complete():
    tray = TaskTray()
    h = tray.add_task("A")
    h.complete()
    assert len(tray) == 0


def test_task_tray_multiple_complete():
    tray = TaskTray()
    h1 = tray.add_task("A")
    h2 = tray.add_task("B")
    h1.complete()
    assert len(tray) == 1
    h2.complete()
    assert len(tray) == 0
