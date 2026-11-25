"""Right Inspector Drawer supporting Document/Diff Preview, Workspace Files, and Terminal."""

import difflib
from collections.abc import Callable
from pathlib import Path
from typing import Any

from nicegui import core, ui

from .state import MthDiffItem


class MthDiffPreview(ui.column):
    """Unified file diff and document code viewer."""

    def __init__(self, diff_item: MthDiffItem | None = None) -> None:
        super().__init__()
        self.diff_item = diff_item
        self.classes("w-full flex-grow p-3 overflow-y-auto")
        self._build_ui()

    def _build_ui(self) -> None:
        self.clear()
        with self:
            if not self.diff_item:
                with ui.column().classes(
                    "w-full h-full items-center justify-center text-slate-500 gap-2 my-auto"
                ):
                    ui.icon("difference", size="36px").classes("text-slate-600")
                    ui.label("No file selected or modified yet.").classes(
                        "text-xs font-mono"
                    )
                return

            # Header with path and line deltas
            with ui.row().classes(
                "w-full items-center justify-between bg-[#161922] p-2 rounded-lg border border-[#232736] mb-3"
            ):
                with ui.row().classes("items-center gap-2 overflow-hidden"):
                    ui.icon("description", size="16px").classes(
                        "text-blue-400 shrink-0"
                    )
                    ui.label(self.diff_item.file_path).classes(
                        "font-mono text-xs text-slate-200 truncate"
                    )

                with ui.row().classes("items-center gap-1.5 shrink-0"):
                    if self.diff_item.added_lines > 0:
                        ui.badge(
                            f"+{self.diff_item.added_lines}", color="emerald-9"
                        ).classes("font-mono text-[10px]")
                    if self.diff_item.removed_lines > 0:
                        ui.badge(
                            f"-{self.diff_item.removed_lines}", color="rose-9"
                        ).classes("font-mono text-[10px]")
                    ui.button(
                        icon="content_copy",
                        on_click=self._copy_diff,
                    ).props("dense flat round size=xs").classes(
                        "text-slate-400 hover:text-white ml-1"
                    ).tooltip("Copy diff")

    def _copy_diff(self) -> None:
        """Copy diff text to clipboard."""
        if self.diff_item and self.diff_item.diff_text:
            try:
                if getattr(core, "loop", None) is not None:
                    ui.run_javascript(
                        f"navigator.clipboard.writeText({repr(self.diff_item.diff_text)})"
                    )
                    ui.notify(
                        "Diff copied to clipboard",
                        type="positive",
                        position="top",
                        timeout=1200,
                    )
            except Exception:
                pass

            # Unified Diff Lines Container
            lines = self.diff_item.diff_text.splitlines()
            with ui.column().classes(
                "w-full font-mono text-xs bg-[#0b0d13] p-2 rounded-lg border border-[#1e2230] overflow-x-auto gap-0.5"
            ):
                for line in lines:
                    if line.startswith("+"):
                        bg_cls = "bg-emerald-950/50 text-emerald-300"
                    elif line.startswith("-"):
                        bg_cls = "bg-rose-950/50 text-rose-300"
                    elif line.startswith("@"):
                        bg_cls = "text-blue-400 font-semibold"
                    else:
                        bg_cls = "text-slate-300"
                    ui.label(line).classes(
                        f"w-full px-2 py-0.5 whitespace-pre {bg_cls}"
                    )

    def update_diff(self, diff_item: MthDiffItem) -> None:
        """Update displayed diff item and refresh view."""
        self.diff_item = diff_item
        self._build_ui()


class MthFileTree(ui.column):
    """Workspace filesystem explorer tree."""

    def __init__(
        self,
        workspace_root: str = ".",
        on_file_select: Callable[[str], Any] | None = None,
    ) -> None:
        super().__init__()
        self.workspace_root = workspace_root
        self.on_file_select = on_file_select
        self.classes("w-full flex-grow p-3 overflow-y-auto")
        self._build_ui()

    def _build_ui(self) -> None:
        self.clear()
        with self:
            with ui.row().classes(
                "w-full items-center justify-between pb-2 mb-2 border-b border-[#232736]"
            ):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("folder_open", size="16px").classes("text-amber-400")
                    ui.label(Path(self.workspace_root).resolve().name).classes(
                        "font-mono text-xs text-slate-300 font-semibold"
                    )
                ui.button(icon="refresh", on_click=self._build_ui).props(
                    "dense flat round size=xs"
                ).classes("text-slate-400")

            root_path = Path(self.workspace_root)
            if not root_path.exists():
                ui.label(f"Path does not exist: {self.workspace_root}").classes(
                    "text-xs text-rose-400 font-mono"
                )
                return

            self._render_directory(root_path, depth=0)

    def _render_directory(self, dir_path: Path, depth: int) -> None:
        if depth > 4:
            return
        try:
            entries = sorted(
                dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())
            )
        except PermissionError:
            return

        for entry in entries:
            # Skip hidden and cache folders
            if entry.name.startswith(".") or entry.name in {
                "__pycache__",
                "node_modules",
                "dist",
                "build",
                ".venv",
            }:
                continue

            indent = f"ml-{depth * 3}" if depth > 0 else ""
            if entry.is_dir():
                with ui.expansion(entry.name, icon="folder").classes(
                    f"w-full text-xs text-slate-300 {indent} py-0"
                ):
                    self._render_directory(entry, depth + 1)
            else:
                with (
                    ui.row()
                    .classes(
                        f"w-full items-center gap-2 py-1 px-2 rounded hover:bg-[#161922] cursor-pointer text-xs {indent}"
                    )
                    .on("click", lambda _, path=str(entry): self._handle_click(path))
                ):
                    ui.icon("description", size="14px").classes("text-slate-400")
                    ui.label(entry.name).classes(
                        "font-mono text-slate-300 truncate flex-grow"
                    )

    def _handle_click(self, file_path: str) -> None:
        if self.on_file_select:
            self.on_file_select(file_path)


