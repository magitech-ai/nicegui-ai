"""Hermetic tests for Mvge AuxiliaryPane mode and TerminalDock."""

from typing import Any

from nicegui_ai.antigravity import AuxiliaryPane, ChangedFile, DiffLine
from nicegui_ai.antigravity.terminal_dock import TerminalDock


def test_terminal_dock_init_and_state() -> None:
    executed_cmds: list[str] = []
    cleared: list[bool] = []
    killed: list[str] = []
    toggled: list[bool] = []

    dock = TerminalDock(
        is_open=True,
        cwd="/mnt/storage/projects/mvge",
        terminal_lines=[
            {
                "id": "cmd-1",
                "cmd": "uv run pytest",
                "output": "28 passed",
                "exit_code": 0,
                "running": False,
                "timestamp": "12:00:00",
                "cwd": "/mnt/storage/projects/mvge",
            }
        ],
        background_tasks=[
            {
                "id": "task-bg-1",
                "command": "python -m http.server 8080",
                "status": "running",
                "output": "Serving HTTP on 0.0.0.0 port 8080",
            }
        ],
        on_execute_command=lambda cmd: executed_cmds.append(cmd),
        on_clear=lambda: cleared.append(True),
        on_kill_task=lambda tid: killed.append(tid),
        on_toggle=lambda state: toggled.append(state),
    )

    assert dock.is_open is True
    assert dock.cwd == "/mnt/storage/projects/mvge"
    assert len(dock.terminal_lines) == 1
    assert len(dock.background_tasks) == 1
    assert dock.active_tab == "shell"

    dock.set_tab("tasks")
    assert dock.active_tab == "tasks"

    dock.execute_command("git status")
    assert executed_cmds == ["git status"]

    dock.clear_history()
    assert cleared == [True]
    assert len(dock.terminal_lines) == 0

    dock.kill_task("task-bg-1")
    assert killed == ["task-bg-1"]

    dock.set_open(False)
    assert dock.is_open is False
    assert toggled == [False]


def test_auxiliary_pane_mvge_mode_tabs_and_badges() -> None:
    diffs = [
        ChangedFile(
            name="file1.py",
            path="src/file1.py",
            additions=10,
            deletions=2,
            status="modified",
            lines=[DiffLine(type="add", text="+x = 1")],
        ),
        ChangedFile(
            name="file2.py",
            path="src/file2.py",
            additions=5,
            deletions=0,
            status="added",
            lines=[DiffLine(type="add", text="+y = 2")],
        ),
    ]

    checkpoints = [
        {
            "leaf_id": "leaf-001",
            "tree_sha": "abc1234",
            "label": "Turn 1: Setup",
            "timestamp": "2m ago",
            "is_current": True,
        }
    ]

    submvges = [
        {
            "sub_mvge_id": "sub-1",
            "role": "research",
            "agent_name": "coding_mvge",
            "model_id": "opencode/big-pickle",
            "child_tome_id": "tome-child-1",
            "tome_path": "/tmp/tome1.jsonl",
            "status": "running",
            "state_detail": "searching",
            "summary": "Investigating API",
            "error": "",
            "mana_used": 150,
            "effective_spells": ["read", "grep"],
            "workspace": "inherit",
            "messages": [],
        }
    ]

    actions: list[tuple[str, dict[str, Any]]] = []

    def handle_aux_action(action: str, payload: dict[str, Any]) -> None:
        actions.append((action, payload))

    pane = AuxiliaryPane(
        is_open=True,
        mvge_mode=True,
        changed_files=diffs,
        checkpoints=checkpoints,
        live_submvges=submvges,
        on_aux_action=handle_aux_action,
    )

    assert pane.mvge_mode is True
    assert pane.active_tab == "review"
    assert len(pane.submitted_comments) == 0  # No fake Van Luther comment
    assert len(pane.changed_files) == 2

    # Switch to subagents tab
    pane.set_tab("agents")
    assert pane.active_tab == "agents"
    assert len(pane.live_submvges) == 1

    pane._handle_message_submvge("sub-1", "Focus on spells")
    assert actions[-1] == (
        "message_submvge",
        {"sub_mvge_id": "sub-1", "message": "Focus on spells"},
    )

    pane._handle_kill_submvge("sub-1")
    assert actions[-1] == ("kill_submvge", {"sub_mvge_id": "sub-1"})

    # Checkpoint time travel
    pane.set_tab("review")
    pane._handle_select_checkpoint("leaf-001")
    assert actions[-1] == ("select_checkpoint_leaf", {"leaf_id": "leaf-001"})

    pane._handle_restore_file("src/file1.py")
    assert actions[-1] == (
        "restore_checkpoint_file",
        {"path": "src/file1.py", "leaf_id": pane.selected_checkpoint_leaf},
    )
