"""Command Fastpicker menu and popup overlay for slash commands and quick actions."""

from collections.abc import Callable
from typing import Any

from nicegui import ui

from .state import MthCommandItem

DEFAULT_COMMANDS: list[MthCommandItem] = [
    MthCommandItem(
        token="/plan",
        name="Plan Mode",
        description="Switch to Planning mode before taking action",
        category="Workflows",
        badge="Ctrl+P",
    ),
    MthCommandItem(
        token="/goal",
        name="Goal Mode",
        description="Autonomous long-running execution until objective is met",
        category="Workflows",
        badge="Goal",
    ),
    MthCommandItem(
        token="/compact",
        name="Compact",
        description="Fold historical turns into a context checkpoint",
        category="Context",
        badge="Fold",
    ),
    MthCommandItem(
        token="/permission",
        name="Permission Preset",
        description="Configure execution authorization preset",
        category="Settings",
        badge="Preset",
    ),
    MthCommandItem(
        token="/clear",
        name="Clear Conversation",
        description="Clear conversation history from current session",
        category="Session",
        badge="Reset",
    ),
    MthCommandItem(
        token="/export",
        name="Export Log",
        description="Export full session event trace to JSON",
        category="Session",
        badge="JSON",
    ),
    MthCommandItem(
        token="/help",
        name="Help & Shortcuts",
        description="Display harness documentation and shortcuts",
        category="General",
        badge="Info",
    ),
]


class MthCommandFastpicker(ui.dialog):
    """Command fastpicker dialog and popup overlay matching reference PopupSelectView."""

    def __init__(
        self,
        commands: list[MthCommandItem] | None = None,
        on_select: Callable[[MthCommandItem], Any] | None = None,
    ) -> None:
        super().__init__()
        self.commands = commands or DEFAULT_COMMANDS
        self.on_select = on_select
        self.filter_text = ""
        self.active_index = 0
        self._build_ui()

    def _build_ui(self) -> None:
        with (
            self,
            ui.card().classes(
                "w-[420px] max-h-[460px] bg-[#141722] border border-[#262c3d] p-3 rounded-2xl shadow-2xl flex flex-col gap-2.5 text-slate-100"
            ),
        ):
            # 1. Search Header with autofocus
            with ui.row().classes(
                "w-full items-center gap-2 px-1 pb-1 border-b border-[#232736]"
            ):
                ui.icon("search", size="16px").classes("text-slate-400")
                self.search_input = (
                    ui.input(placeholder="Type a command or search...")
                    .props("dense borderless autofocus")
                    .classes(
                        "flex-grow text-sm text-white placeholder:text-slate-500 font-sans"
                    )
                )
                self.search_input.on("input", self._on_search_change)
                self.search_input.on("keydown.enter", self._on_enter)
                self.search_input.on("keydown.escape", self.close)

                ui.button(
                    icon="close",
                    on_click=self.close,
                ).props("dense flat round size=xs").classes(
                    "text-slate-400 hover:text-white"
                )

            # 2. Options list container
            self.list_container = ui.column().classes(
                "w-full gap-1 overflow-y-auto max-h-[360px] pr-1"
            )
            self._render_options()

    def _get_filtered_commands(self) -> list[MthCommandItem]:
        query = self.filter_text.strip().lower()
        if not query:
            return self.commands
        if query.startswith("/"):
            clean_q = query.lstrip("/")
            return [
                cmd
                for cmd in self.commands
                if cmd.token.lstrip("/").lower().startswith(clean_q)
            ]
        return [
            cmd
            for cmd in self.commands
            if query in cmd.token.lower()
            or query in cmd.name.lower()
            or query in cmd.description.lower()
        ]

    def _render_options(self) -> None:
        self.list_container.clear()
        filtered = self._get_filtered_commands()

        if not filtered:
            with self.list_container:
                with ui.column().classes(
                    "w-full items-center justify-center py-6 gap-1"
                ):
                    ui.icon("search_off", size="24px").classes("text-slate-600")
                    ui.label("No matching commands found").classes(
                        "text-xs text-slate-400"
                    )
            return

        # Group by category
        categories: dict[str, list[MthCommandItem]] = {}
        for cmd in filtered:
            categories.setdefault(cmd.category, []).append(cmd)

        with self.list_container:
            for cat, cmds in categories.items():
                ui.label(cat.upper()).classes(
                    "text-[10px] font-mono font-semibold text-slate-500 tracking-wider px-2 pt-1"
                )
                for cmd in cmds:
                    with (
                        ui.row()
                        .classes(
                            "w-full items-center justify-between px-2.5 py-1.5 rounded-lg cursor-pointer hover:bg-[#1f2535] transition-colors group"
                        )
                        .on("click", lambda _, c=cmd: self._select_command(c))
                    ):
                        with ui.row().classes("items-center gap-2"):
                            ui.label(cmd.token).classes(
                                "font-mono font-semibold text-xs text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded border border-blue-500/20"
                            )
                            with ui.column().classes("gap-0"):
                                ui.label(cmd.name).classes(
                                    "text-xs font-medium text-slate-200 group-hover:text-white"
                                )
                                ui.label(cmd.description).classes(
                                    "text-[11px] text-slate-400 group-hover:text-slate-300"
                                )
                        if cmd.badge:
                            ui.label(cmd.badge).classes(
                                "text-[10px] font-mono text-slate-400 bg-[#1b202c] px-1.5 py-0.5 rounded border border-[#2b3244]"
                            )

    def _on_search_change(self, e: Any) -> None:
        self.filter_text = self.search_input.value or ""
        self._render_options()

    def _on_enter(self, e: Any) -> None:
        filtered = self._get_filtered_commands()
        if filtered:
            self._select_command(filtered[0])

    def _select_command(self, cmd: MthCommandItem) -> None:
        self.close()
        if self.on_select:
            self.on_select(cmd)