class MthTerminalDock(ui.column):
    """Persistent Terminal panel displaying command history and live interactive output."""

    def __init__(self, on_run_command: Callable[[str], Any] | None = None) -> None:
        super().__init__()
        self.on_run_command = on_run_command
        self.history: list[tuple[str, str, int]] = []  # (cmd, output, exit_code)
        self.classes(
            "w-full flex-grow p-3 flex flex-col justify-between overflow-hidden bg-[#090a0f]"
        )
        self._build_ui()

    def _build_ui(self) -> None:
        self.clear()
        with self:
            # Command log scroll area
            self.log_area = ui.scroll_area().classes(
                "w-full flex-grow font-mono text-xs gap-2 p-2 bg-[#0d0f15] rounded-lg border border-[#1e2230]"
            )
            with self.log_area:
                self.log_container = ui.column().classes("w-full gap-2")

            # Input dock
            with ui.row().classes(
                "w-full items-center gap-2 pt-2 border-t border-[#232736]"
            ):
                ui.label("$").classes("font-mono text-sm text-blue-400 font-bold")
                self.cmd_input = (
                    ui.input(placeholder="Run command...")
                    .props("dense borderless")
                    .classes("flex-grow font-mono text-xs text-slate-200")
                    .on("keydown.enter", self._handle_run)
                )
                ui.button(icon="send", on_click=self._handle_run).props(
                    "dense flat round size=sm"
                ).classes("text-blue-400").tooltip("Run command (Enter)")
                ui.button(icon="delete_sweep", on_click=self.clear_history).props(
                    "dense flat round size=sm"
                ).classes("text-slate-500 hover:text-rose-400").tooltip(
                    "Clear terminal"
                )

            self._refresh_history()

    def _refresh_history(self) -> None:
        self.log_container.clear()
        with self.log_container:
            for cmd, out, code in self.history:
                with ui.column().classes("w-full border-b border-[#1c202e] pb-1"):
                    with ui.row().classes("items-center justify-between w-full"):
                        ui.label(f"$ {cmd}").classes("text-blue-300 font-semibold")
                        badge_color = "emerald-9" if code == 0 else "rose-9"
                        ui.badge(f"exit {code}", color=badge_color).classes(
                            "text-[10px]"
                        )
                    if out:
                        ui.label(out).classes("text-slate-400 whitespace-pre-wrap pl-2")
        self.log_area.scroll_to(percent=1.0)

    def append_output(self, cmd: str, output: str, exit_code: int = 0) -> None:
        """Append executed command and its output to terminal history."""
        self.history.append((cmd, output, exit_code))
        self._refresh_history()

    def clear_history(self) -> None:
        """Clear all logged terminal commands and outputs."""
        self.history.clear()
        self._refresh_history()

    def _handle_run(self) -> None:
        cmd = (self.cmd_input.value or "").strip()
        if not cmd:
            return
        self.cmd_input.set_value("")
        if self.on_run_command:
            self.on_run_command(cmd)


