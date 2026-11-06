"""Collapsible Bottom Terminal and Background Tasks Dock for Antigravity & Mvge."""

from collections.abc import Callable
from typing import Any, Literal

from nicegui import ui

from .icons import AntigravityIcon

DockTabType = Literal["shell", "tasks"]


class TerminalDock(ui.element):
    """1:1 Antigravity Bottom Dock hosting an interactive shell and background tasks."""

    def __init__(
        self,
        *,
        is_open: bool = False,
        cwd: str = "",
        terminal_lines: list[dict[str, Any]] | None = None,
        background_tasks: list[dict[str, Any]] | None = None,
        active_tab: DockTabType = "shell",
        on_execute_command: Callable[[str], Any] | None = None,
        on_clear: Callable[[], Any] | None = None,
        on_kill_task: Callable[[str], Any] | None = None,
        on_toggle: Callable[[bool], Any] | None = None,
    ) -> None:
        super().__init__("div")
        self.is_open = is_open
        self.cwd = cwd
        self.terminal_lines: list[dict[str, Any]] = (
            list(terminal_lines) if terminal_lines is not None else []
        )
        self.background_tasks: list[dict[str, Any]] = (
            list(background_tasks) if background_tasks is not None else []
        )
        self.active_tab: DockTabType = active_tab
        self.on_execute_command = on_execute_command
        self.on_clear = on_clear
        self.on_kill_task = on_kill_task
        self.on_toggle = on_toggle

        self.input_text = ""
        self.is_maximized = False

        self.props('data-testid="terminal-dock"')
        self._apply_root_classes()
        self.render()

    def _apply_root_classes(self) -> None:
        self._classes.clear()
        if not self.is_open:
            self.classes("hidden")
            return
        height_cls = "h-[450px]" if self.is_maximized else "h-[260px]"
        self.classes(
            f"w-full {height_cls} bg-[#101010] border-t border-[#222222] "
            f"flex flex-col shrink-0 select-none relative z-30 transition-all"
        )

    def set_open(self, open_state: bool) -> None:
        self.is_open = open_state
        if self.on_toggle:
            self.on_toggle(open_state)
        self._apply_root_classes()
        self.render()

    def set_tab(self, tab: DockTabType) -> None:
        self.active_tab = tab
        self.render()

    def execute_command(self, cmd: str) -> None:
        clean_cmd = cmd.strip()
        if not clean_cmd:
            return
        if self.on_execute_command:
            self.on_execute_command(clean_cmd)
        self.input_text = ""
        self.render()

    def clear_history(self) -> None:
        self.terminal_lines.clear()
        if self.on_clear:
            self.on_clear()
        self.render()

    def kill_task(self, task_id: str) -> None:
        if self.on_kill_task:
            self.on_kill_task(task_id)

    def render(self) -> None:
        self.clear()
        self._apply_root_classes()
        if not self.is_open:
            return

        with self:
            self._render_header()
            if self.active_tab == "shell":
                self._render_shell_tab()
            elif self.active_tab == "tasks":
                self._render_tasks_tab()

    def _render_header(self) -> None:
        with ui.row().classes(
            "h-[36px] px-3 border-b border-[#222222] items-center "
            "justify-between shrink-0 bg-[#151515] w-full"
        ):
            # Left tabs
            with ui.row().classes("items-center gap-1"):
                # Shell Tab
                is_shell = self.active_tab == "shell"
                btn_shell = (
                    ui.button(on_click=lambda: self.set_tab("shell"))
                    .props('flat dense no-caps data-testid="terminal-dock-tab-shell"')
                    .classes(
                        f"px-2.5 py-1 text-[11px] font-medium rounded transition-colors "
                        f"{'text-[#cccccc] bg-[#222222]' if is_shell else 'text-[#6e6e6e] hover:text-[#cccccc]'}"
                    )
                )
                with btn_shell:
                    with ui.row().classes("items-center gap-1.5"):
                        AntigravityIcon("terminal_tab", size=13)
                        ui.label("TERMINAL")

                # Tasks Tab
                is_tasks = self.active_tab == "tasks"
                btn_tasks = (
                    ui.button(on_click=lambda: self.set_tab("tasks"))
                    .props('flat dense no-caps data-testid="terminal-dock-tab-tasks"')
                    .classes(
                        f"px-2.5 py-1 text-[11px] font-medium rounded transition-colors "
                        f"{'text-[#cccccc] bg-[#222222]' if is_tasks else 'text-[#6e6e6e] hover:text-[#cccccc]'}"
                    )
                )
                with btn_tasks:
                    with ui.row().classes("items-center gap-1.5"):
                        AntigravityIcon("overview_tab", size=13)
                        ui.label("BACKGROUND TASKS")
                        if self.background_tasks:
                            ui.badge(
                                str(len(self.background_tasks)), color="amber-7"
                            ).props("floating rounded")

                # Working directory pill
                if self.cwd:
                    with ui.row().classes("items-center gap-1 ml-3 px-2 py-0.5 rounded bg-[#101010] border border-[#222222] text-[#6e6e6e] text-[10px]"):
                        AntigravityIcon("folder", size=11)
                        ui.label(self.cwd).classes("font-mono truncate max-w-[280px]")

            # Right actions
            with ui.row().classes("items-center gap-1"):
                if self.active_tab == "shell":
                    ui.button(
                        icon="delete_outline", on_click=self.clear_history
                    ).props("flat dense round size=sm").classes(
                        "text-[#6e6e6e] hover:text-[#cccccc]"
                    ).tooltip("Clear Terminal")

                # Maximize/Restore
                def _toggle_max() -> None:
                    self.is_maximized = not self.is_maximized
                    self._apply_root_classes()

                ui.button(
                    icon="unfold_more" if not self.is_maximized else "unfold_less",
                    on_click=_toggle_max,
                ).props("flat dense round size=sm").classes(
                    "text-[#6e6e6e] hover:text-[#cccccc]"
                ).tooltip("Expand / Restore Dock")

                # Close
                ui.button(
                    icon="close", on_click=lambda: self.set_open(False)
                ).props("flat dense round size=sm").classes(
                    "text-[#6e6e6e] hover:text-[#cccccc]"
                ).tooltip("Close Dock (Ctrl+`)")

    def _render_shell_tab(self) -> None:
        with ui.column().classes("flex-1 w-full min-h-0 bg-[#101010] p-2 gap-2"):
            # Output scroll area
            with ui.scroll_area().classes("flex-1 w-full font-mono text-[11px] text-[#cccccc] pr-2"):
                if not self.terminal_lines:
                    with ui.column().classes("p-4 items-center justify-center text-[#6e6e6e] gap-1"):
                        AntigravityIcon("terminal_tab", size=24)
                        ui.label("Interactive Workspace Shell").classes("text-[12px] font-medium text-[#cccccc]")
                        ui.label(f"Commands execute directly in {self.cwd or 'workspace root'}").classes("text-[10px]")
                else:
                    for line in self.terminal_lines:
                        with ui.column().classes("mb-2 p-2 rounded bg-[#151515] border border-[#222222] gap-1"):
                            with ui.row().classes("items-center justify-between w-full"):
                                with ui.row().classes("items-center gap-1.5"):
                                    ui.label("$").classes("text-cyan-400 font-bold")
                                    ui.label(line.get("cmd", "")).classes("font-bold text-white")
                                with ui.row().classes("items-center gap-2"):
                                    exit_code = line.get("exit_code")
                                    if line.get("running"):
                                        ui.spinner(size="xs").classes("text-cyan-400")
                                        ui.label("running").classes("text-cyan-400 text-[10px]")
                                    elif exit_code == 0:
                                        ui.badge("0", color="positive").props("dense rounded")
                                    elif exit_code is not None:
                                        ui.badge(str(exit_code), color="negative").props("dense rounded")
                                    if line.get("timestamp"):
                                        ui.label(line["timestamp"]).classes("text-[#6e6e6e] text-[10px]")
                            if line.get("output"):
                                ui.label(line["output"]).classes("whitespace-pre-wrap break-all text-[#aaaaaa] mt-1")

            # Input prompt row
            with ui.row().classes("h-[36px] w-full items-center gap-2 px-2 bg-[#151515] border border-[#222222] rounded shrink-0"):
                ui.label("$").classes("font-mono text-cyan-400 font-bold text-[13px]")
                inp = (
                    ui.input(
                        placeholder="Type a bash/shell command (e.g. uv run pytest)...",
                        value=self.input_text,
                        on_change=lambda e: setattr(self, "input_text", e.value),
                    )
                    .props('dense borderless data-testid="terminal-dock-input"')
                    .classes("flex-1 font-mono text-[12px] text-[#cccccc]")
                )
                inp.on("keydown.enter", lambda: self.execute_command(self.input_text))
                ui.button(
                    "Run", on_click=lambda: self.execute_command(self.input_text)
                ).props('flat dense no-caps color="primary"').classes("text-[11px] px-2")

    def _render_tasks_tab(self) -> None:
        with ui.column().classes("flex-1 w-full min-h-0 bg-[#101010] p-3 gap-2"):
            with ui.scroll_area().classes("flex-1 w-full"):
                if not self.background_tasks:
                    with ui.column().classes("p-6 items-center justify-center text-[#6e6e6e] gap-1"):
                        AntigravityIcon("overview_tab", size=24)
                        ui.label("No Background Tasks Running").classes("text-[12px] font-medium text-[#cccccc]")
                        ui.label("Background processes and long-running daemons will appear here.").classes("text-[10px]")
                else:
                    for task in self.background_tasks:
                        with ui.column().classes("mb-2 p-3 rounded bg-[#151515] border border-[#222222] gap-1.5"):
                            with ui.row().classes("items-center justify-between w-full"):
                                with ui.row().classes("items-center gap-2"):
                                    status = task.get("status", "running")
                                    color = "positive" if status == "completed" else "negative" if status == "failed" else "amber-7"
                                    ui.badge(status.upper(), color=color).props("dense rounded text-[10px]")
                                target_task_id = task.get("id", "")
                                ui.button(
                                    "Kill Task",
                                    icon="close",
                                    on_click=lambda tid=target_task_id: self.kill_task(tid),
                                ).props('flat dense no-caps color="negative"').classes("text-[11px]")
                            if task.get("output"):
                                with ui.expansion("Output Log", icon="notes").classes("w-full text-[#6e6e6e] text-[11px]"):
                                    ui.label(task["output"]).classes("font-mono text-[10px] text-[#aaaaaa] whitespace-pre-wrap")
