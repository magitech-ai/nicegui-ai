"""Persistent, fully featured Left Sidebar component matching reference visual and functional design."""

from collections.abc import Callable
from typing import Any

from nicegui import ui

from .state import MthSession, format_relative_time


class MthSessionRow(ui.row):
    """Single interactive session item row with status dot, relative time, pin, and context actions."""

    def __init__(
        self,
        session: MthSession,
        is_active: bool,
        on_select: Callable[[str], Any],
        on_pin: Callable[[str], Any] | None = None,
        on_rename: Callable[[str, str], Any] | None = None,
        on_fork: Callable[[str], Any] | None = None,
        on_archive: Callable[[str], Any] | None = None,
        on_delete: Callable[[str], Any] | None = None,
    ) -> None:
        super().__init__()
        self.session = session
        self.is_active = is_active
        self.on_select = on_select
        self.on_pin = on_pin
        self.on_rename = on_rename
        self.on_fork = on_fork
        self.on_archive = on_archive
        self.on_delete = on_delete

        active_cls = (
            "bg-[#1c202e] text-white border border-[#2c3345]"
            if is_active
            else "text-slate-400 hover:bg-[#141721] hover:text-slate-200 border border-transparent"
        )
        self.classes(
            f"group w-full items-center justify-between px-2.5 py-1.5 rounded-lg cursor-pointer text-xs font-sans {active_cls} transition-all duration-100"
        )
        self._build_ui()

    def _build_ui(self) -> None:
        with self:
            # 1. Left Cluster: State Dot / Pin icon + Title
            with (
                ui.row()
                .classes("items-center gap-2 overflow-hidden flex-grow min-w-0")
                .on("click", lambda _: self.on_select(self.session.id))
            ):
                if self.session.pinned:
                    ui.icon("push_pin", size="12px").classes("text-amber-400 shrink-0")
                elif self.session.status == "running":
                    ui.element("div").classes(
                        "w-2 h-2 rounded-full bg-blue-500 animate-pulse shrink-0"
                    )
                else:
                    dot_cls = (
                        "bg-blue-400"
                        if self.is_active
                        else "bg-slate-600 group-hover:bg-slate-400"
                    )
                    ui.element("div").classes(
                        f"w-1.5 h-1.5 rounded-full {dot_cls} shrink-0"
                    )

                title_lbl = ui.label(self.session.title).classes(
                    "truncate font-medium flex-grow"
                )
                with title_lbl:
                    ui.tooltip(self.session.title).classes("text-xs")

            # 2. Right Cluster: Relative Time / Tokens + Hover Actions
            with ui.row().classes("items-center gap-1 shrink-0"):
                # Resting info: relative time or token count
                with ui.row().classes(
                    "items-center gap-1 group-hover:hidden text-[10px] text-slate-500 font-mono"
                ):
                    if self.session.tokens_used > 0:
                        ui.label(f"{self.session.tokens_used:,} tok")
                    rel_time = format_relative_time(self.session.updated_at)
                    ui.label(rel_time)

                # Hover action buttons: Pin quick toggle + Context Menu
                with ui.row().classes("items-center gap-0.5 hidden group-hover:flex"):
                    # Pin toggle
                    pin_icon = "push_pin" if not self.session.pinned else "remove"
                    ui.button(
                        icon=pin_icon,
                        on_click=lambda _: self._handle_pin(),
                    ).props("dense flat round size=xs").classes(
                        "text-slate-400 hover:text-amber-400"
                    )

                    # Context Menu button
                    with (
                        ui.button(icon="more_horiz")
                        .props("dense flat round size=xs")
                        .classes("text-slate-400 hover:text-white")
                    ):
                        with ui.menu().classes(
                            "bg-[#11131a] border border-[#232736] text-xs text-slate-300 p-1 rounded-lg shadow-xl"
                        ):
                            # Pin / Unpin
                            ui.menu_item(
                                "Unpin" if self.session.pinned else "Pin",
                                on_click=self._handle_pin,
                            ).classes("hover:bg-[#1c202e] text-xs py-1 px-3")

                            # Rename
                            ui.menu_item(
                                "Rename",
                                on_click=self._show_rename_dialog,
                            ).classes("hover:bg-[#1c202e] text-xs py-1 px-3")

                            # Fork
                            ui.menu_item(
                                "Fork Branch",
                                on_click=self._handle_fork,
                            ).classes("hover:bg-[#1c202e] text-xs py-1 px-3")

                            # Archive / Unarchive
                            ui.menu_item(
                                "Unarchive" if self.session.archived else "Archive",
                                on_click=self._handle_archive,
                            ).classes("hover:bg-[#1c202e] text-xs py-1 px-3")

                            ui.separator().classes("bg-[#232736] my-1")

                            # Delete
                            ui.menu_item(
                                "Delete",
                                on_click=self._show_delete_dialog,
                            ).classes(
                                "hover:bg-rose-950/60 text-rose-400 text-xs py-1 px-3"
                            )

    def _handle_pin(self) -> None:
        if self.on_pin:
            self.on_pin(self.session.id)

    def _handle_fork(self) -> None:
        if self.on_fork:
            self.on_fork(self.session.id)

    def _handle_archive(self) -> None:
        if self.on_archive:
            self.on_archive(self.session.id)

    def _show_rename_dialog(self) -> None:
        with (
            ui.dialog() as dialog,
            ui.card().classes(
                "bg-[#11131a] border border-[#232736] text-slate-200 p-4 min-w-[320px] rounded-xl"
            ),
        ):
            ui.label("Rename Session").classes("font-semibold text-sm text-white mb-2")
            inp = (
                ui.input(value=self.session.title)
                .props("dense autofocus")
                .classes("w-full text-xs font-mono text-white mb-3")
            )

            def _submit() -> None:
                new_title = (inp.value or "").strip()
                if new_title and self.on_rename:
                    self.on_rename(self.session.id, new_title)
                dialog.close()

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=dialog.close).props(
                    "dense flat no-caps size=sm"
                ).classes("text-slate-400")
                ui.button("Save", on_click=_submit).props(
                    "dense unelevated color=primary no-caps size=sm"
                )
        dialog.open()

    def _show_delete_dialog(self) -> None:
        with (
            ui.dialog() as dialog,
            ui.card().classes(
                "bg-[#11131a] border border-[#232736] text-slate-200 p-4 min-w-[300px] rounded-xl"
            ),
        ):
            ui.label("Delete Session").classes("font-semibold text-sm text-white mb-1")
            ui.label(
                f"Permanently delete '{self.session.title}'? This action cannot be undone."
            ).classes("text-xs text-slate-400 mb-3")

            def _confirm() -> None:
                if self.on_delete:
                    self.on_delete(self.session.id)
                dialog.close()

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=dialog.close).props(
                    "dense flat no-caps size=sm"
                ).classes("text-slate-400")
                ui.button("Delete", on_click=_confirm).props(
                    "dense unelevated color=negative no-caps size=sm"
                )
        dialog.open()