class MthInspectorDrawer(ui.element):
    """The 3-tab Right Inspector Track (Diff / File Explorer / Terminal)."""

    def __init__(
        self,
        workspace_root: str = ".",
        active_diff: MthDiffItem | None = None,
        on_close: Callable[[], Any] | None = None,
        on_file_select: Callable[[str], Any] | None = None,
        on_run_command: Callable[[str], Any] | None = None,
    ) -> None:
        super().__init__("aside")
        self.workspace_root = workspace_root
        self.active_diff = active_diff
        self.on_close = on_close
        self.on_file_select = on_file_select
        self.on_run_command = on_run_command
        self.active_tab = "diff"
        self.is_fullscreen = False

        self.classes(
            "w-96 h-full bg-[#0d0f15] border-l border-[#232736] flex flex-col justify-between shrink-0 overflow-hidden"
        )
        self._build_ui()

    def _build_ui(self) -> None:
        with self:
            # 1. Header with Tab Strip & Close Button
            with ui.row().classes(
                "w-full h-11 items-center justify-between px-3 bg-[#11131a] border-b border-[#232736] shrink-0"
            ):
                with ui.row().classes("items-center gap-1"):
                    self.diff_btn = (
                        ui.button(
                            "Diff",
                            icon="difference",
                            on_click=lambda: self.set_tab("diff"),
                        )
                        .props("dense flat no-caps size=sm")
                        .classes(
                            "font-mono text-xs text-blue-400 bg-[#1c202e] rounded px-2"
                        )
                    )
                    self.files_btn = (
                        ui.button(
                            "Files",
                            icon="folder",
                            on_click=lambda: self.set_tab("files"),
                        )
                        .props("dense flat no-caps size=sm")
                        .classes(
                            "font-mono text-xs text-slate-400 rounded px-2 hover:bg-[#161922]"
                        )
                    )
                    self.term_btn = (
                        ui.button(
                            "Terminal",
                            icon="terminal",
                            on_click=lambda: self.set_tab("terminal"),
                        )
                        .props("dense flat no-caps size=sm")
                        .classes(
                            "font-mono text-xs text-slate-400 rounded px-2 hover:bg-[#161922]"
                        )
                    )

                with ui.row().classes("items-center gap-1"):
                    self.expand_btn = (
                        ui.button(icon="fullscreen", on_click=self.toggle_fullscreen)
                        .props("dense flat round size=sm")
                        .classes("text-slate-400 hover:text-white")
                    )
                    with self.expand_btn:
                        ui.tooltip("Toggle fullscreen inspector").classes("text-xs")

                    ui.button(icon="close", on_click=self._handle_close).props(
                        "dense flat round size=sm"
                    ).classes("text-slate-400 hover:text-white")

            # 2. Body Container for Tabs
            self.body_container = ui.column().classes(
                "w-full flex-grow overflow-hidden"
            )
            with self.body_container:
                self.diff_view = MthDiffPreview(diff_item=self.active_diff)
                self.file_tree = MthFileTree(
                    workspace_root=self.workspace_root,
                    on_file_select=self._handle_file_select,
                )
                self.terminal = MthTerminalDock(on_run_command=self.on_run_command)

            self._update_tab_visibility()

    def set_tab(self, tab: str) -> None:
        """Switch active inspector tab ('diff', 'files', 'terminal')."""
        self.active_tab = tab
        self._update_tab_visibility()

    def toggle_fullscreen(self) -> bool:
        """Toggle inspector between standard docked width and fullscreen overlay."""
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.classes(remove="w-96", add="w-full absolute inset-0 z-30")
            self.expand_btn.props("icon=fullscreen_exit")
        else:
            self.classes(remove="w-full absolute inset-0 z-30", add="w-96")
            self.expand_btn.props("icon=fullscreen")
        return self.is_fullscreen

    def _update_tab_visibility(self) -> None:
        self.diff_view.set_visibility(self.active_tab == "diff")
        self.file_tree.set_visibility(self.active_tab == "files")
        self.terminal.set_visibility(self.active_tab == "terminal")

        # Update tab button styles
        active_cls = "text-blue-400 bg-[#1c202e]"
        inactive_cls = "text-slate-400 bg-transparent"

        self.diff_btn.classes(
            replace=active_cls if self.active_tab == "diff" else inactive_cls
        )
        self.files_btn.classes(
            replace=active_cls if self.active_tab == "files" else inactive_cls
        )
        self.term_btn.classes(
            replace=active_cls if self.active_tab == "terminal" else inactive_cls
        )

    def show_diff(self, diff_item: MthDiffItem) -> None:
        """Display diff and switch to diff tab."""
        self.active_diff = diff_item
        self.diff_view.update_diff(diff_item)
        self.set_tab("diff")

    def show_file(self, file_path: str) -> None:
        """Read a file and show it in the diff preview."""
        p = Path(file_path)
        if p.exists() and p.is_file():
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                diff = MthDiffItem(
                    file_path=file_path,
                    new_content=content,
                    diff_text=content,
                )
                self.show_diff(diff)
            except Exception as e:
                diff = MthDiffItem(
                    file_path=file_path, diff_text=f"Error reading file: {e}"
                )
                self.show_diff(diff)

    def _handle_file_select(self, file_path: str) -> None:
        self.show_file(file_path)
        if self.on_file_select:
            self.on_file_select(file_path)

    def _handle_close(self) -> None:
        if self.on_close:
            self.on_close()


def generate_unified_diff(file_path: str, old_text: str, new_text: str) -> MthDiffItem:
    """Helper to generate a unified diff and MthDiffItem from two text states."""
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)
    diff_lines = list(
        difflib.unified_diff(old_lines, new_lines, fromfile=file_path, tofile=file_path)
    )

    added = sum(
        1 for line in diff_lines if line.startswith("+") and not line.startswith("+++")
    )
    removed = sum(
        1 for line in diff_lines if line.startswith("-") and not line.startswith("---")
    )
    diff_text = "".join(diff_lines)

    return MthDiffItem(
        file_path=file_path,
        old_content=old_text,
        new_content=new_text,
        diff_text=diff_text,
        added_lines=added,
        removed_lines=removed,
    )