class MthSessionDrawer(ui.element):
    """The 1:1 Left Sidebar Shell & Session Browser for Magitech Harness."""

    def __init__(
        self,
        sessions: list[MthSession],
        active_session_id: str | None = None,
        collapsed: bool = False,
        active_workspace: str = "default",
        on_select_session: Callable[[str], Any] | None = None,
        on_new_session: Callable[[str], Any] | None = None,
        on_pin_session: Callable[[str], Any] | None = None,
        on_rename_session: Callable[[str, str], Any] | None = None,
        on_fork_session: Callable[[str], Any] | None = None,
        on_archive_session: Callable[[str], Any] | None = None,
        on_delete_session: Callable[[str], Any] | None = None,
        on_toggle_collapsed: Callable[[bool], Any] | None = None,
        on_open_settings: Callable[[], Any] | None = None,
    ) -> None:
        super().__init__("aside")
        self.sessions = sessions
        self.active_session_id = active_session_id
        self.collapsed = collapsed
        self.active_workspace = active_workspace
        self.on_select_session = on_select_session
        self.on_new_session = on_new_session
        self.on_pin_session = on_pin_session
        self.on_rename_session = on_rename_session
        self.on_fork_session = on_fork_session
        self.on_archive_session = on_archive_session
        self.on_delete_session = on_delete_session
        self.on_toggle_collapsed = on_toggle_collapsed
        self.on_open_settings = on_open_settings

        # View and filter state
        self.search_filter = ""
        self.group_by: str = "workspace"  # "workspace", "flat"
        self.order_by: str = "updated"  # "updated", "manual"
        self.filter_archived: str = "hide"  # "hide", "show", "only"
        self.show_search_input: bool = False
        self.collapsed_folders: set[str] = set()

        self._update_classes()
        self._build_ui()

    def _update_classes(self) -> None:
        width_cls = "w-14 p-2 items-center" if self.collapsed else "w-[280px] p-3"
        self.classes(
            replace=f"{width_cls} h-full bg-[#090a0f] border-r border-[#232736] flex flex-col justify-between shrink-0 transition-all duration-150 overflow-hidden select-none"
        )

    def _build_ui(self) -> None:
        self.clear()
        with self:
            if self.collapsed:
                self._build_collapsed_rail()
            else:
                self._build_expanded_drawer()

    def _build_collapsed_rail(self) -> None:
        """Render 56px Rail Mode (brand mark, new session, search, session dots, footer settings)."""
        with ui.column().classes("w-full items-center gap-3"):
            # Brand mark / Expand toggle at top
            btn_expand = (
                ui.button(icon="menu", on_click=self.toggle)
                .props("dense flat round size=sm")
                .classes("text-slate-400 hover:text-white w-9 h-9")
            )
            with btn_expand:
                ui.tooltip("Expand sidebar (Ctrl+B)").classes("text-xs")

            # Primary Action: New Chat Button
            btn_new = (
                ui.button(icon="add", on_click=self.create_new, color="primary")
                .props("dense round unelevated size=sm")
                .classes("w-8 h-8 shadow-md")
            )
            with btn_new:
                ui.tooltip("New Chat (Ctrl+N)").classes("text-xs")

            # Search shortcut: Clicking expands and opens search
            btn_search = (
                ui.button(icon="search", on_click=self._handle_rail_search)
                .props("dense flat round size=sm")
                .classes("text-slate-400 hover:text-white")
            )
            with btn_search:
                ui.tooltip("Search sessions").classes("text-xs")

            # Session quick switcher dot rail
            with ui.column().classes(
                "w-full items-center gap-1.5 pt-2 border-t border-[#232736] overflow-y-auto max-h-[60vh]"
            ):
                for s in self.sessions:
                    is_active = s.id == self.active_session_id
                    dot_color = (
                        "bg-amber-400"
                        if s.pinned
                        else (
                            "bg-blue-500"
                            if is_active
                            else "bg-slate-600 hover:bg-slate-400"
                        )
                    )
                    dot_btn = (
                        ui.button(on_click=lambda _, sid=s.id: self.select(sid))
                        .props("dense flat round size=xs")
                        .classes(
                            f"w-7 h-7 rounded-lg {'bg-[#1c202e]' if is_active else ''} flex items-center justify-center transition-colors"
                        )
                    )
                    with dot_btn:
                        ui.element("div").classes(f"w-2 h-2 rounded-full {dot_color}")
                        ui.tooltip(f"{s.title} ({s.workspace})").classes("text-xs")

        # Bottom foot area
        with ui.column().classes("w-full items-center pb-2"):
            settings_btn = (
                ui.button(icon="settings", on_click=self._handle_settings)
                .props("dense flat round size=sm")
                .classes("text-slate-500 hover:text-slate-300")
            )
            with settings_btn:
                ui.tooltip("Settings").classes("text-xs")

    def _build_expanded_drawer(self) -> None:
        """Render Expanded Drawer (Brand row, New Chat pill, Workspace browser, Footer)."""
        with ui.column().classes("w-full gap-2.5 flex-grow overflow-hidden"):
            # 1. Top Logo & Brand Row
            with ui.row().classes("w-full items-center justify-between pb-1"):
                with ui.row().classes("items-center gap-2 overflow-hidden"):
                    ui.icon("terminal", size="18px").classes("text-[#3b82f6] shrink-0")
                    ui.label("Magitech Harness").classes(
                        "font-semibold text-xs tracking-wide text-white truncate"
                    )

                # Collapse button
                btn_collapse = (
                    ui.button(icon="chevron_left", on_click=self.toggle)
                    .props("dense flat round size=sm")
                    .classes("text-slate-400 hover:text-white shrink-0")
                )
                with btn_collapse:
                    ui.tooltip("Collapse sidebar (Ctrl+B)").classes("text-xs")

            # 2. Primary New Chat Button (Pill with shortcut badge)
            with (
                ui.button(on_click=self.create_new)
                .props("dense unelevated color=primary no-caps")
                .classes(
                    "w-full h-8 px-3 rounded-lg flex items-center justify-between text-xs font-medium shadow-md hover:brightness-110 transition-all"
                )
            ):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("add", size="16px").classes("text-white")
                    ui.label("New Chat").classes("font-semibold text-white")
                ui.badge("Ctrl+N", color="blue-10").classes(
                    "font-mono text-[9px] px-1 py-0.5 text-blue-200"
                )

            # 3. Workspace / Sessions Section Header
            with ui.row().classes(
                "w-full items-center justify-between pt-1 border-t border-[#1c202e]"
            ):
                with ui.row().classes("items-center gap-1.5"):
                    ui.label("WORKSPACES").classes(
                        "text-[10px] font-mono font-semibold tracking-wider text-slate-400 uppercase"
                    )
                    count = len(self._get_filtered_sessions())
                    ui.badge(str(count), color="dark").classes(
                        "text-[9px] font-mono text-slate-400"
                    )

                # Action cluster: Search toggle, Add Workspace, View options menu
                with ui.row().classes("items-center gap-0.5"):
                    # Search toggle
                    ui.button(
                        icon="search",
                        on_click=self._toggle_search,
                    ).props("dense flat round size=xs").classes(
                        "text-slate-400 hover:text-white"
                    )

                    # Add Workspace Folder dialog
                    ui.button(
                        icon="create_new_folder",
                        on_click=self._show_add_workspace_dialog,
                    ).props("dense flat round size=xs").classes(
                        "text-slate-400 hover:text-white"
                    )

                    # View options menu
                    with (
                        ui.button(icon="tune")
                        .props("dense flat round size=xs")
                        .classes("text-slate-400 hover:text-white")
                    ):
                        with ui.menu().classes(
                            "bg-[#11131a] border border-[#232736] text-xs text-slate-300 p-1.5 rounded-lg shadow-xl min-w-[160px]"
                        ):
                            ui.label("GROUP BY").classes(
                                "text-[10px] font-mono text-slate-500 uppercase px-2 py-1"
                            )
                            ui.menu_item(
                                "Workspace Folder",
                                on_click=lambda: self._set_group_by("workspace"),
                            ).classes("hover:bg-[#1c202e] text-xs py-1 px-2")
                            ui.menu_item(
                                "Flat List",
                                on_click=lambda: self._set_group_by("flat"),
                            ).classes("hover:bg-[#1c202e] text-xs py-1 px-2")

                            ui.separator().classes("bg-[#232736] my-1")
                            ui.label("FILTER").classes(
                                "text-[10px] font-mono text-slate-500 uppercase px-2 py-1"
                            )
                            ui.menu_item(
                                "Hide Archived",
                                on_click=lambda: self._set_filter_archived("hide"),
                            ).classes("hover:bg-[#1c202e] text-xs py-1 px-2")
                            ui.menu_item(
                                "Show Archived",
                                on_click=lambda: self._set_filter_archived("show"),
                            ).classes("hover:bg-[#1c202e] text-xs py-1 px-2")
                            ui.menu_item(
                                "Only Archived",
                                on_click=lambda: self._set_filter_archived("only"),
                            ).classes("hover:bg-[#1c202e] text-xs py-1 px-2")

            # 4. Search Filter Input Box (Collapsible / Toggleable)
            self.search_row = ui.row().classes(
                f"w-full items-center gap-1.5 bg-[#11131a] border border-[#232736] rounded-lg px-2 py-0.5 {'hidden' if not self.show_search_input and not self.search_filter else ''}"
            )
            with self.search_row:
                ui.icon("search", size="14px").classes("text-slate-500 shrink-0")
                self.search_input = (
                    ui.input(placeholder="Search sessions...")
                    .props("dense borderless")
                    .classes("flex-grow text-xs font-mono text-slate-200")
                    .on("input", self._handle_search)
                )
                if self.search_filter:
                    self.search_input.set_value(self.search_filter)
                ui.button(
                    icon="close",
                    on_click=self._clear_search,
                ).props("dense flat round size=xs").classes(
                    "text-slate-500 hover:text-white"
                )

            # 5. Session Item List & Folders Container
            self.list_container = ui.column().classes(
                "w-full gap-1 overflow-y-auto flex-grow pr-1"
            )
            self._render_sessions()

        # 6. Bottom Pinned Footer
        with ui.row().classes(
            "w-full items-center justify-between pt-2 border-t border-[#1c202e] px-1"
        ):
            with ui.row().classes("items-center gap-1.5"):
                ui.icon("account_circle", size="16px").classes("text-slate-400")
                ui.label(self.active_workspace).classes(
                    "text-xs font-mono text-slate-400 truncate max-w-[140px]"
                )

            ui.button(
                icon="settings",
                on_click=self._handle_settings,
            ).props("dense flat round size=sm").classes(
                "text-slate-400 hover:text-white"
            )

    def _get_filtered_sessions(self) -> list[MthSession]:
        query = self.search_filter.lower().strip()
        sessions = self.sessions

        # 1. Archived filter
        if self.filter_archived == "hide":
            sessions = [s for s in sessions if not s.archived]
        elif self.filter_archived == "only":
            sessions = [s for s in sessions if s.archived]

        # 2. Text query filter
        if query:
            sessions = [
                s
                for s in sessions
                if query in s.title.lower() or query in s.workspace.lower()
            ]

        # 3. Order by recency with pinned items on top
        return sorted(
            sessions, key=lambda s: (not s.pinned, s.updated_at), reverse=True
        )

    def _render_sessions(self) -> None:
        if self.collapsed:
            return
        self.list_container.clear()
        filtered = self._get_filtered_sessions()

        with self.list_container:
            if not filtered:
                with ui.column().classes(
                    "w-full items-center justify-center py-8 text-slate-600 gap-1"
                ):
                    ui.icon("chat_bubble_outline", size="24px")
                    ui.label("No sessions found").classes("text-xs font-mono")
                return

            if self.group_by == "flat":
                for s in filtered:
                    MthSessionRow(
                        session=s,
                        is_active=s.id == self.active_session_id,
                        on_select=self.select,
                        on_pin=self._handle_pin,
                        on_rename=self._handle_rename,
                        on_fork=self._handle_fork,
                        on_archive=self._handle_archive,
                        on_delete=self._handle_delete_session,
                    )
            else:
                # Group by workspace folder
                groups: dict[str, list[MthSession]] = {}
                for s in filtered:
                    groups.setdefault(s.workspace, []).append(s)

                for ws_name, sess_list in groups.items():
                    is_folder_collapsed = ws_name in self.collapsed_folders
                    with ui.column().classes("w-full gap-0.5 mb-1"):
                        # Folder row header
                        with (
                            ui.row()
                            .classes(
                                "w-full items-center justify-between px-1.5 py-1 rounded hover:bg-[#141721] cursor-pointer text-slate-400"
                            )
                            .on(
                                "click",
                                lambda _, name=ws_name: self._toggle_folder(name),
                            )
                        ):
                            with ui.row().classes(
                                "items-center gap-1.5 overflow-hidden flex-grow"
                            ):
                                chevron = (
                                    "keyboard_arrow_right"
                                    if is_folder_collapsed
                                    else "keyboard_arrow_down"
                                )
                                ui.icon(chevron, size="14px").classes(
                                    "text-slate-500 shrink-0"
                                )
                                folder_icon = (
                                    "folder" if is_folder_collapsed else "folder_open"
                                )
                                ui.icon(folder_icon, size="14px").classes(
                                    "text-amber-400 shrink-0"
                                )
                                ui.label(ws_name).classes(
                                    "font-mono text-xs text-slate-300 font-semibold truncate"
                                )

                            ui.badge(str(len(sess_list)), color="dark").classes(
                                "text-[9px] font-mono text-slate-500 shrink-0"
                            )

                        # Folder items
                        if not is_folder_collapsed:
                            with ui.column().classes(
                                "w-full pl-3 gap-1 border-l border-[#1e2230] ml-2"
                            ):
                                for s in sess_list:
                                    MthSessionRow(
                                        session=s,
                                        is_active=s.id == self.active_session_id,
                                        on_select=self.select,
                                        on_pin=self._handle_pin,
                                        on_rename=self._handle_rename,
                                        on_fork=self._handle_fork,
                                        on_archive=self._handle_archive,
                                        on_delete=self._handle_delete_session,
                                    )

    def _toggle_folder(self, ws_name: str) -> None:
        if ws_name in self.collapsed_folders:
            self.collapsed_folders.remove(ws_name)
        else:
            self.collapsed_folders.add(ws_name)
        self._render_sessions()

    def _toggle_search(self) -> None:
        self.show_search_input = not self.show_search_input
        if self.show_search_input:
            self.search_row.classes(remove="hidden")
        else:
            if not self.search_filter:
                self.search_row.classes(add="hidden")

    def _clear_search(self) -> None:
        self.search_filter = ""
        self.search_input.set_value("")
        self.show_search_input = False
        self.search_row.classes(add="hidden")
        self._render_sessions()

    def _handle_rail_search(self) -> None:
        self.collapsed = False
        self.show_search_input = True
        self._update_classes()
        self._build_ui()
        if self.on_toggle_collapsed:
            self.on_toggle_collapsed(self.collapsed)

    def _handle_search(self, e: Any) -> None:
        self.search_filter = self.search_input.value or ""
        self._render_sessions()

    def _set_group_by(self, mode: str) -> None:
        self.group_by = mode
        self._render_sessions()

    def _set_filter_archived(self, mode: str) -> None:
        self.filter_archived = mode
        self._render_sessions()

    def _show_add_workspace_dialog(self) -> None:
        with (
            ui.dialog() as dialog,
            ui.card().classes(
                "bg-[#11131a] border border-[#232736] text-slate-200 p-4 min-w-[320px] rounded-xl"
            ),
        ):
            ui.label("Add Workspace Folder").classes(
                "font-semibold text-sm text-white mb-2"
            )
            inp = (
                ui.input(placeholder="Workspace name (e.g. project-core)")
                .props("dense autofocus")
                .classes("w-full text-xs font-mono text-white mb-3")
            )

            def _submit() -> None:
                name = (inp.value or "").strip()
                if name:
                    self.active_workspace = name
                    self.create_new(workspace=name)
                dialog.close()

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=dialog.close).props(
                    "dense flat no-caps size=sm"
                ).classes("text-slate-400")
                ui.button("Create", on_click=_submit).props(
                    "dense unelevated color=primary no-caps size=sm"
                )
        dialog.open()

    def _handle_pin(self, session_id: str) -> None:
        if self.on_pin_session:
            self.on_pin_session(session_id)
        self._render_sessions()

    def _handle_rename(self, session_id: str, new_title: str) -> None:
        if self.on_rename_session:
            self.on_rename_session(session_id, new_title)
        self._render_sessions()

    def _handle_fork(self, session_id: str) -> None:
        if self.on_fork_session:
            self.on_fork_session(session_id)
        self._render_sessions()

    def _handle_archive(self, session_id: str) -> None:
        if self.on_archive_session:
            self.on_archive_session(session_id)
        self._render_sessions()

    def _handle_delete_session(self, session_id: str) -> None:
        if self.on_delete_session:
            self.on_delete_session(session_id)
        self._render_sessions()

    def _handle_settings(self) -> None:
        if self.on_open_settings:
            self.on_open_settings()

    def toggle(self) -> None:
        """Toggle between expanded drawer and collapsed 56px rail."""
        self.collapsed = not self.collapsed
        self._update_classes()
        self._build_ui()
        if self.on_toggle_collapsed:
            self.on_toggle_collapsed(self.collapsed)

    def select(self, session_id: str) -> None:
        """Select and activate a session by id."""
        self.active_session_id = session_id
        if self.collapsed:
            self._build_ui()
        else:
            self._render_sessions()
        if self.on_select_session:
            self.on_select_session(session_id)

    def create_new(self, workspace: str | None = None) -> None:
        """Trigger new session creation."""
        ws = workspace or self.active_workspace
        if self.on_new_session:
            self.on_new_session(ws)
